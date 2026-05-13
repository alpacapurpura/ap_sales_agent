"""F5 — state_check tests (annotates result with advisory flags)."""

from __future__ import annotations

from luana_core_copilot.application.tools.ask_tenant_data.state_check import (
    annotate_state,
)
from luana_core_copilot.domain.ports import DataQueryPlan, DataQueryResult


def test_zero_results_emits_empty_flag() -> None:
    plan = DataQueryPlan(kind="lead_count", filters={})
    result = DataQueryResult(rows=[], metadata={"count": 0})
    flags = annotate_state(plan=plan, result=result)
    assert flags["empty"] is True


def test_offer_lookup_only_archived_emits_flag() -> None:
    plan = DataQueryPlan(kind="offer_lookup", filters={})
    result = DataQueryResult(
        rows=[{"name": "Curso viejo", "status": "archived"}],
        metadata={"count": 1, "active_count": 0, "archived_count": 1},
    )
    flags = annotate_state(plan=plan, result=result)
    assert flags["only_archived"] is True
    assert "empty" not in flags


def test_offer_lookup_with_active_does_not_emit_archived_flag() -> None:
    plan = DataQueryPlan(kind="offer_lookup", filters={})
    result = DataQueryResult(
        rows=[{"name": "X", "status": "active"}],
        metadata={"count": 1, "active_count": 1, "archived_count": 0},
    )
    flags = annotate_state(plan=plan, result=result)
    assert flags == {}


def test_count_with_results_no_flags() -> None:
    plan = DataQueryPlan(kind="lead_count", filters={})
    result = DataQueryResult(rows=[], metadata={"count": 12})
    flags = annotate_state(plan=plan, result=result)
    assert flags == {}


def test_zero_with_period_emits_empty_window_flag() -> None:
    plan = DataQueryPlan(
        kind="conversation_count",
        filters={"since": "2026-04-01", "until": "2026-04-25"},
    )
    result = DataQueryResult(rows=[], metadata={"count": 0})
    flags = annotate_state(plan=plan, result=result)
    assert flags.get("empty_window") is True
