"""Tests for the LangChain callback handler.

Drives synthetic ``BaseCallbackHandler`` calls (matching the real
``langchain_core`` signatures verified in research) and verifies:

* ``on_chat_model_start`` + ``on_llm_end`` together persist a row in
  ``copilot_llm_call`` with tokens and cost set from the pricing
  resolver.
* ``on_tool_start`` + ``on_tool_end`` persist one ``copilot_trace_event``
  row with ``event_type='tool_call'`` and ``duration_ms``.
* ``on_llm_error`` and ``on_tool_error`` write rows with ``status='error'``.
* DB exceptions are swallowed — handler is best-effort.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, LLMResult
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


def _make_handler(db, *, pricing_snapshot=None, fx_rate=Decimal(1), fx_source="passthrough"):
    """Build a handler with mocked pricing/FX resolvers and the test session."""
    from luana_core_copilot.observability.persistence.llm_call_repository import LlmCallRepository
    from luana_core_copilot.observability.persistence.trace_event_repository import (
        TraceEventRepository,
    )
    from luana_core_copilot.observability.recording.callback_handler import (
        ObservabilityCallbackHandler,
    )
    from luana_core_observability.pricing.resolver import PricingResult

    pricing_resolver = MagicMock()
    pricing_resolver.resolve.return_value = PricingResult(
        snapshot=pricing_snapshot or _pricing_snapshot(),
        is_estimated=False,
    )
    fx_resolver = MagicMock()
    fx_resolver.resolve.return_value = (fx_rate, fx_source)

    return ObservabilityCallbackHandler(
        tenant_id=uuid4(),
        conversation_id=uuid4(),
        user_id=uuid4(),
        turn_id=uuid4(),
        llm_call_repo=LlmCallRepository(db),
        trace_repo=TraceEventRepository(db),
        pricing_resolver=pricing_resolver,
        fx_resolver=fx_resolver,
        tenant_currency="USD",
        role="agent",
    )


def _ai_message_with_usage(*, model_name="gpt-4o-2024-11-20", litellm_call_id: str | None = None):
    response_metadata: dict = {"model_name": model_name, "id": "resp-001"}
    if litellm_call_id is not None:
        response_metadata["litellm_call_id"] = litellm_call_id
    msg = AIMessage(
        content="hello world",
        response_metadata=response_metadata,
        usage_metadata={
            "input_tokens": 1000,
            "output_tokens": 500,
            "total_tokens": 1500,
            "input_token_details": {"cache_read": 200},
        },
    )
    return msg


def _stash_cost(call_id: str, cost: float, *, model: str = "openai/gpt-4o") -> None:
    """Pre-populate the LiteLLM cost cache for a synthetic call.

    T-1 (PI-12 S1, X2): runtime cost flows through
    :class:`CostRecorderCustomLogger`'s TTL cache. Tests that don't
    invoke real LiteLLM must pre-stash via this helper so the LangChain
    handler picks up the cost on ``on_llm_end``.
    """
    from luana_core_observability.recording.cost_recorder import (
        CostRecorderCustomLogger,
    )

    CostRecorderCustomLogger().log_success_event(
        kwargs={"litellm_call_id": call_id, "model": model, "response_cost": cost},
        response_obj=type("_R", (), {"id": call_id})(),
        start_time=0.0,
        end_time=0.5,
    )


class TestChatModelLifecycle:
    def test_start_then_end_persists_llm_call_row(self, db) -> None:
        from luana_core_copilot.observability.persistence.models.llm_call_model import (
            CopilotLlmCallModel,
        )

        handler = _make_handler(db)
        run_id = uuid4()
        # T-1 (PI-12 S1, X2): cost is consumed from the LiteLLM CustomLogger
        # cache, NOT recomputed via calculate_cost. Pre-stash a value so the
        # synthetic call has a non-NULL cost on the audit row.
        _stash_cost("resp-001", 0.00725)
        # Synthetic on_chat_model_start payload — mirrors LangChain shape.
        handler.on_chat_model_start(
            serialized={"id": ["langchain", "chat_models", "openai", "ChatOpenAI"]},
            messages=[[]],
            run_id=run_id,
            metadata={"ls_provider": "openai", "ls_model_name": "openai/gpt-4o"},
        )
        response = LLMResult(
            generations=[[ChatGeneration(message=_ai_message_with_usage(litellm_call_id="resp-001"))]],
            llm_output=None,
        )
        handler.on_llm_end(response, run_id=run_id)
        db.flush()

        rows = db.query(CopilotLlmCallModel).filter_by(tenant_id=handler.tenant_id).all()
        assert len(rows) == 1
        row = rows[0]
        assert row.input_tokens == 1000
        assert row.output_tokens == 500
        assert row.cached_read_tokens == 200
        assert row.model_responded == "gpt-4o-2024-11-20"
        # Cost consumed from LiteLLM CustomLogger cache (kwargs["response_cost"]),
        # not recomputed locally — same value as legacy calculate_cost would have
        # produced for this fixture (0.00725).
        assert row.cost_usd == Decimal("0.0072500000")
        assert row.status == "ok"

    def test_end_without_start_is_noop(self, db) -> None:
        from luana_core_copilot.observability.persistence.models.llm_call_model import (
            CopilotLlmCallModel,
        )

        handler = _make_handler(db)
        response = LLMResult(
            generations=[[ChatGeneration(message=_ai_message_with_usage())]],
        )
        # No matching on_chat_model_start.
        handler.on_llm_end(response, run_id=uuid4())
        db.flush()
        assert db.query(CopilotLlmCallModel).count() == 0

    def test_chat_model_error_writes_error_row(self, db) -> None:
        from luana_core_copilot.observability.persistence.models.llm_call_model import (
            CopilotLlmCallModel,
        )

        handler = _make_handler(db)
        run_id = uuid4()
        handler.on_chat_model_start(
            serialized={},
            messages=[[]],
            run_id=run_id,
            metadata={"ls_provider": "openai", "ls_model_name": "gpt-4o"},
        )
        handler.on_llm_error(error=RuntimeError("rate limited"), run_id=run_id)
        db.flush()

        rows = db.query(CopilotLlmCallModel).filter_by(tenant_id=handler.tenant_id).all()
        assert len(rows) == 1
        assert rows[0].status == "error"
        assert rows[0].error_type == "RuntimeError"


class TestToolLifecycle:
    def test_tool_start_then_end_persists_trace_event(self, db) -> None:
        from luana_core_copilot.infrastructure.models.trace_event_model import (
            CopilotTraceEventModel,
        )

        handler = _make_handler(db)
        run_id = uuid4()
        handler.on_tool_start(
            serialized={"name": "search_brand"},
            input_str="{'q': 'laptop'}",
            run_id=run_id,
        )
        handler.on_tool_end(output="ok", run_id=run_id)
        db.flush()

        rows = db.query(CopilotTraceEventModel).filter_by(tenant_id=handler.tenant_id, event_type="tool_call").all()
        assert len(rows) == 1
        assert rows[0].name == "search_brand"
        assert rows[0].duration_ms is not None
        assert rows[0].status == "ok"

    def test_tool_error_writes_error_row(self, db) -> None:
        from luana_core_copilot.infrastructure.models.trace_event_model import (
            CopilotTraceEventModel,
        )

        handler = _make_handler(db)
        run_id = uuid4()
        handler.on_tool_start(
            serialized={"name": "search_brand"},
            input_str="{'q': 'laptop'}",
            run_id=run_id,
        )
        handler.on_tool_error(error=ValueError("bad arg"), run_id=run_id)
        db.flush()

        rows = db.query(CopilotTraceEventModel).filter_by(tenant_id=handler.tenant_id, event_type="tool_call").all()
        assert len(rows) == 1
        assert rows[0].status == "error"


class TestBestEffort:
    def test_db_failure_does_not_propagate(self, db) -> None:
        """Handler must swallow exceptions so a write failure cannot break a turn."""
        from luana_core_copilot.observability.recording.callback_handler import (
            ObservabilityCallbackHandler,
        )

        broken_repo = MagicMock()
        broken_repo.add.side_effect = RuntimeError("DB down")

        handler = ObservabilityCallbackHandler(
            tenant_id=uuid4(),
            conversation_id=uuid4(),
            user_id=uuid4(),
            turn_id=uuid4(),
            llm_call_repo=broken_repo,
            trace_repo=broken_repo,
            pricing_resolver=MagicMock(),
            fx_resolver=MagicMock(),
            tenant_currency="USD",
            role="agent",
        )
        handler.pricing_resolver.resolve.return_value = MagicMock(
            snapshot=_pricing_snapshot(),
            is_estimated=False,
        )
        handler.fx_resolver.resolve.return_value = (Decimal(1), "passthrough")

        run_id = uuid4()
        handler.on_chat_model_start(
            serialized={},
            messages=[[]],
            run_id=run_id,
            metadata={"ls_provider": "openai", "ls_model_name": "gpt-4o"},
        )
        # Must not raise, even though add() blows up.
        handler.on_llm_end(
            LLMResult(generations=[[ChatGeneration(message=_ai_message_with_usage())]]),
            run_id=run_id,
        )
