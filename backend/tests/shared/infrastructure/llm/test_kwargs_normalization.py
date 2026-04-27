"""Unit tests for ``providers/_kwargs.py``.

The helper is the single source of truth for OpenAI-protocol kwarg
translation. Both ``OpenAIService`` and the ``OpenAICompatibleService``
hierarchy (DeepSeek / Kimi / Qwen) call it. Keeping the rules covered
here means future translations land with one test, not three.
"""

from __future__ import annotations

from src.shared.infrastructure.llm.providers._kwargs import (
    normalize_openai_protocol_kwargs,
)


class TestNormalizeOpenAIProtocolKwargs:
    def test_max_output_tokens_translated(self) -> None:
        kwargs = {"max_output_tokens": 512, "temperature": 0.7}
        normalize_openai_protocol_kwargs(kwargs)
        assert kwargs == {"max_tokens": 512, "temperature": 0.7}

    def test_explicit_max_tokens_wins(self) -> None:
        """Explicit ``max_tokens`` set by the caller is authoritative —
        the alias must never silently overwrite it."""
        kwargs = {"max_tokens": 2048, "max_output_tokens": 512}
        normalize_openai_protocol_kwargs(kwargs)
        assert kwargs == {"max_tokens": 2048}

    def test_metadata_dropped(self) -> None:
        """``metadata`` is a Nicolify-internal logging field; the OpenAI
        SDK rejects it. Helper must strip it."""
        kwargs = {"metadata": {"trace_id": "x"}, "temperature": 0.5}
        normalize_openai_protocol_kwargs(kwargs)
        assert kwargs == {"temperature": 0.5}

    def test_idempotent(self) -> None:
        """Running the helper twice on the same dict must be a no-op
        the second time — no key resurrection, no value mutation."""
        kwargs = {"max_output_tokens": 256}
        normalize_openai_protocol_kwargs(kwargs)
        snapshot = dict(kwargs)
        normalize_openai_protocol_kwargs(kwargs)
        assert kwargs == snapshot

    def test_unknown_keys_pass_through(self) -> None:
        """Anything not in the translation table must pass through
        untouched. Exotic provider params (e.g. Kimi's ``extra_body``)
        rely on this behaviour."""
        kwargs = {
            "temperature": 0.7,
            "top_p": 0.95,
            "extra_body": {"thinking": {"type": "disabled"}},
            "stop": ["\n\n"],
        }
        before = dict(kwargs)
        normalize_openai_protocol_kwargs(kwargs)
        assert kwargs == before

    def test_returns_same_dict_for_chaining(self) -> None:
        """The helper returns the mutated dict so call sites can chain
        if they prefer expression-style code over statement-style."""
        kwargs = {"max_output_tokens": 100}
        result = normalize_openai_protocol_kwargs(kwargs)
        assert result is kwargs

    def test_empty_dict_is_noop(self) -> None:
        kwargs: dict = {}
        normalize_openai_protocol_kwargs(kwargs)
        assert kwargs == {}
