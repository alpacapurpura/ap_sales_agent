"""Kwarg normalization for OpenAI-protocol-compatible providers.

Both ``OpenAIService`` (real OpenAI) and ``OpenAICompatibleService``
subclasses (DeepSeek, Kimi, Qwen) end up routing through
``langchain_openai.ChatOpenAI`` — the wire format is the OpenAI Chat
Completions endpoint. Nicolify's internal contract uses
``max_output_tokens`` (mirrors :class:`ResolvedModelPolicy`); the OpenAI
Chat Completions wire format speaks ``max_tokens``. Translating that
alias is provider-agnostic at the protocol level, so it lives here once
instead of being duplicated per service.

Why a separate module instead of a method on ``BaseLLMService``:
``BaseLLMService`` is meant to stay protocol-agnostic so future
providers (Gemini, native Anthropic, …) can extend it without inheriting
OpenAI-specific kwarg quirks. This module is only imported by the
OpenAI-protocol providers.

Known related issue (NOT handled here, deferred to ``docs/mejoras-
proceso/to-do.md``): ``langchain_openai.ChatOpenAI`` rewrites
``max_tokens`` to ``max_completion_tokens`` in the HTTP payload to match
OpenAI's Sept-2024 deprecation. DeepSeek's wire protocol still expects
``max_tokens``, so the rewrite silently breaks token caps on DeepSeek
calls. Surface symptom: DeepSeek responses ignore the cap (not a
TypeError). See ``langchain-ai/langchain#29283``.
"""

from __future__ import annotations

__all__ = ["normalize_openai_protocol_kwargs"]


def normalize_openai_protocol_kwargs(kwargs: dict) -> dict:
    """Translate Nicolify-canonical kwargs to OpenAI Chat Completions wire names.

    Mutates ``kwargs`` in place AND returns it for fluent chaining.
    Idempotent — calling twice is a no-op.

    Translations:

    * ``max_output_tokens`` → ``max_tokens``. Caller-set ``max_tokens``
      wins (``setdefault``) so an explicit override is never silently
      overwritten by the alias.
    * ``metadata`` is a Nicolify-internal logging key; popped so it
      never leaks into the OpenAI SDK call (which would 400).

    Anything else passes through untouched. Adding a new translation is
    a single line here + a parametrized test.
    """
    if "max_output_tokens" in kwargs:
        translated = kwargs.pop("max_output_tokens")
        kwargs.setdefault("max_tokens", translated)
    kwargs.pop("metadata", None)
    return kwargs
