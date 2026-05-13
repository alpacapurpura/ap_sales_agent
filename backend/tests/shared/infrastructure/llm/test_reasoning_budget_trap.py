"""Reasoning-budget exhaustion trap — provider-agnostic detection.

Background
----------

Reasoning models (OpenAI o-series, DeepSeek-V4 reasoning, Anthropic
extended thinking, Gemini thinking) consume the *same* total budget for
both internal chain-of-thought (``reasoning_content`` / ``reasoning``
tokens) and the visible answer (``content``). When ``max_tokens`` is
sized for the visible answer alone, the model spends the full budget on
reasoning and emits empty ``content`` with ``finish_reason="length"`` —
a silent failure mode reported across every major provider in 2025-2026.

Industry consensus (OpenAI Help Center, OpenRouter, LiteLLM, tokenmix
research, Anthropic adaptive thinking docs) converges on the same
mitigation:

* Reserve a per-spec ``reasoning_token_reserve`` added to the requested
  visible budget *before* the wire translation.
* Detect the trap explicitly: empty ``content`` + ``finish_reason ==
  "length"``. Fail loud rather than silently retry with a bumped cap —
  the bumped cap retry just hides the policy bug.
* Use a non-reasoning role for tasks that don't need CoT (structured
  JSON extraction, classification, short summarisation).

This file owns the *detection* contract. Reserve injection lives in
``test_kwargs_normalization.py`` (provider-agnostic translation table).
The two together prove the trap cannot reopen for any current or future
provider without breaking a fitness test.

Conv that triggered the original incident:
``1ec7e82d-e6ac-4875-8f62-7de74c682e9b`` (2026-04-27, tenant Visionarias).
DeepSeek-V4 reasoning model, ``max_tokens=800``, 800 reasoning tokens
consumed, content empty, document extraction returned the recovery card.
"""

from __future__ import annotations

from typing import Any

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage

from luana_core_llm.providers._response_validation import (
    ReasoningBudgetExhaustedError,
    detect_reasoning_budget_exhaustion,
)


def _build_response(
    *,
    content: str,
    finish_reason: str | None = None,
    reasoning_tokens: int = 0,
) -> AIMessage:
    """Return an ``AIMessage`` shaped like LangChain's BaseChatOpenAI output.

    LangChain mirrors OpenAI's ``usage.completion_tokens_details.reasoning_tokens``
    onto ``response.response_metadata['token_usage']['completion_tokens_details']['reasoning_tokens']``
    and onto ``response.usage_metadata['output_token_details']['reasoning']``.
    The detector reads the second path because it is provider-normalised
    by LangChain across DeepSeek / OpenAI / Anthropic adapters.
    """
    return AIMessage(
        content=content,
        response_metadata={"finish_reason": finish_reason} if finish_reason else {},
        usage_metadata={
            "input_tokens": 0,
            "output_tokens": reasoning_tokens,
            "total_tokens": reasoning_tokens,
            "output_token_details": {"reasoning": reasoning_tokens},
        }
        if reasoning_tokens
        else None,
    )


class _StubChatModel(BaseChatModel):
    """Stub returning a pre-built ``AIMessage`` so we can exercise the
    detector against synthetic provider replies without any network."""

    pre_built: AIMessage = AIMessage(content="")

    @property
    def _llm_type(self) -> str:
        return "stub"

    def _generate(self, *args: Any, **kwargs: Any) -> Any:
        from langchain_core.outputs import ChatGeneration, ChatResult

        return ChatResult(generations=[ChatGeneration(message=type(self).pre_built)])


# ── Detection contract ──────────────────────────────────────────────


