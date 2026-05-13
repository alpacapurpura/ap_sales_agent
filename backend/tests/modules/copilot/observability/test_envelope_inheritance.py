"""Regression test for the copilot envelope refactor (PR-2 PI-1.1).

Validates the inheritance contract:

1. ``CopilotObservabilityContext`` extends :class:`BaseObservabilityContext`.
2. Module-level alias ``ObservabilityContext = CopilotObservabilityContext``
   keeps ``from src.modules.copilot.observability import ObservabilityContext``
   working — 4260 conv import sites depend on this.
3. Lifecycle parity: ``turn_start`` + ``turn_end`` rows have the same
   shape as pre-refactor (smoke against in-memory SQLite).
4. ``_legacy_compat_keys_or_empty`` returns the full JSONB shape
   Streamlit consumes (model, prompt_tokens, ..., cache_hit_rate).
5. ``_aggregate_totals`` targets :class:`CopilotLlmCallModel`.
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


def _build_ctx(db):
    from luana_core_copilot.observability.persistence.llm_call_repository import (
        LlmCallRepository,
    )
    from luana_core_copilot.observability.persistence.trace_event_repository import (
        TraceEventRepository,
    )
    from luana_core_copilot.observability.recording.turn_envelope import ObservabilityContext

    pricing_resolver = MagicMock()
    fx_resolver = MagicMock()
    fx_resolver.resolve.return_value = (Decimal(1), "passthrough")

    return ObservabilityContext.start(
        tenant_id=uuid4(),
        conversation_id=uuid4(),
        user_id=uuid4(),
        llm_call_repo=LlmCallRepository(db),
        trace_repo=TraceEventRepository(db),
        pricing_resolver=pricing_resolver,
        fx_resolver=fx_resolver,
        tenant_currency="USD",
        role="agent",
    )


class TestInheritanceContract:
    def test_copilot_context_extends_base(self) -> None:
        from luana_core_copilot.observability.recording.turn_envelope import (
            CopilotObservabilityContext,
        )
        from luana_core_observability.recording.turn_envelope import (
            BaseObservabilityContext,
        )

        assert issubclass(CopilotObservabilityContext, BaseObservabilityContext)

    def test_observability_context_alias_is_copilot_subclass(self) -> None:
        """4260 conversation import sites depend on this alias."""
        from luana_core_copilot.observability import ObservabilityContext as PublicAlias
        from luana_core_copilot.observability.recording.turn_envelope import (
            CopilotObservabilityContext,
            ObservabilityContext as ModuleAlias,
        )

        assert PublicAlias is CopilotObservabilityContext
        assert ModuleAlias is CopilotObservabilityContext

    def test_subclass_does_not_redefine_locked_methods(self) -> None:
        """Locked methods (lifecycle, set_turn_*, langchain_config, _commit_session,
        _write_turn_*) MUST live on the base only — subclass overrides forbidden.
        """
        from luana_core_copilot.observability.recording.turn_envelope import (
            CopilotObservabilityContext,
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
        # Every locked method MUST resolve to the base, not the subclass body.
        own = set(vars(CopilotObservabilityContext).keys())
        overridden = locked & own
        assert not overridden, f"Subclass overrides locked methods: {overridden}"


class TestLifecycleParity:
    @pytest.mark.asyncio
    async def test_turn_start_and_turn_end_rows_persist(self, db) -> None:
        from luana_core_copilot.infrastructure.models.trace_event_model import (
            CopilotTraceEventModel,
        )

        ctx = _build_ctx(db)
        async with ctx.observe_turn(message="hola", route="/copilot/chat", attachments=[]):
            pass
        db.flush()

        rows = (
            db.query(CopilotTraceEventModel)
            .filter_by(turn_id=ctx.turn_id)
            .order_by(CopilotTraceEventModel.created_at.asc())
            .all()
        )
        events = {r.event_type for r in rows}
        assert "turn_start" in events
        assert "turn_end" in events


class TestLegacyCompatKeys:
    def test_legacy_compat_returns_jsonb_shape_streamlit_consumes(self) -> None:
        """Streamlit ``/trazas`` + ``/copilot-routing`` read these keys."""
        from luana_core_copilot.observability.recording.turn_envelope import (
            CopilotObservabilityContext,
        )

        # Probe the method signature directly — does not need a full instance.
        totals = {
            "llm_call_count": 1,
            "total_input_tokens": 100,
            "total_output_tokens": 50,
            "total_cached_read_tokens": 0,
            "total_cost_usd": "0.001",
            "model_responded": "gpt-4o",
        }
        # Build a minimal-arg instance to call the method on.
        ctx = CopilotObservabilityContext(
            tenant_id=uuid4(),
            conversation_id=uuid4(),
            user_id=uuid4(),
            turn_id=uuid4(),
            callback_handler=MagicMock(),
            trace_repo=MagicMock(),
            llm_call_repo=MagicMock(),
        )
        keys = ctx._legacy_compat_keys_or_empty(totals)
        # Streamlit-mandated shape:
        for required in (
            "model",
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "cached_input_tokens",
            "cache_hit_rate",
            "cost_usd",
            "response_length",
            "message_count",
            "block_count",
        ):
            assert required in keys, f"Missing legacy compat key: {required}"


class TestAggregateTargetsCopilotModel:
    def test_aggregate_totals_executes_against_copilot_llm_call_model(self, db) -> None:
        """Smoke that ``_aggregate_totals`` queries ``copilot_llm_call``."""
        from luana_core_copilot.observability.persistence.models.llm_call_model import (
            CopilotLlmCallModel,
        )

        ctx = _build_ctx(db)
        # Two LLM call rows for this turn.
        for i in range(2):
            db.add(
                CopilotLlmCallModel(
                    tenant_id=ctx.tenant_id,
                    turn_id=ctx.turn_id,
                    span_id=uuid4(),
                    role="agent",
                    provider="openai",
                    model_requested="gpt-4o",
                    model_responded="gpt-4o-2024-11-20",
                    input_tokens=100 * (i + 1),
                    output_tokens=50 * (i + 1),
                    cached_read_tokens=0,
                    cached_write_tokens=0,
                    reasoning_tokens=0,
                    pricing_version_id=uuid4(),
                    input_unit_cost_usd=Decimal("0.0000025"),
                    output_unit_cost_usd=Decimal("0.000010"),
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


class TestObserveTurnIsBaseConcrete:
    """Regression for arch invariant — subclass body MUST NOT shadow lifecycle."""

    def test_observe_turn_resolves_to_base_class(self) -> None:
        from luana_core_copilot.observability.recording.turn_envelope import (
            CopilotObservabilityContext,
        )
        from luana_core_observability.recording.turn_envelope import (
            BaseObservabilityContext,
        )

        # MRO inspection: the function descriptor should belong to the base.
        method = inspect.getattr_static(CopilotObservabilityContext, "observe_turn")
        base_method = inspect.getattr_static(BaseObservabilityContext, "observe_turn")
        assert method is base_method
