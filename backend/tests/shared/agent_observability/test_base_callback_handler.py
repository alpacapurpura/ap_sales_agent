"""Contract tests for :class:`BaseAgentCallbackHandler` shared.

Validates the Template Method skeleton lifted in S11A:

* Helpers (``_extract_usage`` / ``_from_openai_token_usage`` /
  ``_extract_provider_and_model`` / ``_extract_model_responded`` /
  ``_chain_name``) live on the base and are agent-agnostic.
* Abstract persisters (``_persist_llm_call_row`` / ``_persist_trace_event_row``)
  must be overridden — instantiating without them raises ``TypeError``.
* The base accepts a minimal subclass that only overrides the
  abstracts — no LangChain plumbing required from subclasses.

Once Sub-sprint A finishes the lift (commit 4), this file gains tests
for the 6 ``on_*`` callbacks living on the base.
"""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import pytest

from src.shared.agent_observability.recording.base_callback_handler import (
    BaseAgentCallbackHandler,
)

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID


# ── Helpers tests (pure functions on the base) ──────────────────────────


class TestExtractProviderAndModel:
    def test_metadata_ls_pair_wins(self) -> None:
        provider, model = BaseAgentCallbackHandler._extract_provider_and_model(
            {"kwargs": {"model_name": "ignored"}},
            {"ls_provider": "kimi", "ls_model_name": "kimi-k2.6"},
        )
        assert provider == "kimi"
        assert model == "kimi-k2.6"

    def test_metadata_legacy_keys(self) -> None:
        provider, model = BaseAgentCallbackHandler._extract_provider_and_model(
            {},
            {"provider": "deepseek", "model_name": "deepseek-v4"},
        )
        assert provider == "deepseek"
        assert model == "deepseek-v4"

    def test_falls_back_to_serialized_kwargs(self) -> None:
        provider, model = BaseAgentCallbackHandler._extract_provider_and_model(
            {"kwargs": {"model_name": "qwen-3-coder"}},
            {},
        )
        assert provider == "unknown"
        assert model == "qwen-3-coder"

    def test_unknown_when_nothing_set(self) -> None:
        provider, model = BaseAgentCallbackHandler._extract_provider_and_model({}, None)
        assert provider == "unknown"
        assert model == "unknown"


class TestExtractUsage:
    def test_returns_zeros_for_none_response(self) -> None:
        usage = BaseAgentCallbackHandler._extract_usage(None)
        assert usage["input_tokens"] == 0
        assert usage["output_tokens"] == 0

    def test_reads_langchain_usage_metadata(self) -> None:
        response = _build_response(
            usage_metadata={
                "input_tokens": 100,
                "output_tokens": 50,
                "input_token_details": {"cache_read": 80, "cache_creation": 5},
                "output_token_details": {"reasoning": 30},
            },
        )
        usage = BaseAgentCallbackHandler._extract_usage(response)
        assert usage == {
            "input_tokens": 100,
            "output_tokens": 50,
            "cached_read_tokens": 80,
            "cached_write_tokens": 5,
            "reasoning_tokens": 30,
        }

    def test_falls_back_to_response_metadata_token_usage(self) -> None:
        response = _build_response(
            usage_metadata={},
            response_metadata={
                "token_usage": {
                    "prompt_tokens": 200,
                    "completion_tokens": 80,
                    "prompt_tokens_details": {
                        "cached_tokens": 150,
                        "cache_creation_tokens": 0,
                    },
                    "completion_tokens_details": {"reasoning_tokens": 40},
                },
            },
        )
        usage = BaseAgentCallbackHandler._extract_usage(response)
        assert usage["input_tokens"] == 200
        assert usage["output_tokens"] == 80
        assert usage["cached_read_tokens"] == 150
        assert usage["reasoning_tokens"] == 40

    def test_falls_back_to_llm_output_aggregate(self) -> None:
        response = _build_response(
            usage_metadata={},
            llm_output_token_usage={
                "prompt_tokens": 10,
                "completion_tokens": 5,
            },
        )
        usage = BaseAgentCallbackHandler._extract_usage(response)
        assert usage["input_tokens"] == 10
        assert usage["output_tokens"] == 5


