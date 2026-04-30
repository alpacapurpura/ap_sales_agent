"""Architecture fitness — BudgetGuard uses mv_refresh_log, not pg_stat_user_tables.

PM Q4 decision: BudgetGuard must probe MV freshness via the mv_refresh_log
table (app-controlled, tenant-observable, low-overhead) rather than
pg_stat_user_tables (system catalog, requires superuser in some configs,
unreliable freshness for views).

This test enforces:
1. BudgetGuard source code does NOT reference pg_stat_user_tables.
2. BudgetGuard source code DOES reference mv_refresh_log.
3. MVRefreshLogRepository is injected into BudgetGuard (not bypassed).
4. The _is_mv_stale method calls get_last_refresh on the repository.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

# ── Source file under test ───────────────────────────────────────────────────

_BACKEND = Path(__file__).resolve().parents[2]
_BUDGET_GUARD_SRC = _BACKEND / "src" / "shared" / "billing" / "application" / "budget_guard.py"


# ── Helpers ──────────────────────────────────────────────────────────────────


def _source() -> str:
    return _BUDGET_GUARD_SRC.read_text(encoding="utf-8")


def _ast_tree() -> ast.Module:
    return ast.parse(_source())


# ── Tests ────────────────────────────────────────────────────────────────────


def test_budget_guard_source_exists() -> None:
    """BudgetGuard implementation file must exist."""
    assert _BUDGET_GUARD_SRC.exists(), (
        f"BudgetGuard source not found at {_BUDGET_GUARD_SRC}. Has the file been moved or deleted?"
    )


def test_budget_guard_does_not_call_execute_with_pg_stat_user_tables() -> None:
    """BudgetGuard must NOT call session.execute() with pg_stat_user_tables SQL.

    pg_stat_user_tables is unreliable for MV freshness detection and
    requires elevated privileges in some Postgres configurations.
    Use mv_refresh_log instead.

    Note: the string "pg_stat_user_tables" may legitimately appear in docstrings
    documenting the architectural decision (PM Q4). We check that no method
    in BudgetGuard calls `execute(` or `text(` with a pg_stat_user_tables query.

    AST strategy: find ast.Call nodes where the callee is 'execute' or 'text',
    and any string constant argument contains 'pg_stat_user_tables'.
    """
    tree = _ast_tree()
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        # Check if this is execute(...) or text(...) call
        func = node.func
        is_db_call = (isinstance(func, ast.Name) and func.id in ("execute", "text")) or (
            isinstance(func, ast.Attribute) and func.attr in ("execute", "text")
        )
        if not is_db_call:
            continue
        # Check if any argument string contains pg_stat_user_tables
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and "pg_stat_user_tables" in arg.value:
                violations.append(repr(arg.value[:100]))

    assert not violations, (
        "BudgetGuard calls execute()/text() with pg_stat_user_tables SQL. "
        "PM Q4: use mv_refresh_log.get_last_refresh() for MV freshness probing. "
        f"Found in: {violations}"
    )


def test_budget_guard_references_mv_refresh_log() -> None:
    """BudgetGuard must reference mv_refresh_log (PM Q4 SSoT for MV freshness)."""
    source = _source()
    assert "mv_refresh_log" in source.lower(), (
        "BudgetGuard does not reference mv_refresh_log. "
        "PM Q4: freshness probe MUST use mv_refresh_log, not pg_stat_user_tables."
    )


def test_budget_guard_injects_mv_refresh_log_repo() -> None:
    """BudgetGuard.__init__ must accept mv_refresh_log_repo parameter."""
    from src.shared.billing.application.budget_guard import BudgetGuard

    sig = inspect.signature(BudgetGuard.__init__)
    param_names = list(sig.parameters.keys())
    assert "mv_refresh_log_repo" in param_names, (
        f"BudgetGuard.__init__ must have 'mv_refresh_log_repo' parameter. "
        f"Found: {param_names}. MVRefreshLogRepository must be injected (DI, not hardwired)."
    )


def test_budget_guard_has_is_mv_stale_method() -> None:
    """BudgetGuard must have _is_mv_stale() method for MV freshness probing."""
    from src.shared.billing.application.budget_guard import BudgetGuard

    assert hasattr(BudgetGuard, "_is_mv_stale"), "BudgetGuard must have _is_mv_stale() method (PM Q4 probe method)."


def test_is_mv_stale_calls_get_last_refresh() -> None:
    """_is_mv_stale must call get_last_refresh on the mv_refresh_log_repo.

    Parsed via AST: verifies the method body calls get_last_refresh.
    """
    tree = _ast_tree()
    stale_method_body: list[ast.stmt] = []

    # Find _is_mv_stale method in BudgetGuard class
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "BudgetGuard":
            for item in node.body:
                if isinstance(item, ast.AsyncFunctionDef) and item.name == "_is_mv_stale":
                    stale_method_body = item.body
                    break
            break

    assert stale_method_body, (
        "_is_mv_stale method not found in BudgetGuard class. "
        "It must be defined as `async def _is_mv_stale(self) -> bool`."
    )

    # Look for get_last_refresh call in the method body
    found_call = False
    for node in ast.walk(ast.Module(body=stale_method_body, type_ignores=[])):
        if isinstance(node, ast.Attribute) and node.attr == "get_last_refresh":
            found_call = True
            break

    assert found_call, (
        "_is_mv_stale() does not call get_last_refresh. "
        "PM Q4: freshness probe MUST query mv_refresh_log via get_last_refresh(mv_name)."
    )


def test_mv_name_constant_references_correct_mv() -> None:
    """MV_NAME constant in BudgetGuard must reference mv_daily_llm_cost_per_tenant_v2."""
    from src.shared.billing.application.budget_guard import MV_NAME

    assert MV_NAME == "mv_daily_llm_cost_per_tenant_v2", (
        f"MV_NAME must be 'mv_daily_llm_cost_per_tenant_v2', got {MV_NAME!r}. "
        "This MV is the cross-agent cost materialized view built by the observability pipeline."
    )
