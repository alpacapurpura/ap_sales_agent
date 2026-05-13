"""Cross-agent cost alert breakdown — S2.

Validates that ``check_cost_alerts``:

* Sums copilot + sales_agent cost per tenant before comparing to the
  threshold (cross-agent threshold, not per-agent).
* Emits a structlog warning whose payload carries
  ``breakdown_usd_by_agent`` with one entry per registered agent_kind.
* Does not double-count when only one agent has data.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import sessionmaker

from luana_core_copilot.observability.persistence.models.llm_call_model import (
    CopilotLlmCallModel,
)
from luana_core_sales_agent.observability.persistence.models.llm_call_model import (
    SalesAgentLlmCallModel,
)


@pytest.fixture
def db(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


def _seed_billing_config(db, tenant_id: UUID, threshold_usd: Decimal) -> None:
    from luana_core_observability.persistence.tenant_billing_config_repository import (
        TenantBillingConfigRepository,
    )

    TenantBillingConfigRepository(db).upsert(
        tenant_id=tenant_id,
        billing_cycle_anchor_day=25,
        billing_currency="USD",
        fx_source="frankfurter",
        cost_alert_threshold_usd=threshold_usd,
    )
    db.flush()


def _seed_copilot(db, tenant_id: UUID, started_at: dt.datetime, cost_usd: Decimal) -> None:
    db.add(
        CopilotLlmCallModel(
            tenant_id=tenant_id,
            user_id=uuid4(),
            conversation_id=uuid4(),
            turn_id=uuid4(),
            span_id=uuid4(),
            parent_span_id=None,
            role="agent",
            provider="openai",
            model_requested="gpt-4o",
            model_responded="gpt-4o",
            input_tokens=100,
            output_tokens=50,
            cached_read_tokens=0,
            cached_write_tokens=0,
            reasoning_tokens=0,
            pricing_version_id=uuid4(),
            input_unit_cost_usd=Decimal("0.0000025"),
            output_unit_cost_usd=Decimal("0.000010"),
            cached_read_unit_cost_usd=Decimal(0),
            cost_usd=cost_usd,
            tenant_currency="USD",
            fx_rate_to_tenant=Decimal("1.0"),
            fx_rate_source="passthrough",
            cost_tenant_currency=cost_usd,
            started_at=started_at,
            duration_ms=1500,
            status="ok",
            error_type=None,
        ),
    )
    db.flush()


def _seed_sales(db, tenant_id: UUID, started_at: dt.datetime, cost_usd: Decimal) -> None:
    db.add(
        SalesAgentLlmCallModel(
            tenant_id=tenant_id,
            lead_id=uuid4(),
            channel_type="whatsapp",
            turn_id=uuid4(),
            span_id=uuid4(),
            parent_span_id=None,
            role="agent",
            provider="kimi",
            model_requested="kimi-k2.6",
            model_responded="kimi-k2.6",
            input_tokens=200,
            output_tokens=80,
            cached_read_tokens=0,
            cached_write_tokens=0,
            reasoning_tokens=0,
            pricing_version_id=uuid4(),
            input_unit_cost_usd=Decimal("0.0000004"),
            output_unit_cost_usd=Decimal("0.000002"),
            cached_read_unit_cost_usd=Decimal(0),
            cost_usd=cost_usd,
            tenant_currency="USD",
            fx_rate_to_tenant=Decimal("1.0"),
            fx_rate_source="passthrough",
            cost_tenant_currency=cost_usd,
            started_at=started_at,
            duration_ms=2200,
            status="ok",
            error_type=None,
        ),
    )
    db.flush()


def _stub_logger(monkeypatch, target_module) -> list[dict]:
    captured: list[dict] = []

    def _capture(event: str, **kwargs) -> None:
        captured.append({"event": event, **kwargs})

    fake = MagicMock()
    fake.warning = _capture
    monkeypatch.setattr(target_module, "logger", fake)
    return captured


class TestCrossAgentBreakdown:
    def test_emits_breakdown_when_cross_agent_total_exceeds_threshold(
        self,
        db,
        monkeypatch,
    ) -> None:
        """Copilot ($0.50) + sales ($1.50) = $2.00 > $1.00 threshold → alert with breakdown."""
        from luana_core_observability.application import cost_alert_service

        tenant_id = uuid4()
        cycle_pivot = dt.datetime(2026, 4, 26, tzinfo=dt.UTC)
        _seed_billing_config(db, tenant_id, threshold_usd=Decimal("1.00"))
        _seed_copilot(db, tenant_id, cycle_pivot, Decimal("0.5000000000"))
        _seed_sales(db, tenant_id, cycle_pivot, Decimal("1.5000000000"))

        warnings = _stub_logger(monkeypatch, cost_alert_service)

        def _today_stub() -> dt.date:
            return cycle_pivot.date()

        monkeypatch.setattr(cost_alert_service, "_today", _today_stub)

        result = cost_alert_service.check_cost_alerts(db)
        assert result["alerts_emitted"] == 1

        alert = next(w for w in warnings if w["event"] == "cost_alert_threshold_exceeded")
        breakdown = alert["breakdown_usd_by_agent"]
        # Registry may include extra agents (e.g. "campaign") registered by
        # Sub-C; we only assert the two seeded agents are present and correct.
        assert {"copilot", "sales_agent"} <= set(breakdown.keys())
        assert Decimal(breakdown["copilot"]) == Decimal("0.5000000000")
        assert Decimal(breakdown["sales_agent"]) == Decimal("1.5000000000")
        assert Decimal(str(alert["cost_usd"])) == Decimal("2.0000000000")

    def test_neither_agent_alone_triggers_but_combined_does(self, db, monkeypatch) -> None:
        """Each agent under threshold individually but combined goes over."""
        from luana_core_observability.application import cost_alert_service

        tenant_id = uuid4()
        cycle_pivot = dt.datetime(2026, 4, 26, tzinfo=dt.UTC)
        _seed_billing_config(db, tenant_id, threshold_usd=Decimal("1.00"))
        _seed_copilot(db, tenant_id, cycle_pivot, Decimal("0.6000000000"))
        _seed_sales(db, tenant_id, cycle_pivot, Decimal("0.6000000000"))

        warnings = _stub_logger(monkeypatch, cost_alert_service)

        def _today_stub() -> dt.date:
            return cycle_pivot.date()

        monkeypatch.setattr(cost_alert_service, "_today", _today_stub)

        result = cost_alert_service.check_cost_alerts(db)
        assert result["alerts_emitted"] == 1
        alert = next(w for w in warnings if w["event"] == "cost_alert_threshold_exceeded")
        assert Decimal(str(alert["cost_usd"])) == Decimal("1.2000000000")

    def test_only_one_agent_no_double_count(self, db, monkeypatch) -> None:
        """Tenant with only sales calls — copilot breakdown is 0, total is sales-only."""
        from luana_core_observability.application import cost_alert_service

        tenant_id = uuid4()
        cycle_pivot = dt.datetime(2026, 4, 26, tzinfo=dt.UTC)
        _seed_billing_config(db, tenant_id, threshold_usd=Decimal("1.00"))
        _seed_sales(db, tenant_id, cycle_pivot, Decimal("3.0000000000"))

        warnings = _stub_logger(monkeypatch, cost_alert_service)

        def _today_stub() -> dt.date:
            return cycle_pivot.date()

        monkeypatch.setattr(cost_alert_service, "_today", _today_stub)

        result = cost_alert_service.check_cost_alerts(db)
        assert result["alerts_emitted"] == 1
        alert = next(w for w in warnings if w["event"] == "cost_alert_threshold_exceeded")
        breakdown = alert["breakdown_usd_by_agent"]
        assert Decimal(breakdown["copilot"]) == Decimal(0)
        assert Decimal(breakdown["sales_agent"]) == Decimal("3.0000000000")
        assert Decimal(str(alert["cost_usd"])) == Decimal("3.0000000000")
