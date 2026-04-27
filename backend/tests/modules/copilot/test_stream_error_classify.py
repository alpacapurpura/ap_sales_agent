"""Tests for stream-error classification + user-facing copy.

Sprint 1.5 — when a provider returns 429/overloaded the orchestrator
needs to:
1. Tag the trace with ``error_kind='provider_overloaded'``.
2. Show the user a Spanish-neutro friendly message (not "Ocurrió un
   error" generic) so they know to retry.

Conv real reproductora: 2026-04-27 18:48:32 turn_end status='error'
``RateLimitError: Error code: 429 - engine_overloaded_error``.
"""

from __future__ import annotations

import pytest

from src.modules.copilot.application.orchestrator.chat import (
    _classify_stream_error,
    _user_facing_error_message,
)


class _RateLimitError(Exception):
    """Stand-in for openai.RateLimitError without importing it."""


class GraphRecursionError(Exception):
    """Stand-in for langgraph.GraphRecursionError matched by class-name string."""


class TestClassifyStreamError:
    def test_kimi_engine_overloaded_classifies_as_provider_overloaded(self) -> None:
        err = _RateLimitError(
            "Error code: 429 - {'error': {'message': 'The engine is currently "
            "overloaded, please try again later', 'type': 'engine_overloaded_error'}}",
        )
        assert _classify_stream_error(err) == "provider_overloaded"

    def test_openai_rate_limit_classname_classifies(self) -> None:
        # Even when message lacks "overloaded", the class name carries signal.
        err = _RateLimitError("brief")
        # type-name match via "ratelimit" pattern.
        assert _classify_stream_error(err) == "provider_overloaded"

    def test_503_message_classifies_as_overloaded(self) -> None:
        err = Exception("Service Unavailable: 503")
        assert _classify_stream_error(err) == "provider_overloaded"

    def test_graph_recursion_classifies_separately(self) -> None:
        err = GraphRecursionError("recursion limit hit")
        assert _classify_stream_error(err) == "graph_recursion"

    def test_unknown_error_falls_back_to_stream_error(self) -> None:
        err = ValueError("some random parse fail")
        assert _classify_stream_error(err) == "stream_error"


class TestUserFacingErrorMessage:
    @pytest.mark.parametrize(
        "kind",
        ["provider_overloaded", "graph_recursion", "stream_error"],
    )
    def test_known_kinds_return_neutro_spanish_copy(self, kind: str) -> None:
        msg = _user_facing_error_message(kind)
        assert isinstance(msg, str)
        assert len(msg) > 20  # not the empty string / placeholder
        # Spanish-neutro tuteo invariant — no voseo verb endings.
        assert "podés" not in msg
        assert "tenés" not in msg
        assert "querés" not in msg

    def test_overloaded_copy_mentions_retry(self) -> None:
        msg = _user_facing_error_message("provider_overloaded")
        assert "vuelve a enviar" in msg or "intenta" in msg.lower()

    def test_unknown_kind_falls_back_to_generic(self) -> None:
        generic = _user_facing_error_message("stream_error")
        assert _user_facing_error_message("totally_unknown_kind") == generic
