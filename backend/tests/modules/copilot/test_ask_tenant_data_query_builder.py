"""F5 — query_builder tests (intent + period → DataQueryPlan)."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from luana_core_copilot.application.tools.ask_tenant_data.intent_classifier import (
    IntentResult,
)
from luana_core_copilot.application.tools.ask_tenant_data.query_builder import (
    build_plan,
)

NOW = datetime(2026, 4, 25, 14, 0, 0, tzinfo=timezone.utc)


def test_build_plan_offer_lookup_with_name_query() -> None:
    intent = IntentResult(
        kind="offer_lookup",
        name_query="propósito",
        period_phrase=None,
        channel=None,
        raw_question="dame resumen del programa propósito",
        confidence=0.9,
    )
    plan = build_plan(intent, now=NOW)
    assert plan is not None
    assert plan.kind == "offer_lookup"
    assert plan.filters["name_query"] == "propósito"
    assert plan.filters.get("status") == "active"
    assert plan.limit == 20


def test_build_plan_lead_count_resolves_period() -> None:
    intent = IntentResult(
        kind="lead_count",
        name_query=None,
        period_phrase="esta semana",
        channel="whatsapp",
        raw_question="cuántas personas escribieron por whatsapp esta semana",
        confidence=0.9,
    )
    plan = build_plan(intent, now=NOW)
    assert plan is not None
    assert plan.kind == "lead_count"
    assert plan.filters["since"] == datetime(2026, 4, 20, 0, 0, 0, tzinfo=timezone.utc)
    assert plan.filters["until"].date() == date(2026, 4, 26)
    assert plan.filters["channel"] == "whatsapp"


def test_build_plan_conversation_count_defaults_to_current_week_if_missing() -> None:
    intent = IntentResult(
        kind="conversation_count",
        name_query=None,
        period_phrase=None,  # missing → default current week
        channel=None,
        raw_question="cuántas conversaciones tuve",
        confidence=0.6,
    )
    plan = build_plan(intent, now=NOW)
    assert plan is not None
    assert plan.kind == "conversation_count"
    assert plan.filters["since"] == datetime(2026, 4, 20, 0, 0, 0, tzinfo=timezone.utc)


def test_build_plan_unknown_returns_none() -> None:
    intent = IntentResult(
        kind="unknown",
        name_query=None,
        period_phrase=None,
        channel=None,
        raw_question="???",
        confidence=0.0,
    )
    assert build_plan(intent, now=NOW) is None


@pytest.mark.parametrize("limit", [5, 10, 50])
def test_build_plan_respects_limit(limit: int) -> None:
    intent = IntentResult(
        kind="offer_lookup",
        name_query="x",
        period_phrase=None,
        channel=None,
        raw_question="x",
        confidence=0.9,
    )
    plan = build_plan(intent, now=NOW, default_limit=limit)
    assert plan is not None
    assert plan.limit == limit
