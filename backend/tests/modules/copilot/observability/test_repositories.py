"""Repository tests for the Phase 1 observability persistence layer.

Verifies the four repos (LLM call, pricing snapshot, tenant billing
config, trace event) wrap the new tables with tenant-isolated queries
and the basic operations needed by the callback handler / pricing
resolver / domain subscribers in later tasks.

Pricing repository is **global** (cross-tenant), justified in code:
``model_pricing_snapshot`` is reference data, not tenant data.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
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


# ── LlmCallRepository ───────────────────────────────────────────────────


def _make_llm_call_kwargs(tenant_id, *, turn_id=None, started_at=None, status="ok"):
    return {
        "tenant_id": tenant_id,
        "user_id": uuid4(),
        "conversation_id": uuid4(),
        "turn_id": turn_id or uuid4(),
        "span_id": uuid4(),
        "parent_span_id": None,
        "role": "agent",
        "provider": "openai",
        "model_requested": "gpt-4o",
        "model_responded": "gpt-4o-2024-11-20",
        "input_tokens": 100,
        "output_tokens": 50,
        "cached_read_tokens": 0,
        "cached_write_tokens": 0,
        "reasoning_tokens": 0,
        "pricing_version_id": uuid4(),
        "input_unit_cost_usd": Decimal("0.0000025"),
        "output_unit_cost_usd": Decimal("0.000010"),
        "cached_read_unit_cost_usd": Decimal(0),
        "cost_usd": Decimal("0.000750"),
        "tenant_currency": "USD",
        "fx_rate_to_tenant": Decimal("1.00000000"),
        "fx_rate_source": "frankfurter",
        "cost_tenant_currency": Decimal("0.00075000"),
        "started_at": started_at or dt.datetime(2026, 4, 26, 12, 0, tzinfo=dt.UTC),
        "duration_ms": 250,
        "status": status,
        "error_type": None,
    }


class TestLlmCallRepository:
    def test_add_and_find_by_turn(self, db) -> None:
        from luana_core_copilot.observability.persistence.llm_call_repository import (
            LlmCallRepository,
        )

        repo = LlmCallRepository(db)
        tenant = uuid4()
        turn = uuid4()
        repo.add(**_make_llm_call_kwargs(tenant, turn_id=turn))
        repo.add(**_make_llm_call_kwargs(tenant, turn_id=turn))
        # Different turn — should not be returned by find_by_turn(turn).
        repo.add(**_make_llm_call_kwargs(tenant, turn_id=uuid4()))
        db.flush()

        rows = repo.find_by_turn(tenant_id=tenant, turn_id=turn)
        assert len(rows) == 2
        assert all(r.turn_id == turn for r in rows)

    def test_find_by_tenant_range(self, db) -> None:
        from luana_core_copilot.observability.persistence.llm_call_repository import (
            LlmCallRepository,
        )

        repo = LlmCallRepository(db)
        tenant = uuid4()
        repo.add(**_make_llm_call_kwargs(tenant, started_at=dt.datetime(2026, 4, 25, 10, 0, tzinfo=dt.UTC)))
        repo.add(**_make_llm_call_kwargs(tenant, started_at=dt.datetime(2026, 4, 26, 10, 0, tzinfo=dt.UTC)))
        repo.add(**_make_llm_call_kwargs(tenant, started_at=dt.datetime(2026, 4, 27, 10, 0, tzinfo=dt.UTC)))
        db.flush()

        rows = repo.find_by_tenant_range(
            tenant_id=tenant,
            start=dt.datetime(2026, 4, 26, 0, 0, tzinfo=dt.UTC),
            end=dt.datetime(2026, 4, 27, 0, 0, tzinfo=dt.UTC),
        )
        assert len(rows) == 1
        assert rows[0].started_at.day == 26

    def test_count_errors_today(self, db) -> None:
        from luana_core_copilot.observability.persistence.llm_call_repository import (
            LlmCallRepository,
        )

        repo = LlmCallRepository(db)
        tenant = uuid4()
        today = dt.datetime.now(tz=dt.UTC)
        repo.add(**_make_llm_call_kwargs(tenant, started_at=today, status="error"))
        repo.add(**_make_llm_call_kwargs(tenant, started_at=today, status="error"))
        repo.add(**_make_llm_call_kwargs(tenant, started_at=today, status="ok"))
        db.flush()

        count = repo.count_errors_today(tenant_id=tenant)
        assert count == 2

    def test_tenant_isolation_on_find_by_turn(self, db) -> None:
        from luana_core_copilot.observability.persistence.llm_call_repository import (
            LlmCallRepository,
        )

        repo = LlmCallRepository(db)
        tenant_a = uuid4()
        tenant_b = uuid4()
        turn = uuid4()
        # Same turn id used by two different tenants — IDs collide in tests.
        repo.add(**_make_llm_call_kwargs(tenant_a, turn_id=turn))
        repo.add(**_make_llm_call_kwargs(tenant_b, turn_id=turn))
        db.flush()

        rows = repo.find_by_turn(tenant_id=tenant_a, turn_id=turn)
        assert len(rows) == 1
        assert rows[0].tenant_id == tenant_a


# ── PricingSnapshotRepository ────────────────────────────────────────────


def _make_pricing_kwargs(provider="openai", model="gpt-4o", *, valid_from=None, valid_to=None):
    return {
        "provider": provider,
        "model": model,
        "input_cost_per_token": Decimal("0.0000025"),
        "output_cost_per_token": Decimal("0.000010"),
        "cache_read_cost_per_token": Decimal("0.00000125"),
        "cache_write_cost_per_token": Decimal(0),
        "batch_input_cost_per_token": None,
        "source": "litellm",
        "source_etag": "abc123",
        "valid_from": valid_from or dt.datetime(2026, 4, 1, 0, 0, tzinfo=dt.UTC),
        "valid_to": valid_to,
        "raw_payload": {},
    }


class TestPricingSnapshotRepository:
    def test_add_and_find_active(self, db) -> None:
        from luana_core_observability.persistence.pricing_snapshot_repository import (
            PricingSnapshotRepository,
        )

        repo = PricingSnapshotRepository(db)
        repo.add(**_make_pricing_kwargs())
        db.flush()

        active = repo.find_active(provider="openai", model="gpt-4o")
        assert active is not None
        assert active.valid_to is None

    def test_find_active_returns_none_when_missing(self, db) -> None:
        from luana_core_observability.persistence.pricing_snapshot_repository import (
            PricingSnapshotRepository,
        )

        repo = PricingSnapshotRepository(db)
        active = repo.find_active(provider="openai", model="nonexistent-model")
        assert active is None

    def test_close_active_sets_valid_to(self, db) -> None:
        from luana_core_observability.persistence.pricing_snapshot_repository import (
            PricingSnapshotRepository,
        )

        repo = PricingSnapshotRepository(db)
        repo.add(**_make_pricing_kwargs())
        db.flush()

        cutoff = dt.datetime(2026, 4, 26, 0, 0, tzinfo=dt.UTC)
        closed = repo.close_active(provider="openai", model="gpt-4o", at_ts=cutoff)
        db.flush()
        assert closed is not None
        assert closed.valid_to == cutoff

        active_after = repo.find_active(provider="openai", model="gpt-4o")
        assert active_after is None

    def test_find_at_returns_correct_snapshot_for_timestamp(self, db) -> None:
        from luana_core_observability.persistence.pricing_snapshot_repository import (
            PricingSnapshotRepository,
        )

        repo = PricingSnapshotRepository(db)
        # Old snapshot (closed).
        repo.add(
            **_make_pricing_kwargs(
                valid_from=dt.datetime(2026, 1, 1, 0, 0, tzinfo=dt.UTC),
                valid_to=dt.datetime(2026, 4, 1, 0, 0, tzinfo=dt.UTC),
            ),
        )
        # New snapshot (active).
        repo.add(
            **_make_pricing_kwargs(
                valid_from=dt.datetime(2026, 4, 1, 0, 0, tzinfo=dt.UTC),
                valid_to=None,
            ),
        )
        db.flush()

        # Call from Feb 2026 must resolve to the older row.
        snap = repo.find_at(
            provider="openai",
            model="gpt-4o",
            at_ts=dt.datetime(2026, 2, 15, 0, 0, tzinfo=dt.UTC),
        )
        assert snap is not None
        assert snap.valid_to is not None
        # Call from May 2026 must resolve to the active row.
        snap2 = repo.find_at(
            provider="openai",
            model="gpt-4o",
            at_ts=dt.datetime(2026, 5, 15, 0, 0, tzinfo=dt.UTC),
        )
        assert snap2 is not None
        assert snap2.valid_to is None


# ── TenantBillingConfigRepository ────────────────────────────────────────


class TestTenantBillingConfigRepository:
    def test_get_returns_none_for_unconfigured_tenant(self, db) -> None:
        from luana_core_observability.persistence.tenant_billing_config_repository import (
            TenantBillingConfigRepository,
        )

        repo = TenantBillingConfigRepository(db)
        assert repo.get(tenant_id=uuid4()) is None

    def test_upsert_inserts_then_updates(self, db) -> None:
        from luana_core_observability.persistence.tenant_billing_config_repository import (
            TenantBillingConfigRepository,
        )

        repo = TenantBillingConfigRepository(db)
        tenant = uuid4()
        first = repo.upsert(
            tenant_id=tenant,
            billing_cycle_anchor_day=15,
            billing_currency="MXN",
            fx_source="frankfurter",
        )
        db.flush()
        assert first.billing_cycle_anchor_day == 15

        # Second upsert overwrites — same tenant_id (PK).
        second = repo.upsert(
            tenant_id=tenant,
            billing_cycle_anchor_day=20,
            billing_currency="USD",
            fx_source="frankfurter",
        )
        db.flush()
        assert second.billing_cycle_anchor_day == 20
        assert second.billing_currency == "USD"


# ── TraceEventRepository ─────────────────────────────────────────────────


class TestTraceEventRepository:
    def test_add_inserts_row(self, db) -> None:
        from luana_core_copilot.observability.persistence.trace_event_repository import (
            TraceEventRepository,
        )

        repo = TraceEventRepository(db)
        tenant = uuid4()
        turn = uuid4()
        span = uuid4()
        row = repo.add(
            tenant_id=tenant,
            turn_id=turn,
            span_id=span,
            event_type="llm_call",
            name="agent.chat",
            data={"input_tokens": 100, "output_tokens": 50},
            duration_ms=250,
            status="ok",
        )
        db.flush()
        assert row.id is not None
        assert row.tenant_id == tenant

    def test_list_by_turn_filters_tenant(self, db) -> None:
        from luana_core_copilot.observability.persistence.trace_event_repository import (
            TraceEventRepository,
        )

        repo = TraceEventRepository(db)
        tenant_a, tenant_b = uuid4(), uuid4()
        turn = uuid4()
        repo.add(
            tenant_id=tenant_a,
            turn_id=turn,
            span_id=uuid4(),
            event_type="turn_start",
        )
        repo.add(
            tenant_id=tenant_b,
            turn_id=turn,
            span_id=uuid4(),
            event_type="turn_start",
        )
        db.flush()

        rows = repo.list_by_turn(tenant_id=tenant_a, turn_id=turn)
        assert len(rows) == 1
        assert rows[0].tenant_id == tenant_a
