"""Tests for the per-tenant cost alert ARQ task."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import sessionmaker


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

    repo = TenantBillingConfigRepository(db)
    repo.upsert(
        tenant_id=tenant_id,
        billing_cycle_anchor_day=25,
        billing_currency="USD",
        fx_source="frankfurter",
        cost_alert_threshold_usd=threshold_usd,
    )
    db.flush()


def _seed_call(db, tenant_id: UUID, cost_usd: Decimal, started_at: dt.datetime) -> None:
    from luana_core_copilot.observability.persistence.llm_call_repository import (
        LlmCallRepository,
    )

    LlmCallRepository(db).add(
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
    )
    db.flush()


class TestCostAlertCheck:
    def test_emits_alert_when_cycle_cost_exceeds_threshold(self, db, monkeypatch) -> None:
        """Tenant with threshold $1.00 + $5.00 cycle cost → alert emitted."""
        from luana_core_observability.application import cost_alert_service

        tenant_id = uuid4()
        _seed_billing_config(db, tenant_id, threshold_usd=Decimal("1.00"))
        cycle_pivot = dt.datetime(2026, 4, 26, tzinfo=dt.UTC)
        _seed_call(db, tenant_id, Decimal("5.0000000000"), cycle_pivot)

        warnings: list[dict] = []

        def _capture_warning(event: str, **kwargs) -> None:
            warnings.append({"event": event, **kwargs})

        fake_logger = MagicMock()
        fake_logger.warning = _capture_warning
        monkeypatch.setattr(cost_alert_service, "logger", fake_logger)

        def _today_stub() -> dt.date:
            return cycle_pivot.date()

        monkeypatch.setattr(cost_alert_service, "_today", _today_stub)

        result = cost_alert_service.check_cost_alerts(db)

        assert result["tenants_checked"] == 1
        assert result["alerts_emitted"] == 1
        assert any(w["event"] == "cost_alert_threshold_exceeded" for w in warnings)
        # The captured warning carries the tenant id, the threshold and the
        # actual cost so the alert is actionable from a log search.
        alert = next(w for w in warnings if w["event"] == "cost_alert_threshold_exceeded")
        assert str(tenant_id) in str(alert.get("tenant_id"))
        assert Decimal(str(alert["cost_usd"])) >= Decimal("5.0000000000")
        assert Decimal(str(alert["threshold_usd"])) == Decimal("1.00")

    def test_no_alert_when_under_threshold(self, db, monkeypatch) -> None:
        from luana_core_observability.application import cost_alert_service

        tenant_id = uuid4()
        _seed_billing_config(db, tenant_id, threshold_usd=Decimal("100.00"))
        cycle_pivot = dt.datetime(2026, 4, 26, tzinfo=dt.UTC)
        _seed_call(db, tenant_id, Decimal("0.5000000000"), cycle_pivot)

        warnings: list[dict] = []

        def _capture_warning(event: str, **kwargs) -> None:
            warnings.append({"event": event, **kwargs})

        fake_logger = MagicMock()
        fake_logger.warning = _capture_warning
        monkeypatch.setattr(cost_alert_service, "logger", fake_logger)

        def _today_stub() -> dt.date:
            return cycle_pivot.date()

        monkeypatch.setattr(cost_alert_service, "_today", _today_stub)

        result = cost_alert_service.check_cost_alerts(db)

        assert result["alerts_emitted"] == 0
        assert all(w["event"] != "cost_alert_threshold_exceeded" for w in warnings)

    def test_skips_tenants_without_threshold(self, db, monkeypatch) -> None:
        """Tenants whose billing config has no threshold are NOT alerted."""
        from luana_core_observability.application import cost_alert_service
        from luana_core_observability.persistence.tenant_billing_config_repository import (
            TenantBillingConfigRepository,
        )

        tenant_id = uuid4()
        # Threshold is None.
        TenantBillingConfigRepository(db).upsert(
            tenant_id=tenant_id,
            billing_cycle_anchor_day=25,
            billing_currency="USD",
            fx_source="frankfurter",
            cost_alert_threshold_usd=None,
        )
        db.flush()
        _seed_call(db, tenant_id, Decimal("1.0000000000"), dt.datetime(2026, 4, 26, tzinfo=dt.UTC))

        result = cost_alert_service.check_cost_alerts(db)
        assert result["tenants_checked"] == 0


class TestSchedulerRegistration:
    def test_task_listed_in_settings(self) -> None:
        from luana_core_observability.workers.cost_alert_task import (
            run_cost_alerts,
        )
        from src.workers.settings import SchedulerSettings, WorkerSettings

        assert run_cost_alerts in WorkerSettings.functions
        assert run_cost_alerts in SchedulerSettings.functions

    def test_cron_job_present(self) -> None:
        from luana_core_observability.workers.cost_alert_task import (
            run_cost_alerts,
        )
        from src.workers.settings import SchedulerSettings

        scheduled = [getattr(j, "coroutine", None) for j in SchedulerSettings.cron_jobs]
        assert run_cost_alerts in scheduled
