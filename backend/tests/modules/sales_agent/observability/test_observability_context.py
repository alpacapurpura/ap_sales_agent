"""Tests for :class:`SalesAgentObservabilityContext` (PR-2 PI-1.1).

NEW concrete subclass of :class:`BaseObservabilityContext`. Adds
``lead_id`` + ``channel_type`` fields; targets
:class:`SalesAgentLlmCallModel` for aggregation; returns ``{}`` from
:meth:`_legacy_compat_keys_or_empty` (sales_agent has no JSONB
consumer).

NOT a byte-mirror of copilot — class name distinct, fields distintos,
3 abstract method overrides distintos. Anti-duplication grep at arch
test enforces.
"""

from __future__ import annotations

import datetime as dt
import inspect
from decimal import Decimal
from unittest.mock import MagicMock
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


def _build_ctx(db, *, lead_id=None, channel_type="telegram"):
    """Build a sales_agent context bound to an in-memory session."""
    from src.modules.sales_agent.observability.persistence.llm_call_repository import (
        SalesAgentLlmCallRepository,
    )
    from src.modules.sales_agent.observability.persistence.trace_event_repository import (
        SalesAgentTraceEventRepository,
    )
    from src.modules.sales_agent.observability.recording.turn_envelope import (
        SalesAgentObservabilityContext,
    )

    pricing_resolver = MagicMock()
    fx_resolver = MagicMock()
    fx_resolver.resolve.return_value = (Decimal(1), "passthrough")

    return SalesAgentObservabilityContext.start(
        tenant_id=uuid4(),
        lead_id=lead_id or uuid4(),
        channel_type=channel_type,
        llm_call_repo=SalesAgentLlmCallRepository(db),
        trace_repo=SalesAgentTraceEventRepository(db),
        pricing_resolver=pricing_resolver,
        fx_resolver=fx_resolver,
        db_session=db,
        tenant_currency="USD",
        role="agent",
    )


class TestInheritanceContract:
    def test_extends_base(self) -> None:
        from src.modules.sales_agent.observability.recording.turn_envelope import (
            SalesAgentObservabilityContext,
        )
        from src.shared.agent_observability.recording.turn_envelope import (
            BaseObservabilityContext,
        )

        assert issubclass(SalesAgentObservabilityContext, BaseObservabilityContext)

    def test_does_not_redefine_locked_methods(self) -> None:
        """Lifecycle owned by base — subclass MUST NOT shadow."""
        from src.modules.sales_agent.observability.recording.turn_envelope import (
            SalesAgentObservabilityContext,
        )

        locked = {
            "observe_turn",
            "langchain_config",
            "set_turn_summary",
            "set_turn_error",
            "_write_turn_start",
            "_write_turn_end",
            "_commit_session",
            "_safe_aggregate_totals",
            "_safe_legacy_compat_keys",
        }
        own = set(vars(SalesAgentObservabilityContext).keys())
        overridden = locked & own
        assert not overridden, f"Sales subclass overrides locked methods: {overridden}"

    def test_observe_turn_resolves_to_base(self) -> None:
        from src.modules.sales_agent.observability.recording.turn_envelope import (
            SalesAgentObservabilityContext,
        )
        from src.shared.agent_observability.recording.turn_envelope import (
            BaseObservabilityContext,
        )

        method = inspect.getattr_static(SalesAgentObservabilityContext, "observe_turn")
        base_method = inspect.getattr_static(BaseObservabilityContext, "observe_turn")
        assert method is base_method


class TestPersistsAgentSpecificFields:
    @pytest.mark.asyncio
    async def test_turn_start_row_has_lead_id_and_channel_type(self, db) -> None:
        from src.modules.sales_agent.observability.persistence.models.trace_event_model import (
            SalesAgentTraceEventModel,
        )

        lead_id = uuid4()
        ctx = _build_ctx(db, lead_id=lead_id, channel_type="telegram")

        async with ctx.observe_turn(message="hola", route="sales_agent", attachments=[]):
            pass
        db.flush()

        rows = (
            db.query(SalesAgentTraceEventModel)
            .filter_by(turn_id=ctx.turn_id)
            .order_by(SalesAgentTraceEventModel.created_at.asc())
            .all()
        )
        assert len(rows) >= 2  # turn_start + turn_end
        for r in rows:
            assert r.lead_id == lead_id
            assert r.channel_type == "telegram"
            assert r.tenant_id == ctx.tenant_id


