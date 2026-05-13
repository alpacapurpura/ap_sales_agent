"""Smoke tests for the Phase 1 observability SQLAlchemy models.

The generated columns (``occurred_on`` / ``occurred_year_month``) are
**not** mapped on the ORM side — see model docstring for why. We only
verify the ordinary columns roundtrip through ``Base.metadata.create_all``
on the in-memory SQLite test engine and stay tenant-scoped.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from uuid import uuid4

import pytest


class TestCopilotLlmCallModel:
    def test_instantiate_and_commit(self, db) -> None:
        from luana_core_copilot.observability.persistence.models.llm_call_model import (
            CopilotLlmCallModel,
        )

        tenant = uuid4()
        row = CopilotLlmCallModel(
            tenant_id=tenant,
            user_id=uuid4(),
            conversation_id=uuid4(),
            turn_id=uuid4(),
            span_id=uuid4(),
            role="agent",
            provider="openai",
            model_requested="gpt-4o",
            model_responded="gpt-4o-2024-11-20",
            input_tokens=1200,
            output_tokens=345,
            cached_read_tokens=100,
            cached_write_tokens=0,
            reasoning_tokens=0,
            pricing_version_id=uuid4(),
            input_unit_cost_usd=Decimal("0.0000025"),
            output_unit_cost_usd=Decimal("0.000010"),
            cached_read_unit_cost_usd=Decimal("0.00000125"),
            cost_usd=Decimal("0.0064500000"),
            tenant_currency="USD",
            fx_rate_to_tenant=Decimal("1.00000000"),
            fx_rate_source="frankfurter",
            cost_tenant_currency=Decimal("0.00645000"),
            started_at=dt.datetime(2026, 4, 26, 12, 0, tzinfo=dt.UTC),
            duration_ms=812,
            status="ok",
        )
        db.add(row)
        db.commit()

        fetched = db.query(CopilotLlmCallModel).filter_by(tenant_id=tenant).one()
        assert fetched.role == "agent"
        assert fetched.provider == "openai"
        assert fetched.model_responded == "gpt-4o-2024-11-20"
        assert fetched.input_tokens == 1200
        assert fetched.output_tokens == 345
        assert fetched.cached_read_tokens == 100
        assert fetched.status == "ok"

    def test_default_status_is_ok(self, db) -> None:
        from luana_core_copilot.observability.persistence.models.llm_call_model import (
            CopilotLlmCallModel,
        )

        row = CopilotLlmCallModel(
            tenant_id=uuid4(),
            turn_id=uuid4(),
            span_id=uuid4(),
            role="agent",
            provider="openai",
            model_requested="gpt-4o-mini",
            model_responded="gpt-4o-mini",
            pricing_version_id=uuid4(),
            input_unit_cost_usd=Decimal(0),
            output_unit_cost_usd=Decimal(0),
            cost_usd=Decimal(0),
            started_at=dt.datetime(2026, 4, 26, 12, 0, tzinfo=dt.UTC),
            duration_ms=10,
        )
        db.add(row)
        db.commit()
        fetched = db.query(CopilotLlmCallModel).first()
        assert fetched.status == "ok"
        assert fetched.input_tokens == 0  # column default
        assert fetched.cached_read_tokens == 0

    def test_repr_human_readable(self, db) -> None:
        from luana_core_copilot.observability.persistence.models.llm_call_model import (
            CopilotLlmCallModel,
        )

        row = CopilotLlmCallModel(
            tenant_id=uuid4(),
            turn_id=uuid4(),
            span_id=uuid4(),
            role="agent",
            provider="anthropic",
            model_requested="claude-3-5-sonnet",
            model_responded="claude-3-5-sonnet-20241022",
            pricing_version_id=uuid4(),
            input_unit_cost_usd=Decimal(0),
            output_unit_cost_usd=Decimal(0),
            cost_usd=Decimal(0),
            started_at=dt.datetime(2026, 4, 26, 12, 0, tzinfo=dt.UTC),
            duration_ms=10,
        )
        text = repr(row)
        assert "CopilotLlmCall" in text
        assert "anthropic" in text


class TestModelPricingSnapshotModel:
    def test_active_snapshot_roundtrip(self, db) -> None:
        from luana_core_observability.persistence.models.pricing_snapshot_model import (
            ModelPricingSnapshotModel,
        )

        snap = ModelPricingSnapshotModel(
            provider="openai",
            model="gpt-4o",
            input_cost_per_token=Decimal("0.0000025"),
            output_cost_per_token=Decimal("0.000010"),
            cache_read_cost_per_token=Decimal("0.00000125"),
            cache_write_cost_per_token=Decimal(0),
            source="litellm",
            source_etag="abc123",
            valid_from=dt.datetime(2026, 4, 26, 0, 0, tzinfo=dt.UTC),
            valid_to=None,
            raw_payload={"input_cost_per_token": 0.0000025},
        )
        db.add(snap)
        db.commit()

        fetched = db.query(ModelPricingSnapshotModel).one()
        assert fetched.provider == "openai"
        assert fetched.model == "gpt-4o"
        assert fetched.valid_to is None  # active snapshot

    def test_close_snapshot_sets_valid_to(self, db) -> None:
        from luana_core_observability.persistence.models.pricing_snapshot_model import (
            ModelPricingSnapshotModel,
        )

        snap = ModelPricingSnapshotModel(
            provider="openai",
            model="gpt-4o",
            input_cost_per_token=Decimal("0.0000025"),
            output_cost_per_token=Decimal("0.000010"),
            source="litellm",
            valid_from=dt.datetime(2026, 4, 1, 0, 0, tzinfo=dt.UTC),
            valid_to=dt.datetime(2026, 4, 26, 0, 0, tzinfo=dt.UTC),
            raw_payload={},
        )
        db.add(snap)
        db.commit()

        fetched = db.query(ModelPricingSnapshotModel).one()
        assert fetched.valid_to is not None


class TestTenantBillingConfigModel:
    def test_default_anchor_currency_fxsource(self, db) -> None:
        from luana_core_observability.persistence.models.tenant_billing_config_model import (
            TenantBillingConfigModel,
        )

        cfg = TenantBillingConfigModel(tenant_id=uuid4())
        db.add(cfg)
        db.commit()

        fetched = db.query(TenantBillingConfigModel).one()
        # Defaults declared on the column should land in the row.
        assert fetched.billing_cycle_anchor_day == 25
        assert fetched.billing_currency == "USD"
        assert fetched.fx_source == "frankfurter"

    def test_override_anchor_day(self, db) -> None:
        from luana_core_observability.persistence.models.tenant_billing_config_model import (
            TenantBillingConfigModel,
        )

        cfg = TenantBillingConfigModel(
            tenant_id=uuid4(),
            billing_cycle_anchor_day=15,
            billing_currency="MXN",
            fx_source="frankfurter",
        )
        db.add(cfg)
        db.commit()

        fetched = db.query(TenantBillingConfigModel).one()
        assert fetched.billing_cycle_anchor_day == 15
        assert fetched.billing_currency == "MXN"


@pytest.fixture
def db(db_engine):
    """Per-test transactional session.

    Wider conftest provides a session-scoped ``db`` using model_registry
    pre-import. We override here for clarity and to ensure the new
    observability models are present before ``Base.metadata.create_all``
    runs (the conftest imports them via the registry).
    """
    from sqlalchemy.orm import sessionmaker

    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()
