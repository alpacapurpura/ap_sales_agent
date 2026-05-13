"""Kwarg normalization for OpenAI-protocol-compatible providers.

Both ``OpenAIService`` (real OpenAI) and ``OpenAICompatibleService``
subclasses (DeepSeek, Kimi, Qwen) end up routing through
``langchain_openai.ChatOpenAI`` (or the partner-package equivalent
``langchain_deepseek.ChatDeepSeek``) — the wire format is the OpenAI
Chat Completions endpoint. Nicolify's internal contract uses
``max_output_tokens`` (mirrors :class:`ResolvedModelPolicy`); the OpenAI
Chat Completions wire format speaks ``max_tokens``. Translating that
alias is provider-agnostic at the protocol level, so it lives here once
instead of being duplicated per service.

Reasoning-budget reserve
------------------------

Reasoning-capable specs (``is_reasoning_model=True``) consume the same
``max_tokens`` budget for *both* internal chain-of-thought and the
visible answer. Sized for the visible answer alone, the budget is
exhausted by reasoning before any content emits — the empty-content
trap reproduced across OpenAI o-series, DeepSeek R1/V4, Anthropic
extended thinking, Gemini 2.5/3.

The normalizer's job is to keep callers thinking in *visible* output
tokens — the framework adds the reserve on the wire. Adding a reasoning
provider is now: declare a spec with ``is_reasoning_model=True`` and a
sensible ``reasoning_token_reserve``. No call-site changes anywhere.

Why a separate module instead of a method on ``BaseLLMService``:
``BaseLLMService`` is meant to stay protocol-agnostic so future
providers (Gemini, native Anthropic) can extend it without inheriting
OpenAI-specific kwarg quirks. This module is only imported by the
OpenAI-protocol providers.

Known related issue (NOT handled here, deferred to ``docs/mejoras-
proceso/to-do.md``): ``langchain_openai.ChatOpenAI`` rewrites
``max_tokens`` to ``max_completion_tokens`` in the HTTP payload to match
OpenAI's Sept-2024 deprecation. Native partner packages
(``langchain_deepseek.ChatDeepSeek``) own their own translation. See
``langchain-ai/langchain#29283``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from luana_core_llm.providers._chat_model_resolver import (
        ChatModelSpec,
    )

__all__ = ["normalize_openai_protocol_kwargs"]


def normalize_openai_protocol_kwargs(
    kwargs: dict,
    *,
    spec: ChatModelSpec | None = None,
) -> dict:
    """Translate Nicolify-canonical kwargs to OpenAI Chat Completions wire names.

    Mutates ``kwargs`` in place AND returns it for fluent chaining.
    Idempotent — calling twice is a no-op.

    Translations applied in order:

    1. **Reasoning reserve.** When ``spec.is_reasoning_model`` is True
       and ``max_output_tokens`` is set, inflate the visible budget by
       ``spec.reasoning_token_reserve`` so internal CoT cannot starve
       the visible answer. Caller-set ``max_tokens`` always wins
       (escape hatch when the operator has measured the right cap).
    2. **``max_output_tokens`` → ``max_tokens``.** OpenAI Chat
       Completions wire param. ``setdefault`` so an explicit caller
       override is never silently overwritten by the alias.
    3. **``reasoning_effort`` routing.** When ``spec.reasoning_effort_param``
       is set, the canonical ``reasoning_effort`` value is moved to the
       declared wire-param name (e.g. OpenAI o-series accepts
       ``reasoning_effort`` directly). When the spec does not surface
       effort, the canonical key is dropped silently — passing it to a
       provider that doesn't accept it would 400.
    4. **``metadata``** is a Nicolify-internal logging key; popped so it
       never leaks into the OpenAI SDK call (which would 400).

    Anything else passes through untouched. Adding a new translation is
    a single line here + a parametrized test.
    """
    if "max_output_tokens" in kwargs and "max_tokens" not in kwargs:
        visible = kwargs.pop("max_output_tokens")
        if spec is not None and spec.is_reasoning_model:
            visible += spec.reasoning_token_reserve
        kwargs["max_tokens"] = visible
    elif "max_output_tokens" in kwargs:
        # Caller-set max_tokens already authoritative; drop the alias.
        kwargs.pop("max_output_tokens")

    if "reasoning_effort" in kwargs:
        effort = kwargs.pop("reasoning_effort")
        if spec is not None and spec.reasoning_effort_param:
            kwargs[spec.reasoning_effort_param] = effort

    kwargs.pop("metadata", None)
    return kwargs
