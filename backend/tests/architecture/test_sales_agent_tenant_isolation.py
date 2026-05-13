"""Architectural fitness — tenant isolation en queries SQLA del sales_agent.

Cada query (``select(Model)``) que toca una tabla observability del
sales_agent (``sales_agent_llm_call``, ``sales_agent_trace_event``,
``sales_agent_routing_log``) DEBE filtrar por ``Model.tenant_id == ...``
en algún ``.where(...)`` adjunto.

Excepción única: ``dual_write_reconciliation_task`` ejecuta agregaciones
cross-tenant intencionales (worker cron, computa diff legacy vs
event-sourced por tenant). Allowlistado por linea + razón documentada.

Ratchet pattern: nuevas queries cross-tenant requieren entry en
``KNOWN_CROSS_TENANT_QUERY_LINES`` con razón en docstring del archivo
emisor.

# [SALES-AGENT-CALLBACK-HANDLER-S1] tenant isolation guard.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SALES_AGENT_DIR = REPO / "src" / "modules" / "sales_agent"

# Modelos observability cuyo schema incluye ``tenant_id`` y deben filtrarse
# en cada query.
TENANT_SCOPED_MODELS: frozenset[str] = frozenset(
    {
        "SalesAgentLlmCallModel",
        "SalesAgentTraceEventModel",
        "SalesAgentRoutingLogModel",
    },
)

# Allowlist explícito de queries cross-tenant intencionales.
# Format: ``"<rel_path>:<lineno>"`` — bumpear con razón en docstring del file.
KNOWN_CROSS_TENANT_QUERY_LINES: frozenset[str] = frozenset(
    {
        # Reconciliation worker computa diff legacy vs event-sourced por tenant.
        # La query GROUP BY tenant_id es intencional (cross-tenant aggregate).
        # Razón documentada en
        # ``src/modules/sales_agent/observability/workers/dual_write_reconciliation_task.py``.
        "src/modules/sales_agent/observability/workers/dual_write_reconciliation_task.py:75",
    },
)


def _is_select_of_tenant_scoped_model(call: ast.Call) -> str | None:
    """Si ``call`` es ``select(SalesAgentXModel, ...)``, retorna el model name.
    None si no es un select sobre un modelo tenant-scoped."""
    func = call.func
    if isinstance(func, ast.Name) and func.id == "select":
        for arg in call.args:
            # ``select(Model)`` o ``select(Model.col, ...)``
            target = arg if isinstance(arg, ast.Name) else getattr(arg, "value", None)
            if isinstance(target, ast.Name) and target.id in TENANT_SCOPED_MODELS:
                return target.id
    return None


def _statement_contains_tenant_id_filter(stmt: ast.AST, model_name: str) -> bool:
    """¿``stmt`` (la statement que contiene el ``select``) tiene un
    ``Compare`` con ``Model.tenant_id == ...``?"""
    for node in ast.walk(stmt):
        if not isinstance(node, ast.Compare):
            continue
        sides = [node.left, *node.comparators]
        for side in sides:
            if (
                isinstance(side, ast.Attribute)
                and side.attr == "tenant_id"
                and isinstance(side.value, ast.Name)
                and side.value.id == model_name
            ):
                return True
    return False


def _enclosing_statement(tree: ast.Module, lineno: int) -> ast.AST | None:
    """Encuentra la statement (Assign / Return / Expr) más anidada que
    contiene ``lineno``."""
    candidate: ast.AST | None = None
    for node in ast.walk(tree):
        if not isinstance(node, ast.stmt):
            continue
        end = getattr(node, "end_lineno", None)
        if end is None or not node.lineno <= lineno <= end:
            continue
        if candidate is None or end - node.lineno < getattr(candidate, "end_lineno", 0) - candidate.lineno:
            candidate = node
    return candidate


def _violations_in_file(path: Path) -> list[tuple[int, str]]:
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    offenders: list[tuple[int, str]] = []

    for call in ast.walk(tree):
        if not isinstance(call, ast.Call):
            continue
        model = _is_select_of_tenant_scoped_model(call)
        if model is None:
            continue
        rel = path.relative_to(REPO).as_posix()
        key = f"{rel}:{call.lineno}"
        if key in KNOWN_CROSS_TENANT_QUERY_LINES:
            continue

        stmt = _enclosing_statement(tree, call.lineno)
        if stmt is None or not _statement_contains_tenant_id_filter(stmt, model):
            offenders.append((call.lineno, model))

    return offenders


def _iter_sales_agent_python_files() -> list[Path]:
    return [p for p in SALES_AGENT_DIR.rglob("*.py") if p.is_file()]


class TestTenantIsolation:
    def test_every_observability_query_filters_tenant_id(self) -> None:
        all_offenders: list[str] = []
        for py in _iter_sales_agent_python_files():
            for lineno, model in _violations_in_file(py):
                rel = py.relative_to(REPO).as_posix()
                all_offenders.append(f"{rel}:{lineno}  select({model}, ...) sin filtro tenant_id")
        assert not all_offenders, (
            "Cada query observability del sales_agent debe filtrar por tenant_id. "
            "Violations:\n  - " + "\n  - ".join(all_offenders)
        )

    def test_allowlist_entries_still_present(self) -> None:
        """Drift detection: si un allowlist entry desaparece (linea movida o
        archivo borrado), el ratchet debe shrink — quitar la entry del set
        antes que el test crashee con FileNotFoundError."""
        for entry in KNOWN_CROSS_TENANT_QUERY_LINES:
            path_str, lineno_str = entry.rsplit(":", 1)
            path = REPO / path_str
            assert path.is_file(), (
                f"Allowlist entry stale (file missing): {entry}. Quitar de KNOWN_CROSS_TENANT_QUERY_LINES."
            )
            lineno = int(lineno_str)
            src = path.read_text(encoding="utf-8").splitlines()
            assert lineno <= len(src), (
                f"Allowlist entry stale (lineno fuera de archivo): {entry}. Refrescar el lineno o quitar la entry."
            )