class TestReasoningBudgetTrapDetection:
    """The detector returns silently for healthy responses and raises
    :class:`ReasoningBudgetExhaustedError` for the trap signature."""

    def test_healthy_response_is_noop(self) -> None:
        """Non-empty content → never raise."""
        msg = _build_response(content='{"ok": true}', finish_reason="stop")
        # No raise, no return value to assert — pass-through behaviour.
        detect_reasoning_budget_exhaustion(msg, model_name="stub")

    def test_empty_content_with_natural_stop_is_noop(self) -> None:
        """Empty content can be legitimate (e.g. tool-call only assistant
        message). Detector must NOT trigger when ``finish_reason`` is not
        ``length`` — that signal is reserved for budget exhaustion."""
        msg = _build_response(content="", finish_reason="stop")
        detect_reasoning_budget_exhaustion(msg, model_name="stub")

    def test_empty_content_plus_length_plus_reasoning_raises(self) -> None:
        """The trap signature: zero visible output, ``finish_reason=length``,
        reasoning tokens consumed. Must raise the typed error so callers
        can react (or tests can assert)."""
        msg = _build_response(
            content="",
            finish_reason="length",
            reasoning_tokens=800,
        )
        with pytest.raises(ReasoningBudgetExhaustedError) as excinfo:
            detect_reasoning_budget_exhaustion(msg, model_name="deepseek-v4-flash")
        assert "deepseek-v4-flash" in str(excinfo.value)
        assert "800" in str(excinfo.value)

    def test_whitespace_only_content_treated_as_empty(self) -> None:
        """``\\n\\n   `` is empty in practice — providers occasionally
        emit padding whitespace before truncation. Detector must strip."""
        msg = _build_response(
            content="   \n\n  ",
            finish_reason="length",
            reasoning_tokens=420,
        )
        with pytest.raises(ReasoningBudgetExhaustedError):
            detect_reasoning_budget_exhaustion(msg, model_name="stub")

    def test_length_finish_with_partial_content_is_noop(self) -> None:
        """If the model managed *some* visible tokens before truncation we
        let the caller decide whether to retry with more budget. The trap
        detector targets the *zero* visible-output silent-failure case
        only — partial truncation surfaces normally to the caller."""
        msg = _build_response(
            content='{"partial":',
            finish_reason="length",
            reasoning_tokens=500,
        )
        detect_reasoning_budget_exhaustion(msg, model_name="stub")

    def test_reasoning_tokens_zero_with_empty_content_does_not_raise(self) -> None:
        """If the model claims zero reasoning tokens, the trap is not the
        cause — raising would hide the real failure (e.g. content filter,
        provider 400). Detector stays inert."""
        msg = _build_response(
            content="",
            finish_reason="length",
            reasoning_tokens=0,
        )
        detect_reasoning_budget_exhaustion(msg, model_name="stub")

    def test_error_carries_actionable_diagnostics(self) -> None:
        """Error message must include the model name and the reasoning
        token count so the operator can pick the right policy lever
        (bump ``max_output_tokens`` or pick a non-reasoning role)."""
        msg = _build_response(
            content="",
            finish_reason="length",
            reasoning_tokens=1234,
        )
        with pytest.raises(ReasoningBudgetExhaustedError) as excinfo:
            detect_reasoning_budget_exhaustion(msg, model_name="o4-mini")
        text = str(excinfo.value)
        assert "o4-mini" in text
        assert "1234" in text
        assert "max_output_tokens" in text or "non-reasoning" in text


# ── Reserve injection contract (lives in normalizer) ────────────────