class TestAggregateTargetsSalesAgentModel:
    def test_aggregate_totals_targets_sales_agent_llm_call_model(self, db) -> None:
        from src.modules.sales_agent.observability.persistence.models.llm_call_model import (
            SalesAgentLlmCallModel,
        )

        ctx = _build_ctx(db)
        # Simulate two LLM call rows.
        for i in range(2):
            db.add(
                SalesAgentLlmCallModel(
                    tenant_id=ctx.tenant_id,
                    lead_id=ctx.lead_id,
                    channel_type=ctx.channel_type,
                    turn_id=ctx.turn_id,
                    span_id=uuid4(),
                    role="agent",
                    provider="moonshot",
                    model_requested="kimi-k2.6",
                    model_responded="kimi-k2.6",
                    input_tokens=100 * (i + 1),
                    output_tokens=50 * (i + 1),
                    cached_read_tokens=0,
                    cached_write_tokens=0,
                    reasoning_tokens=0,
                    pricing_version_id=uuid4(),
                    input_unit_cost_usd=Decimal("0.0000004"),
                    output_unit_cost_usd=Decimal("0.000002"),
                    cached_read_unit_cost_usd=Decimal(0),
                    cost_usd=Decimal("0.001") * (i + 1),
                    tenant_currency="USD",
                    fx_rate_to_tenant=Decimal(1),
                    fx_rate_source="passthrough",
                    cost_tenant_currency=Decimal("0.001") * (i + 1),
                    started_at=dt.datetime.now(tz=dt.UTC),
                    duration_ms=200,
                    status="ok",
                ),
            )
        db.flush()

        totals = ctx._aggregate_totals()
        assert totals["llm_call_count"] == 2
        assert totals["total_input_tokens"] == 300
        assert totals["total_output_tokens"] == 150


class TestLegacyCompatReturnsEmpty:
    def test_legacy_compat_keys_returns_empty(self) -> None:
        """Sales_agent has no JSONB consumer → empty dict."""
        from src.modules.sales_agent.observability.recording.turn_envelope import (
            SalesAgentObservabilityContext,
        )

        ctx = SalesAgentObservabilityContext(
            tenant_id=uuid4(),
            lead_id=uuid4(),
            channel_type="telegram",
            turn_id=uuid4(),
            callback_handler=MagicMock(),
            trace_repo=MagicMock(),
            llm_call_repo=MagicMock(),
        )
        keys = ctx._legacy_compat_keys_or_empty(
            {"llm_call_count": 1, "total_input_tokens": 100},
        )
        assert keys == {}


class TestObserveTurnLifecycle:
    @pytest.mark.asyncio
    async def test_clean_exit_writes_turn_start_and_end(self, db) -> None:
        from src.modules.sales_agent.observability.persistence.models.trace_event_model import (
            SalesAgentTraceEventModel,
        )

        ctx = _build_ctx(db)
        async with ctx.observe_turn(message="hola", route="sales_agent", attachments=[]):
            pass
        db.flush()

        events = {r.event_type for r in db.query(SalesAgentTraceEventModel).filter_by(turn_id=ctx.turn_id).all()}
        assert "turn_start" in events
        assert "turn_end" in events

    @pytest.mark.asyncio
    async def test_exception_marks_turn_end_status_error(self, db) -> None:
        from src.modules.sales_agent.observability.persistence.models.trace_event_model import (
            SalesAgentTraceEventModel,
        )

        ctx = _build_ctx(db)
        with pytest.raises(RuntimeError):
            async with ctx.observe_turn(message="hola", route="sales_agent", attachments=[]):
                msg = "boom"
                raise RuntimeError(msg)
        db.flush()

        end_row = db.query(SalesAgentTraceEventModel).filter_by(turn_id=ctx.turn_id, event_type="turn_end").one()
        assert end_row.status == "error"
        assert "RuntimeError" in (end_row.data or {}).get("error_type", "")
