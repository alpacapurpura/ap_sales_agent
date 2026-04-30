"""Architectural fitness: outbox table tenant_id invariants.

Scans all Python source files that use OutboxRepositoryImpl or reference the
``domain_event_outbox`` table to verify that:
1. All SQLAlchemy ``select()`` / ``update()`` / ``delete()`` calls on
   DomainEventOutboxModel include a ``tenant_id`` predicate.
2. The only documented cross-tenant exception is ``claim_pending`` (worker
   scope, FOR UPDATE SKIP LOCKED), which must NOT be added to general CRUD
   code.

Strategy:
- AST-walk files that import from the outbox infrastructure.
- Detect function definitions that use SQLA select/update/delete.
- Verify ``tenant_id`` appears in the function body (as attribute name or
  keyword in a ``.where()`` call).
- The ``claim_pending`` method is explicitly allowed as the sole
  cross-tenant exception (documented in OutboxRepository docstring).

This test is intentionally simple: it checks textual presence of
``tenant_id`` within functions that query the table, not deep data-flow.
That's sufficient because the outbox model only has two consumers:
OutboxRepositoryImpl and OutboxDispatcher (which only calls append and
mark_dispatched, both tenant-scoped).

Ratchet: the ``CROSS_TENANT_ALLOWED_METHODS`` set is the only allowlist
and should only ever shrink.
"""

from __future__ import annotations

import ast
from pathlib import Path

# ──────────────────────────────────────────────────────────────
# ALLOWLIST — ratchet: only remove entries, never add.
# claim_pending is the only documented cross-tenant exception.
# ──────────────────────────────────────────────────────────────
CROSS_TENANT_ALLOWED_METHODS: frozenset[str] = frozenset(
    {
        "claim_pending",  # FOR UPDATE SKIP LOCKED — documented worker-scope exception
    }
)

# Files to scan — all files that reference OutboxRepositoryImpl or the table name
_SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
_OUTBOX_TABLE = "domain_event_outbox"
_OUTBOX_CLASS = "OutboxRepositoryImpl"
_QUERY_FUNCS = {"select", "update", "delete"}


def _collects_outbox_files() -> list[Path]:
    """Find all .py files that reference the outbox repo or table."""
    results: list[Path] = []
    for py_file in sorted(_SRC_ROOT.rglob("*.py")):
        try:
            text = py_file.read_text(encoding="utf-8")
        except OSError:
            continue
        if (
            (_OUTBOX_CLASS in text or _OUTBOX_TABLE in text)
            and "migrations" not in py_file.parts
            and "alembic" not in py_file.parts
        ):
            results.append(py_file)
    return results


def _extract_query_function_bodies(
    tree: ast.Module,
) -> list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]:
    """Return (function_name, node) for all funcs containing SQLA query calls."""
    found: list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        # Check if this function body contains select(), update(), or delete()
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                func = child.func
                name = ""
                if isinstance(func, ast.Name):
                    name = func.id
                elif isinstance(func, ast.Attribute):
                    name = func.attr
                if name in _QUERY_FUNCS:
                    found.append((node.name, node))
                    break
    return found


def _function_body_mentions_tenant_id(func_node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return True if ``tenant_id`` appears as an attribute or Name anywhere in the body."""
    for child in ast.walk(func_node):
        if isinstance(child, ast.Name) and child.id == "tenant_id":
            return True
        if isinstance(child, ast.Attribute) and child.attr == "tenant_id":
            return True
        # Also match string literals containing "tenant_id" (e.g. column refs)
        if isinstance(child, ast.Constant) and isinstance(child.value, str) and "tenant_id" in child.value:
            return True
    return False


def test_outbox_queries_filter_tenant_id() -> None:
    """All SQLAlchemy queries on domain_event_outbox must filter by tenant_id.

    Only ``claim_pending`` (worker-scope FOR UPDATE SKIP LOCKED) is allowed
    to be cross-tenant. Any other function querying the table must include
    ``tenant_id`` in its body.
    """
    violations: list[str] = []

    for py_file in _collects_outbox_files():
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue

        rel = py_file.relative_to(_SRC_ROOT)
        query_funcs = _extract_query_function_bodies(tree)

        for func_name, func_node in query_funcs:
            if func_name in CROSS_TENANT_ALLOWED_METHODS:
                continue  # documented cross-tenant exception

            if not _function_body_mentions_tenant_id(func_node):
                violations.append(f"{rel}::{func_name} — queries table but no tenant_id filter found")

    assert not violations, (
        "Outbox queries missing tenant_id filter.\n\n"
        "All select/update/delete on domain_event_outbox must include "
        "tenant_id in the WHERE clause (except claim_pending — see CROSS_TENANT_ALLOWED_METHODS).\n\n"
        "Violations:\n" + "\n".join(f"  - {v}" for v in violations)
    )


def test_cross_tenant_allowlist_not_grown() -> None:
    """Ratchet: CROSS_TENANT_ALLOWED_METHODS must not grow without justification.

    Current cap: 1 entry (claim_pending). Adding entries requires an explicit
    architectural decision with documented rationale in the commit message.
    """
    current_count = len(CROSS_TENANT_ALLOWED_METHODS)
    assert current_count <= 1, (
        f"CROSS_TENANT_ALLOWED_METHODS grew to {current_count} entries. "
        "Only 'claim_pending' is the documented cross-tenant exception. "
        "Any new entry requires architectural justification in the commit message."
    )
