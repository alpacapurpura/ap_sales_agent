"""End-to-end test for the observability module — runs in isolation.

Drives a real LangChain ``Runnable`` (a fake chat model that returns a
canned AIMessage with usage_metadata) with the observability callback
handler attached, exactly the way the orchestrator will at the Phase 2
atomic switch:

    runnable.ainvoke(input, config={"callbacks": [handler]})

Verifies the full pipeline — turn_start, llm_call row with cost > 0,
mirrored trace_event row, turn_end with totals — lands in DB without
any code under ``backend/src/modules/copilot/application/orchestrator/``
being touched.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
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


def _pricing_snapshot():
    snap = MagicMock()
    snap.id = uuid4()
    snap.provider = "openai"
    snap.model = "gpt-4o"
    snap.input_cost_per_token = Decimal("0.0000025")
    snap.output_cost_per_token = Decimal("0.000010")
    snap.cache_read_cost_per_token = Decimal("0.00000125")
    snap.cache_write_cost_per_token = Decimal(0)
    snap.valid_from = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
    snap.valid_to = None
    return snap


def _build_context(db):
    """Wire the new envelope to an in-memory SQLite session + mocked resolvers."""
    from luana_core_copilot.observability.persistence.llm_call_repository import LlmCallRepository
    from luana_core_copilot.observability.persistence.trace_event_repository import (
        TraceEventRepository,
    )
    from luana_core_copilot.observability.recording.turn_envelope import ObservabilityContext
    from luana_core_observability.pricing.resolver import PricingResult

    pricing_resolver = MagicMock()
    pricing_resolver.resolve.return_value = PricingResult(
        snapshot=_pricing_snapshot(),
        is_estimated=False,
    )
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


class _FakeChatModel:
    """Minimal callable-as-runnable that emits an AIMessage with usage_metadata.

    Wrapped in a ``RunnableLambda`` so LangChain's runtime fires
    ``on_chain_*`` (the lambda) but we manually fire ``on_chat_model_*``
    on the bound handler — which mirrors how a real chat model would
    propagate to the callback manager.

    T-1 (PI-12 S1, X2): the runtime cost source is now the LiteLLM
    ``CustomLogger`` cache populated via ``kwargs["response_cost"]``,
    NOT the legacy ``calculate_cost`` over a snapshot. The fake model
    pre-stashes a cost under the same ``litellm_call_id`` it embeds in
    the ``response_metadata`` so the bridge fires end-to-end.
    """

    def __init__(self, *, handler) -> None:
        self.handler = handler

    def __call__(self, _input):
        from luana_core_observability.recording.cost_recorder import (
            CostRecorderCustomLogger,
        )

        run_id = uuid4()
        call_id = "resp-001"
        # Pre-stash a cost via the LiteLLM CustomLogger — simulates LiteLLM
        # firing its callback after `litellm.completion(...)` returns. Real
        # LiteLLM does this in-process before the LangChain `on_llm_end`
        # closes the span.
        CostRecorderCustomLogger().log_success_event(
            kwargs={
                "litellm_call_id": call_id,
                "model": "openai/gpt-4o",
                "response_cost": 0.0125,
            },
            response_obj=type("_R", (), {"id": call_id})(),
            start_time=0.0,
            end_time=0.5,
        )
        # Emulate the BaseChatModel runtime: start, end-with-usage.
        self.handler.on_chat_model_start(
            serialized={},
            messages=[[]],
            run_id=run_id,
            metadata={"ls_provider": "openai", "ls_model_name": "openai/gpt-4o"},
        )
        ai = AIMessage(
            content="hi",
            response_metadata={
                "model_name": "gpt-4o-2024-11-20",
                "id": call_id,
                "litellm_call_id": call_id,
            },
            usage_metadata={
                "input_tokens": 1000,
                "output_tokens": 500,
                "total_tokens": 1500,
                "input_token_details": {"cache_read": 200},
            },
        )
        from langchain_core.outputs import ChatGeneration, LLMResult

        self.handler.on_llm_end(
            LLMResult(generations=[[ChatGeneration(message=ai)]]),
            run_id=run_id,
        )
        return ai


@pytest.mark.asyncio
async def test_full_turn_records_llm_call_and_trace_events(db) -> None:
    """A full turn through the envelope persists the canonical rows."""
    from luana_core_copilot.infrastructure.models.trace_event_model import (
        CopilotTraceEventModel,
    )
    from luana_core_copilot.observability.persistence.models.llm_call_model import (
        CopilotLlmCallModel,
    )

    ctx = _build_context(db)
    fake_model = _FakeChatModel(handler=ctx.callback_handler)
    runnable = RunnableLambda(fake_model)

    async with ctx.observe_turn(message="hola", route="/copilot/chat", attachments=[]):
        await runnable.ainvoke("ignored", config=ctx.langchain_config())
    db.flush()

    # Exactly 1 turn_start + 1 turn_end row.
    starts = db.query(CopilotTraceEventModel).filter_by(tenant_id=ctx.tenant_id, event_type="turn_start").all()
    ends = db.query(CopilotTraceEventModel).filter_by(tenant_id=ctx.tenant_id, event_type="turn_end").all()
    assert len(starts) == 1
    assert len(ends) == 1

    # 1 row in copilot_llm_call with cost > 0.
    llm_calls = db.query(CopilotLlmCallModel).filter_by(tenant_id=ctx.tenant_id, turn_id=ctx.turn_id).all()
    assert len(llm_calls) == 1
    assert llm_calls[0].cost_usd > 0
    assert llm_calls[0].input_tokens == 1000
    assert llm_calls[0].output_tokens == 500

    # 1 mirrored trace_event row with event_type='llm_call'.
    llm_traces = db.query(CopilotTraceEventModel).filter_by(tenant_id=ctx.tenant_id, event_type="llm_call").all()
    assert len(llm_traces) == 1
    assert "openai" in llm_traces[0].name

    # turn_end aggregates totals from the llm_call rows.
    end = ends[0]
    assert end.data["llm_call_count"] == 1
    assert end.data["total_input_tokens"] == 1000
    assert end.data["total_output_tokens"] == 500
    assert Decimal(end.data["total_cost_usd"]) > 0