class TestExtractModelResponded:
    def test_uses_response_metadata_when_present(self) -> None:
        response = _build_response(
            usage_metadata={},
            response_metadata={"model_name": "kimi-k2.6"},
        )
        assert BaseAgentCallbackHandler._extract_model_responded(response, fallback="x") == "kimi-k2.6"

    def test_falls_back_when_response_is_none(self) -> None:
        assert BaseAgentCallbackHandler._extract_model_responded(None, fallback="kimi") == "kimi"


class TestChainName:
    def test_returns_name_when_present(self) -> None:
        assert BaseAgentCallbackHandler._chain_name({"name": "qualifier"}) == "qualifier"

    def test_returns_none_for_unnamed_chain(self) -> None:
        assert BaseAgentCallbackHandler._chain_name({}) is None

    def test_returns_none_for_non_dict(self) -> None:
        assert BaseAgentCallbackHandler._chain_name("not_a_dict") is None  # type: ignore[arg-type]


# ── Subclass contract ───────────────────────────────────────────────────


class _MinimalHandler(BaseAgentCallbackHandler):
    """Smallest viable subclass — only overrides the abstracts."""

    def __init__(self) -> None:
        self.llm_calls: list[dict[str, Any]] = []
        self.trace_events: list[dict[str, Any]] = []

    def _persist_llm_call_row(self, **kwargs: Any) -> None:
        self.llm_calls.append(kwargs)

    def _persist_trace_event_row(self, **kwargs: Any) -> None:
        self.trace_events.append(kwargs)


class TestSubclassContract:
    def test_base_cannot_be_instantiated_directly(self) -> None:
        with pytest.raises(TypeError, match="abstract"):
            BaseAgentCallbackHandler()  # type: ignore[abstract]

    def test_minimal_subclass_instantiates(self) -> None:
        handler = _MinimalHandler()
        assert isinstance(handler, BaseAgentCallbackHandler)

    def test_persisters_capture_kwargs(self) -> None:
        handler = _MinimalHandler()
        from datetime import UTC, datetime
        from uuid import uuid4

        ts = datetime(2026, 4, 28, 12, 0, 0, tzinfo=UTC)
        tenant = uuid4()
        turn = uuid4()
        span = uuid4()
        version = uuid4()

        handler._persist_llm_call_row(
            tenant_id=tenant,
            turn_id=turn,
            span_id=span,
            provider="kimi",
            model_requested="kimi-k2.6",
            model_responded="kimi-k2.6",
            input_tokens=100,
            output_tokens=50,
            cached_read_tokens=80,
            cached_write_tokens=0,
            reasoning_tokens=0,
            pricing_version_id=version,
            input_unit_cost_usd=Decimal("0.000001"),
            output_unit_cost_usd=Decimal("0.000005"),
            cached_read_unit_cost_usd=Decimal("0.0000005"),
            cost_usd=Decimal("0.000310"),
            tenant_currency="USD",
            fx_rate_to_tenant=Decimal("1.0"),
            fx_rate_source="stub",
            cost_tenant_currency=Decimal("0.000310"),
            started_at=ts,
            duration_ms=24,
            status="ok",
            error_type=None,
            role="agent",
            extra_kwarg="agent_specific",
        )
        assert len(handler.llm_calls) == 1
        assert handler.llm_calls[0]["extra_kwarg"] == "agent_specific"

        handler._persist_trace_event_row(
            tenant_id=tenant,
            turn_id=turn,
            span_id=span,
            event_type="llm_call",
            name="kimi.kimi-k2.6",
            data={"input_tokens": 100},
            duration_ms=24,
            status="ok",
        )
        assert len(handler.trace_events) == 1


# ── Helpers ─────────────────────────────────────────────────────────────


def _build_response(
    *,
    usage_metadata: dict[str, Any],
    response_metadata: dict[str, Any] | None = None,
    llm_output_token_usage: dict[str, Any] | None = None,
) -> Any:
    """Build a SimpleNamespace mimicking ``LLMResult`` for unit tests."""
    message = SimpleNamespace(
        usage_metadata=usage_metadata,
        response_metadata=response_metadata or {},
    )
    generation = SimpleNamespace(message=message)
    llm_output: dict[str, Any] | None = None
    if llm_output_token_usage is not None:
        llm_output = {"token_usage": llm_output_token_usage}
    return SimpleNamespace(generations=[[generation]], llm_output=llm_output)
