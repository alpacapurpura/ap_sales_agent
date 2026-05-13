"""Tests for ``CostAggregator``.

The aggregator queries ``copilot_llm_call`` (and the MV when available)
to feed the costo-copilot dashboard. Tests use SQLite in-memory with the
same model classes; SQL portability is preserved by sticking to ANSI
``SUM/COUNT/AVG`` operations and avoiding Postgres-only constructs in
the aggregator code path itself (the MV refresh stays Postgres-only and
gets bypassed in tests by reading directly from ``copilot_llm_call``).
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import sessionmaker

from luana_core_copilot.observability.persistence.models.llm_call_model import (
    CopilotLlmCallModel,
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


def _make_call(
    *,
    tenant_id: UUID,
    started_at: dt.datetime,
    cost_usd: Decimal,
    cost_tenant_currency: Decimal | None = None,
    tenant_currency: str | None = "USD",
    model_responded: str = "gpt-4o-2024-11-20",
    provider: str = "openai",
    role: str = "agent",
    status: str = "ok",
    turn_id: UUID | None = None,
    conversation_id: UUID | None = None,
    input_tokens: int = 100,
    output_tokens: int = 50,
):
    """Build column kwargs ready to feed ``LlmCallRepository.add``."""
    return {
        "tenant_id": tenant_id,
        "user_id": uuid4(),
        "conversation_id": conversation_id or uuid4(),
        "turn_id": turn_id or uuid4(),
        "span_id": uuid4(),
        "parent_span_id": None,
        "role": role,
        "provider": provider,
        "model_requested": model_responded,
        "model_responded": model_responded,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cached_read_tokens": 0,
        "cached_write_tokens": 0,
        "reasoning_tokens": 0,
        "pricing_version_id": uuid4(),
        "input_unit_cost_usd": Decimal("0.0000025"),
        "output_unit_cost_usd": Decimal("0.000010"),
        "cached_read_unit_cost_usd": Decimal(0),
        "cost_usd": cost_usd,
        "tenant_currency": tenant_currency,
        "fx_rate_to_tenant": Decimal("1.0") if tenant_currency == "USD" else None,
        "fx_rate_source": "passthrough" if tenant_currency == "USD" else None,
        "cost_tenant_currency": cost_tenant_currency,
        "started_at": started_at,
        "duration_ms": 1500,
        "status": status,
        "error_type": None,
    }


@pytest.fixture
def seed(db):
    """Seed two tenants x multiple calls across two days."""
    from luana_core_copilot.observability.persistence.llm_call_repository import (
        LlmCallRepository,
    )

    tenant_a = UUID("11111111-1111-1111-1111-111111111111")
    tenant_b = UUID("22222222-2222-2222-2222-222222222222")
    repo = LlmCallRepository(db)

    base = dt.datetime(2026, 4, 26, 12, 0, tzinfo=dt.UTC)
    # tenant_a — 3 calls (2 ok, 1 error) on day 1, 1 call on day 2.
    conv_a1 = uuid4()
    conv_a2 = uuid4()
    turn_a1 = uuid4()
    repo.add(
        **_make_call(
            tenant_id=tenant_a,
            started_at=base,
            cost_usd=Decimal("0.0050"),
            cost_tenant_currency=Decimal("0.0050"),
            turn_id=turn_a1,
            conversation_id=conv_a1,
        ),
    )
    repo.add(
        **_make_call(
            tenant_id=tenant_a,
            started_at=base + dt.timedelta(seconds=10),
            cost_usd=Decimal("0.0030"),
            cost_tenant_currency=Decimal("0.0030"),
            turn_id=turn_a1,
            conversation_id=conv_a1,
        ),
    )
    repo.add(
        **_make_call(
            tenant_id=tenant_a,
            started_at=base + dt.timedelta(seconds=20),
            cost_usd=Decimal("0.0010"),
            cost_tenant_currency=Decimal("0.0010"),
            status="error",
            conversation_id=conv_a2,
        ),
    )
    repo.add(
        **_make_call(
            tenant_id=tenant_a,
            started_at=base + dt.timedelta(days=1),
            cost_usd=Decimal("0.0020"),
            cost_tenant_currency=Decimal("0.0020"),
            model_responded="claude-3-7-sonnet",
            provider="anthropic",
            conversation_id=conv_a2,
        ),
    )
    # tenant_b — 1 call.
    repo.add(
        **_make_call(
            tenant_id=tenant_b,
            started_at=base,
            cost_usd=Decimal("0.0100"),
            cost_tenant_currency=Decimal("0.0100"),
        ),
    )
    db.flush()
    return tenant_a, tenant_b, base


class TestTenantsSummary:
    def test_returns_one_row_per_tenant_in_window(self, db, seed) -> None:
        from luana_core_observability.reporting.cost_aggregator import (
            CostAggregator,
        )

        tenant_a, tenant_b, base = seed
        agg = CostAggregator(db, CopilotLlmCallModel)

        rows = agg.tenants_summary(
            start=base.date(),
            end=(base + dt.timedelta(days=2)).date(),
        )

        rows_by_tenant = {row.tenant_id: row for row in rows}
        assert tenant_a in rows_by_tenant
        assert tenant_b in rows_by_tenant
        assert rows_by_tenant[tenant_a].call_count == 4
        assert rows_by_tenant[tenant_a].turn_count == 3
        assert rows_by_tenant[tenant_a].error_count == 1
        assert rows_by_tenant[tenant_a].cost_usd == Decimal("0.0110")
        assert rows_by_tenant[tenant_b].call_count == 1
        assert rows_by_tenant[tenant_b].cost_usd == Decimal("0.0100")

    def test_excludes_calls_outside_window(self, db, seed) -> None:
        from luana_core_observability.reporting.cost_aggregator import (
            CostAggregator,
        )

        _, _, base = seed
        agg = CostAggregator(db, CopilotLlmCallModel)

        rows = agg.tenants_summary(
            start=(base + dt.timedelta(days=10)).date(),
            end=(base + dt.timedelta(days=20)).date(),
        )
        assert rows == []


class TestTenantDetail:
    def test_breakdown_by_model_inside_window(self, db, seed) -> None:
        from luana_core_observability.reporting.cost_aggregator import (
            CostAggregator,
        )

        tenant_a, _, base = seed
        agg = CostAggregator(db, CopilotLlmCallModel)

        detail = agg.tenant_detail(
            tenant_id=tenant_a,
            start=base.date(),
            end=(base + dt.timedelta(days=2)).date(),
        )

        assert detail.tenant_id == tenant_a
        assert detail.cost_usd == Decimal("0.0110")
        assert detail.call_count == 4
        assert detail.turn_count == 3

        models_by_name = {m.model: m for m in detail.by_model}
        assert "gpt-4o-2024-11-20" in models_by_name
        assert "claude-3-7-sonnet" in models_by_name
        assert models_by_name["gpt-4o-2024-11-20"].call_count == 3
        assert models_by_name["claude-3-7-sonnet"].call_count == 1


class TestTopConversations:
    def test_returns_top_conversations_ordered_by_cost(self, db, seed) -> None:
        from luana_core_observability.reporting.cost_aggregator import (
            CostAggregator,
        )

        tenant_a, _, base = seed
        agg = CostAggregator(db, CopilotLlmCallModel)

        rows = agg.top_conversations_by_cost(
            tenant_id=tenant_a,
            start=base.date(),
            end=(base + dt.timedelta(days=2)).date(),
            limit=5,
        )

        # Two distinct conversations under tenant_a.
        assert len(rows) == 2
        # The first conversation owns 2 calls totalling $0.0080 (>$0.0030 of the other).
        assert rows[0].cost_usd >= rows[1].cost_usd


class TestDailySeries:
    def test_returns_daily_points_for_window(self, db, seed) -> None:
        from luana_core_observability.reporting.cost_aggregator import (
            CostAggregator,
        )

        tenant_a, _, base = seed
        agg = CostAggregator(db, CopilotLlmCallModel)

        series = agg.daily_series(
            tenant_id=tenant_a,
            start=base.date(),
            end=(base + dt.timedelta(days=2)).date(),
        )

        days = {p.day for p in series}
        assert base.date() in days
        assert (base + dt.timedelta(days=1)).date() in days


class TestEmptyState:
    def test_empty_when_no_data(self, db) -> None:
        """Aggregator returns sane empty defaults for a tenant with no calls."""
        from luana_core_observability.reporting.cost_aggregator import (
            CostAggregator,
        )

        agg = CostAggregator(db, CopilotLlmCallModel)
        rows = agg.tenants_summary(
            start=dt.date(2026, 4, 1),
            end=dt.date(2026, 4, 30),
        )
        assert rows == []

        detail = agg.tenant_detail(
            tenant_id=uuid4(),
            start=dt.date(2026, 4, 1),
            end=dt.date(2026, 4, 30),
        )
        assert detail.call_count == 0
        assert detail.cost_usd == Decimal(0)
        assert detail.by_model == []
