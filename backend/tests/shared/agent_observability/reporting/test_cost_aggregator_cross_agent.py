"""Cross-agent cost aggregator — S2.

Validates:

* :class:`CostAggregator` works against either the copilot or sales_agent
  ``*_llm_call`` model class (model-class injection, no SQL hardcoded).
* :class:`CrossAgentCostAggregator` sums per-agent rollups for a single
  tenant and returns a per-agent breakdown ready for cost alerts.
* Tenant scope is preserved across both backends (no leakage between
  tenants).
* :meth:`CostAggregator.top_leads_by_cost` works against the sales model
  (which exposes ``lead_id``); :meth:`top_conversations_by_cost` raises
  ``AttributeError`` for the same model (defensive contract).
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import sessionmaker

from src.modules.copilot.observability.persistence.models.llm_call_model import (
    CopilotLlmCallModel,
)
from src.modules.sales_agent.observability.persistence.models.llm_call_model import (
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


def _copilot_call(
    *,
    tenant_id: UUID,
    started_at: dt.datetime,
    cost_usd: Decimal,
    turn_id: UUID | None = None,
) -> dict:
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
        "model_responded": "gpt-4o",
        "input_tokens": 100,
        "output_tokens": 50,
        "cached_read_tokens": 0,
        "cached_write_tokens": 0,
        "reasoning_tokens": 0,
        "pricing_version_id": uuid4(),
        "input_unit_cost_usd": Decimal("0.0000025"),
        "output_unit_cost_usd": Decimal("0.000010"),
        "cached_read_unit_cost_usd": Decimal(0),
        "cost_usd": cost_usd,
        "tenant_currency": "USD",
        "fx_rate_to_tenant": Decimal("1.0"),
        "fx_rate_source": "passthrough",
        "cost_tenant_currency": cost_usd,
        "started_at": started_at,
        "duration_ms": 1500,
        "status": "ok",
        "error_type": None,
    }


def _sales_call(
    *,
    tenant_id: UUID,
    lead_id: UUID,
    started_at: dt.datetime,
    cost_usd: Decimal,
    turn_id: UUID | None = None,
    channel_type: str = "whatsapp",
) -> dict:
    return {
        "tenant_id": tenant_id,
        "lead_id": lead_id,
        "channel_type": channel_type,
        "turn_id": turn_id or uuid4(),
        "span_id": uuid4(),
        "parent_span_id": None,
        "role": "agent",
        "provider": "kimi",
        "model_requested": "kimi-k2.6",
        "model_responded": "kimi-k2.6",
        "input_tokens": 200,
        "output_tokens": 80,
        "cached_read_tokens": 0,
        "cached_write_tokens": 0,
        "reasoning_tokens": 0,
        "pricing_version_id": uuid4(),
        "input_unit_cost_usd": Decimal("0.0000004"),
        "output_unit_cost_usd": Decimal("0.000002"),
        "cached_read_unit_cost_usd": Decimal(0),
        "cost_usd": cost_usd,
        "tenant_currency": "USD",
        "fx_rate_to_tenant": Decimal("1.0"),
        "fx_rate_source": "passthrough",
        "cost_tenant_currency": cost_usd,
        "started_at": started_at,
        "duration_ms": 2200,
        "status": "ok",
        "error_type": None,
    }


@pytest.fixture
def seed_cross_agent(db):
    """Seed copilot + sales_agent calls for two tenants."""
    tenant_a = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    tenant_b = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
    base = dt.datetime(2026, 4, 26, 12, 0, tzinfo=dt.UTC)

    # tenant_a: 2 copilot calls + 3 sales calls (2 leads).
    db.add(CopilotLlmCallModel(**_copilot_call(tenant_id=tenant_a, started_at=base, cost_usd=Decimal("0.0050"))))
    db.add(
        CopilotLlmCallModel(
            **_copilot_call(tenant_id=tenant_a, started_at=base + dt.timedelta(hours=1), cost_usd=Decimal("0.0030")),
        ),
    )
    lead_x = uuid4()
    lead_y = uuid4()
    db.add(
        SalesAgentLlmCallModel(
            **_sales_call(tenant_id=tenant_a, lead_id=lead_x, started_at=base, cost_usd=Decimal("0.0200"))
        )
    )
    db.add(
        SalesAgentLlmCallModel(
            **_sales_call(
                tenant_id=tenant_a,
                lead_id=lead_x,
                started_at=base + dt.timedelta(minutes=10),
                cost_usd=Decimal("0.0100"),
            ),
        ),
    )
    db.add(
        SalesAgentLlmCallModel(
            **_sales_call(
                tenant_id=tenant_a, lead_id=lead_y, started_at=base + dt.timedelta(hours=2), cost_usd=Decimal("0.0050")
            ),
        ),
    )

    # tenant_b: only copilot calls — sales tab should be 0.
    db.add(CopilotLlmCallModel(**_copilot_call(tenant_id=tenant_b, started_at=base, cost_usd=Decimal("0.0040"))))
    db.flush()
    return tenant_a, tenant_b, base, lead_x, lead_y


class TestCostAggregatorParametrized:
    def test_aggregator_against_copilot_model(self, db, seed_cross_agent) -> None:
        from src.shared.agent_observability.reporting.cost_aggregator import (
            CostAggregator,
        )

        tenant_a, _, base, _, _ = seed_cross_agent
        agg = CostAggregator(db, CopilotLlmCallModel)

        detail = agg.tenant_detail(
            tenant_id=tenant_a,
            start=base.date(),
            end=(base + dt.timedelta(days=2)).date(),
        )
        assert detail.cost_usd == Decimal("0.0080")
        assert detail.call_count == 2

    def test_aggregator_against_sales_model(self, db, seed_cross_agent) -> None:
        from src.shared.agent_observability.reporting.cost_aggregator import (
            CostAggregator,
        )

        tenant_a, _, base, _, _ = seed_cross_agent
        agg = CostAggregator(db, SalesAgentLlmCallModel)

        detail = agg.tenant_detail(
            tenant_id=tenant_a,
            start=base.date(),
            end=(base + dt.timedelta(days=2)).date(),
        )
        assert detail.cost_usd == Decimal("0.0350")
        assert detail.call_count == 3

    def test_top_leads_for_sales_model(self, db, seed_cross_agent) -> None:
        from src.shared.agent_observability.reporting.cost_aggregator import (
            CostAggregator,
        )

        tenant_a, _, base, lead_x, lead_y = seed_cross_agent
        agg = CostAggregator(db, SalesAgentLlmCallModel)

        rows = agg.top_leads_by_cost(
            tenant_id=tenant_a,
            start=base.date(),
            end=(base + dt.timedelta(days=2)).date(),
        )
        assert len(rows) == 2
        # lead_x has 2 calls totalling $0.0300; lead_y has 1 call $0.0050.
        assert rows[0].lead_id == lead_x
        assert rows[0].cost_usd == Decimal("0.0300")
        assert rows[1].lead_id == lead_y

    def test_top_conversations_unsupported_for_sales(self, db) -> None:
        from src.shared.agent_observability.reporting.cost_aggregator import (
            CostAggregator,
        )

        agg = CostAggregator(db, SalesAgentLlmCallModel)
        with pytest.raises(AttributeError, match="conversation_id"):
            agg.top_conversations_by_cost(
                tenant_id=uuid4(),
                start=dt.date(2026, 4, 1),
                end=dt.date(2026, 4, 30),
            )

    def test_top_leads_unsupported_for_copilot(self, db) -> None:
        from src.shared.agent_observability.reporting.cost_aggregator import (
            CostAggregator,
        )

        agg = CostAggregator(db, CopilotLlmCallModel)
        with pytest.raises(AttributeError, match="lead_id"):
            agg.top_leads_by_cost(
                tenant_id=uuid4(),
                start=dt.date(2026, 4, 1),
                end=dt.date(2026, 4, 30),
            )


class TestCrossAgentCostAggregator:
    def test_breakdown_sums_both_agents(self, db, seed_cross_agent) -> None:
        from src.shared.agent_observability.reporting.cost_aggregator import (
            CrossAgentCostAggregator,
        )

        tenant_a, _, base, _, _ = seed_cross_agent
        cross = CrossAgentCostAggregator(db)

        breakdown = cross.tenant_breakdown(
            tenant_id=tenant_a,
            start=base.date(),
            end=(base + dt.timedelta(days=2)).date(),
        )
        # 0.0080 (copilot) + 0.0350 (sales) = 0.0430.
        assert breakdown.cost_usd == Decimal("0.0430")
        assert breakdown.call_count == 5
        by_kind = {b.agent_kind: b for b in breakdown.by_agent}
        assert by_kind["copilot"].cost_usd == Decimal("0.0080")
        assert by_kind["sales_agent"].cost_usd == Decimal("0.0350")

    def test_tenant_without_sales_calls_returns_zero_for_sales(self, db, seed_cross_agent) -> None:
        from src.shared.agent_observability.reporting.cost_aggregator import (
            CrossAgentCostAggregator,
        )

        _, tenant_b, base, _, _ = seed_cross_agent
        cross = CrossAgentCostAggregator(db)

        breakdown = cross.tenant_breakdown(
            tenant_id=tenant_b,
            start=base.date(),
            end=(base + dt.timedelta(days=2)).date(),
        )
        assert breakdown.cost_usd == Decimal("0.0040")
        by_kind = {b.agent_kind: b for b in breakdown.by_agent}
        assert by_kind["copilot"].cost_usd == Decimal("0.0040")
        assert by_kind["sales_agent"].cost_usd == Decimal(0)
        assert by_kind["sales_agent"].call_count == 0

    def test_summary_keyed_by_agent_kind(self, db, seed_cross_agent) -> None:
        from src.shared.agent_observability.reporting.cost_aggregator import (
            CrossAgentCostAggregator,
        )

        _, _, base, _, _ = seed_cross_agent
        cross = CrossAgentCostAggregator(db)

        summary = cross.tenants_summary_by_agent(
            start=base.date(),
            end=(base + dt.timedelta(days=2)).date(),
        )
        assert set(summary.keys()) == {"copilot", "sales_agent"}
        # tenant_a appears in both, tenant_b only in copilot.
        copilot_tenants = {row.tenant_id for row in summary["copilot"]}
        sales_tenants = {row.tenant_id for row in summary["sales_agent"]}
        assert len(copilot_tenants) == 2
        assert len(sales_tenants) == 1


class TestRegistryWiring:
    def test_registry_lists_known_agents(self) -> None:
        from src.shared.agent_observability.registry import (
            agent_observability_registry,
            get_spec,
        )

        registry = agent_observability_registry()
        kinds = {spec.agent_kind for spec in registry}
        assert "copilot" in kinds
        assert "sales_agent" in kinds

        copilot_spec = get_spec("copilot")
        assert copilot_spec.has_lead_id is False
        assert copilot_spec.trace_event_table == "copilot_trace_event"

        sales_spec = get_spec("sales_agent")
        assert sales_spec.has_lead_id is True
        assert sales_spec.trace_event_table == "sales_agent_trace_event"

    def test_unknown_agent_raises(self) -> None:
        from src.shared.agent_observability.registry import get_spec

        with pytest.raises(KeyError, match="Unknown agent_kind"):
            get_spec("email_agent_2099")