class TestReasoningReserveInjection:
    """When the active spec declares ``is_reasoning_model=True`` the
    normalizer must transparently inflate the visible budget by
    ``reasoning_token_reserve`` before translating to the wire param.

    Callers continue to think in terms of *visible* tokens; the framework
    accounts for thinking overhead. This is the layer that prevents the
    trap from reopening for any future reasoning-capable provider.
    """

    def test_non_reasoning_spec_unchanged(self) -> None:
        from langchain_openai import ChatOpenAI

        from luana_core_llm.providers._chat_model_resolver import (
            ChatModelSpec,
            build_chat_openai,
        )
        from luana_core_llm.providers._kwargs import (
            normalize_openai_protocol_kwargs,
        )

        spec = ChatModelSpec(
            chat_class=ChatOpenAI,
            builder=build_chat_openai,
            is_reasoning_model=False,
            reasoning_token_reserve=0,
        )
        kwargs = {"max_output_tokens": 800, "temperature": 0.7}
        normalize_openai_protocol_kwargs(kwargs, spec=spec)
        assert kwargs == {"max_tokens": 800, "temperature": 0.7}

    def test_reasoning_spec_adds_reserve(self) -> None:
        from langchain_openai import ChatOpenAI

        from luana_core_llm.providers._chat_model_resolver import (
            ChatModelSpec,
            build_chat_openai,
        )
        from luana_core_llm.providers._kwargs import (
            normalize_openai_protocol_kwargs,
        )

        spec = ChatModelSpec(
            chat_class=ChatOpenAI,
            builder=build_chat_openai,
            is_reasoning_model=True,
            reasoning_token_reserve=4000,
        )
        kwargs = {"max_output_tokens": 800}
        normalize_openai_protocol_kwargs(kwargs, spec=spec)
        # Visible 800 + reserve 4000 = 4800 total wire budget.
        assert kwargs == {"max_tokens": 4800}

    def test_explicit_max_tokens_still_wins(self) -> None:
        """Caller override is authoritative even on reasoning specs —
        operators escape-hatch when they have measured the right cap."""
        from langchain_openai import ChatOpenAI

        from luana_core_llm.providers._chat_model_resolver import (
            ChatModelSpec,
            build_chat_openai,
        )
        from luana_core_llm.providers._kwargs import (
            normalize_openai_protocol_kwargs,
        )

        spec = ChatModelSpec(
            chat_class=ChatOpenAI,
            builder=build_chat_openai,
            is_reasoning_model=True,
            reasoning_token_reserve=4000,
        )
        kwargs = {"max_tokens": 12000, "max_output_tokens": 800}
        normalize_openai_protocol_kwargs(kwargs, spec=spec)
        assert kwargs == {"max_tokens": 12000}

    def test_reasoning_effort_routed_to_native_param(self) -> None:
        """When the spec declares a native effort param (e.g. OpenAI
        o-series ``reasoning_effort``), the normalizer routes the
        canonical key to the wire-name without breaking providers that
        do not surface the concept (e.g. DeepSeek today)."""
        from langchain_openai import ChatOpenAI

        from luana_core_llm.providers._chat_model_resolver import (
            ChatModelSpec,
            build_chat_openai,
        )
        from luana_core_llm.providers._kwargs import (
            normalize_openai_protocol_kwargs,
        )

        spec = ChatModelSpec(
            chat_class=ChatOpenAI,
            builder=build_chat_openai,
            is_reasoning_model=True,
            reasoning_token_reserve=4000,
            reasoning_effort_param="reasoning_effort",
        )
        kwargs = {"reasoning_effort": "low", "max_output_tokens": 800}
        normalize_openai_protocol_kwargs(kwargs, spec=spec)
        assert kwargs == {"max_tokens": 4800, "reasoning_effort": "low"}

    def test_reasoning_effort_dropped_when_param_undeclared(self) -> None:
        """Specs that don't surface effort (DeepSeek-V4 implicit) drop the
        canonical key silently — passing ``reasoning_effort`` to a
        provider that doesn't accept it would 400."""
        from langchain_openai import ChatOpenAI

        from luana_core_llm.providers._chat_model_resolver import (
            ChatModelSpec,
            build_chat_openai,
        )
        from luana_core_llm.providers._kwargs import (
            normalize_openai_protocol_kwargs,
        )

        spec = ChatModelSpec(
            chat_class=ChatOpenAI,
            builder=build_chat_openai,
            is_reasoning_model=True,
            reasoning_token_reserve=4000,
            reasoning_effort_param=None,
        )
        kwargs = {"reasoning_effort": "high", "max_output_tokens": 800}
        normalize_openai_protocol_kwargs(kwargs, spec=spec)
        assert kwargs == {"max_tokens": 4800}

    def test_idempotent_with_spec(self) -> None:
        from langchain_openai import ChatOpenAI

        from luana_core_llm.providers._chat_model_resolver import (
            ChatModelSpec,
            build_chat_openai,
        )
        from luana_core_llm.providers._kwargs import (
            normalize_openai_protocol_kwargs,
        )

        spec = ChatModelSpec(
            chat_class=ChatOpenAI,
            builder=build_chat_openai,
            is_reasoning_model=True,
            reasoning_token_reserve=4000,
        )
        kwargs = {"max_output_tokens": 800}
        normalize_openai_protocol_kwargs(kwargs, spec=spec)
        snapshot = dict(kwargs)
        normalize_openai_protocol_kwargs(kwargs, spec=spec)
        # Second pass is a no-op (max_output_tokens already consumed,
        # max_tokens already at 4800, no double-counting reserve).
        assert kwargs == snapshot
