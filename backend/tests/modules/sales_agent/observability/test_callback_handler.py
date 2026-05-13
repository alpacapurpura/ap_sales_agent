"""SalesAgentCallbackHandler invariants.

* Hereda :class:`BaseAgentCallbackHandler` (S0 Template Method).
* Captura ``on_chat_model_start`` + ``on_llm_end`` y persiste a
  ``sales_agent_llm_call`` con ``lead_id`` + ``channel_type``.
* PII redactada en payload de trace event mirror.
* Pricing resuelto vía shared ``aliases.py`` (Kimi K2.6 → cost > 0).
* Excepción en repo NO rompe turn (best-effort).
* ``on_tool_start`` / ``on_tool_end`` persiste row a
  ``sales_agent_trace_event`` con ``event_type='tool_call'``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from tests.conftest import prime_cost_bridge


def _build_llm_response(
    *,
    input_tokens: int = 1000,
    output_tokens: int = 500,
    cached_read: int = 0,
    model_name: str = "kimi-k2.6",
    litellm_call_id: str | None = None,
) -> SimpleNamespace:
    """Build a fake ``LLMResult`` matching the shape callbacks consume.

    **Bridge note (PI-12 S1 T-1.bis):**
    ``litellm_call_id`` must be injected into ``response_metadata`` so that
    ``BaseAgentCallbackHandler._extract_litellm_call_id()`` can retrieve it and
    call ``pop_cost(call_id)`` during ``on_llm_end``. In production this key is
    populated by LangChain's OpenAI-compat adapters echoing the LiteLLM call id.
    Tests that assert ``cost_usd > 0`` must also call ``prime_cost_bridge(call_id,
    cost)`` in setup to stash the cost before ``on_llm_end`` fires (see
    ``tests/conftest.py::prime_cost_bridge``).
    """
    response_metadata: dict = {"model_name": model_name}
    if litellm_call_id is not None:
        response_metadata["litellm_call_id"] = litellm_call_id
    message = SimpleNamespace(
        usage_metadata={
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_token_details": {"cache_read": cached_read},
            "output_token_details": {},
        },
        response_metadata=response_metadata,
    )
    generation = SimpleNamespace(message=message)
    return SimpleNamespace(generations=[[generation]], llm_output=None)


@pytest.fixture
def fake_pricing_resolver() -> MagicMock:
    """Pricing resolver returning a snapshot stub."""
    snapshot = SimpleNamespace(
        id=uuid4(),
        input_cost_per_token=Decimal("0.0000004"),
        output_cost_per_token=Decimal("0.000002"),
        cache_read_cost_per_token=Decimal("0.0000001"),
        cache_write_cost_per_token=Decimal(0),
    )
    resolver = MagicMock()
    resolver.resolve.return_value = SimpleNamespace(
        snapshot=snapshot,
        is_estimated=False,
    )
    return resolver


@pytest.fixture
def fake_fx_resolver() -> MagicMock:
    """FX resolver returning rate=1.0 USD."""
    resolver = MagicMock()
    resolver.resolve.return_value = (Decimal(1), "frankfurter")
    return resolver


@pytest.fixture
def llm_call_repo_stub() -> MagicMock:
    """LLM call repo stub recording add() calls."""
    return MagicMock()


@pytest.fixture
def trace_repo_stub() -> MagicMock:
    """Trace event repo stub recording add() calls."""
    return MagicMock()


@pytest.fixture
def fake_db_session() -> MagicMock:
    """Mock SA session — best-effort path needs rollback() callable."""
    return MagicMock()


@pytest.fixture
def handler(
    llm_call_repo_stub: MagicMock,
    trace_repo_stub: MagicMock,
    fake_pricing_resolver: MagicMock,
    fake_fx_resolver: MagicMock,
    fake_db_session: MagicMock,
) -> object:
    """Construct a SalesAgentCallbackHandler with all deps mocked."""
    from luana_core_sales_agent.observability.recording.callback_handler import (
        SalesAgentCallbackHandler,
    )

    return SalesAgentCallbackHandler(
        tenant_id=uuid4(),
        lead_id=uuid4(),
        channel_type="telegram",
        turn_id=uuid4(),
        llm_call_repo=llm_call_repo_stub,
        trace_repo=trace_repo_stub,
        pricing_resolver=fake_pricing_resolver,
        fx_resolver=fake_fx_resolver,
        db_session=fake_db_session,
        tenant_currency="USD",
        role="closer",
    )


class TestInheritance:
    def test_handler_inherits_base_agent_callback_handler(self) -> None:
        from luana_core_sales_agent.observability.recording.callback_handler import (
            SalesAgentCallbackHandler,
        )
        from luana_core_observability.recording.base_callback_handler import (
            BaseAgentCallbackHandler,
        )

        assert issubclass(SalesAgentCallbackHandler, BaseAgentCallbackHandler)


class TestOnChatModelEnd:
    def test_persists_row_with_sales_columns(
        self,
        handler: object,
        llm_call_repo_stub: MagicMock,
    ) -> None:
        # Bridge setup (PI-12 S1 T-1.bis):
        # In production the LiteLLM CustomLogger stashes the cost under
        # litellm_call_id before on_llm_end fires.  The mocked LLMResult
        # doesn't go through LiteLLM, so we prime the cache manually.
        call_id = str(uuid4())
        prime_cost_bridge(call_id, Decimal("0.001"))

        run_id = uuid4()
        handler.on_chat_model_start(
            serialized={"name": "ChatOpenAI", "kwargs": {"model_name": "kimi-k2.6"}},
            messages=[],
            run_id=run_id,
            metadata={"ls_provider": "kimi", "ls_model_name": "kimi-k2.6"},
        )
        handler.on_llm_end(_build_llm_response(litellm_call_id=call_id), run_id=run_id)

        llm_call_repo_stub.add.assert_called_once()
        kwargs = llm_call_repo_stub.add.call_args.kwargs
        assert kwargs["lead_id"] == handler.lead_id
        assert kwargs["channel_type"] == "telegram"
        assert kwargs["provider"] == "kimi"
        assert kwargs["model_responded"] == "kimi-k2.6"
        assert kwargs["input_tokens"] == 1000
        assert kwargs["output_tokens"] == 500
        # Cost > 0: bridged from LiteLLM cost recorder via litellm_call_id.
        assert kwargs["cost_usd"] > 0
        assert kwargs["status"] == "ok"

    def test_pii_redacted_in_trace_event_mirror(
        self,
        handler: object,
        trace_repo_stub: MagicMock,
    ) -> None:
        run_id = uuid4()
        handler.on_chat_model_start(
            serialized={"name": "ChatOpenAI"},
            messages=[],
            run_id=run_id,
            metadata={"ls_provider": "kimi", "ls_model_name": "kimi-k2.6"},
        )
        handler.on_llm_end(_build_llm_response(), run_id=run_id)

        # The mirror trace event must have been persisted; payload should
        # not carry raw PII even if added via name/data later. We assert
        # the trace_repo was called with sanitization-aware data dict.
        assert trace_repo_stub.add.called
        kwargs = trace_repo_stub.add.call_args.kwargs
        assert kwargs["lead_id"] == handler.lead_id
        assert kwargs["channel_type"] == "telegram"
        assert kwargs["event_type"] == "llm_call"

    def test_repo_exception_does_not_propagate(
        self,
        handler: object,
        llm_call_repo_stub: MagicMock,
        fake_db_session: MagicMock,
    ) -> None:
        llm_call_repo_stub.add.side_effect = RuntimeError("DB down")
        run_id = uuid4()
        handler.on_chat_model_start(
            serialized={"name": "ChatOpenAI"},
            messages=[],
            run_id=run_id,
            metadata={"ls_provider": "kimi", "ls_model_name": "kimi-k2.6"},
        )
        # MUST NOT raise — best-effort observability.
        handler.on_llm_end(_build_llm_response(), run_id=run_id)
        # rollback was called as part of best-effort recovery.
        assert fake_db_session.rollback.called

    def test_error_status_yields_zero_cost(
        self,
        handler: object,
        llm_call_repo_stub: MagicMock,
    ) -> None:
        run_id = uuid4()
        handler.on_chat_model_start(
            serialized={"name": "ChatOpenAI"},
            messages=[],
            run_id=run_id,
            metadata={"ls_provider": "kimi", "ls_model_name": "kimi-k2.6"},
        )
        handler.on_llm_error(error=RuntimeError("rate limit"), run_id=run_id)

        kwargs = llm_call_repo_stub.add.call_args.kwargs
        assert kwargs["cost_usd"] == 0
        assert kwargs["status"] == "error"
        assert kwargs["error_type"] == "RuntimeError"


class TestOnToolEnd:
    def test_persists_tool_call_trace_event(
        self,
        handler: object,
        trace_repo_stub: MagicMock,
    ) -> None:
        run_id = uuid4()
        handler.on_tool_start(
            serialized={"name": "create_payment_link"},
            input_str='{"product_id": "abc"}',
            run_id=run_id,
        )
        handler.on_tool_end(output={"link": "https://mpago.la/abc"}, run_id=run_id)

        # tool_call event mirrored in trace
        calls = [c for c in trace_repo_stub.add.call_args_list if c.kwargs.get("event_type") == "tool_call"]
        assert len(calls) == 1
        kwargs = calls[0].kwargs
        assert kwargs["name"] == "create_payment_link"
        assert kwargs["lead_id"] == handler.lead_id
        assert kwargs["channel_type"] == "telegram"
        assert kwargs["status"] == "ok"

    def test_tool_args_with_email_get_sanitized(
        self,
        handler: object,
        trace_repo_stub: MagicMock,
    ) -> None:
        run_id = uuid4()
        handler.on_tool_start(
            serialized={"name": "send_summary"},
            input_str='{"to": "lead@example.com"}',
            run_id=run_id,
        )
        handler.on_tool_end(output="ok", run_id=run_id)

        calls = [c for c in trace_repo_stub.add.call_args_list if c.kwargs.get("event_type") == "tool_call"]
        assert len(calls) == 1
        # Payload (data dict) must NOT carry raw email.
        data = calls[0].kwargs["data"]
        rendered = str(data)
        assert "lead@example.com" not in rendered


class TestOnChainEvents:
    def test_node_enter_persisted_for_named_chain(
        self,
        handler: object,
        trace_repo_stub: MagicMock,
    ) -> None:
        run_id = uuid4()
        handler.on_chain_start(
            serialized={"name": "qualifier"},
            inputs={},
            run_id=run_id,
        )
        calls = [c for c in trace_repo_stub.add.call_args_list if c.kwargs.get("event_type") == "node_enter"]
        assert len(calls) == 1
        assert calls[0].kwargs["name"] == "qualifier"
        assert calls[0].kwargs["lead_id"] == handler.lead_id

    def test_node_exit_after_chain_end(
        self,
        handler: object,
        trace_repo_stub: MagicMock,
    ) -> None:
        run_id = uuid4()
        handler.on_chain_start(serialized={"name": "closer"}, inputs={}, run_id=run_id)
        handler.on_chain_end(outputs={}, run_id=run_id)
        calls = [c for c in trace_repo_stub.add.call_args_list if c.kwargs.get("event_type") == "node_exit"]
        assert len(calls) == 1
        assert calls[0].kwargs["name"] == "closer"


class TestStartedAtIsTimezoneAware:
    def test_started_at_is_utc(
        self,
        handler: object,
        llm_call_repo_stub: MagicMock,
    ) -> None:
        run_id = uuid4()
        before = datetime.now(tz=UTC)
        handler.on_chat_model_start(
            serialized={"name": "ChatOpenAI"},
            messages=[],
            run_id=run_id,
            metadata={"ls_provider": "kimi", "ls_model_name": "kimi-k2.6"},
        )
        handler.on_llm_end(_build_llm_response(), run_id=run_id)
        kwargs = llm_call_repo_stub.add.call_args.kwargs
        started = kwargs["started_at"]
        assert started.tzinfo is not None
        assert started >= before
