"""Tests for ``BillingCycleService``.

Service is a thin wrapper around :func:`compute_cycle_start_py` that
loads the per-tenant anchor day from ``tenant_billing_config`` and
falls back to 25 when the row is missing. The interesting bits live in
``cycle_window``; the service tests cover the DB integration.
"""

from __future__ import annotations

import datetime as dt
from uuid import uuid4

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


def _seed_config(db, tenant_id, anchor: int) -> None:
    from src.shared.agent_observability.persistence.tenant_billing_config_repository import (
        TenantBillingConfigRepository,
    )

    repo = TenantBillingConfigRepository(db)
    repo.upsert(
        tenant_id=tenant_id,
        billing_cycle_anchor_day=anchor,
        billing_currency="USD",
        fx_source="frankfurter",
    )
    db.flush()


class TestBillingCycleService:
    def test_compute_window_uses_anchor_25_when_no_config(self, db) -> None:
        from src.shared.agent_observability.reporting.billing_cycle_service import (
            BillingCycleService,
        )

        svc = BillingCycleService(db)
        start, end = svc.compute_window(uuid4(), dt.date(2026, 4, 26))
        assert start == dt.date(2026, 4, 25)
        assert end == dt.date(2026, 5, 25)

    def test_compute_window_honours_tenant_anchor(self, db) -> None:
        from src.shared.agent_observability.reporting.billing_cycle_service import (
            BillingCycleService,
        )

        tenant_id = uuid4()
        _seed_config(db, tenant_id, anchor=15)

        svc = BillingCycleService(db)
        start, end = svc.compute_window(tenant_id, dt.date(2026, 4, 14))
        assert start == dt.date(2026, 3, 15)
        assert end == dt.date(2026, 4, 15)

    def test_current_cycle_window_uses_today(self, monkeypatch, db) -> None:
        from src.shared.agent_observability.reporting import billing_cycle_service

        monkeypatch.setattr(
            billing_cycle_service,
            "_today",
            lambda: dt.date(2026, 4, 26),
        )

        svc = billing_cycle_service.BillingCycleService(db)
        start, end = svc.current_cycle_window(uuid4())
        assert start == dt.date(2026, 4, 25)
        assert end == dt.date(2026, 5, 25)

    def test_previous_cycle_window(self, monkeypatch, db) -> None:
        from src.shared.agent_observability.reporting import billing_cycle_service

        monkeypatch.setattr(
            billing_cycle_service,
            "_today",
            lambda: dt.date(2026, 4, 26),
        )

        svc = billing_cycle_service.BillingCycleService(db)
        start, end = svc.previous_cycle_window(uuid4())
        assert start == dt.date(2026, 3, 25)
        assert end == dt.date(2026, 4, 25)

    def test_resolve_currency_returns_tenant_currency_when_config_present(self, db) -> None:
        from src.shared.agent_observability.reporting.billing_cycle_service import (
            BillingCycleService,
        )

        tenant_id = uuid4()
        _seed_config(db, tenant_id, anchor=25)

        svc = BillingCycleService(db)
        assert svc.resolve_currency(tenant_id) == "USD"

    def test_resolve_currency_defaults_to_usd_when_unconfigured(self, db) -> None:
        from src.shared.agent_observability.reporting.billing_cycle_service import (
            BillingCycleService,
        )

        svc = BillingCycleService(db)
        assert svc.resolve_currency(uuid4()) == "USD"
