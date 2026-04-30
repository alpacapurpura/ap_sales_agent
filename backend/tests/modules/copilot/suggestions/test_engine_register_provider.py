"""TDD — SuggestionEngine: provider registration invariants.

Tests written RED first per ``tdd-mandatory.md``.
"""

from __future__ import annotations

from uuid import uuid4

import pytest


def _make_provider(provider_id: str, routes: tuple[str, ...] = ()):
    """Minimal provider stub satisfying the Protocol."""
    from src.modules.copilot.domain.suggestion import Suggestion, SuggestionContext

    class _Stub:
        @property
        def provider_id(self) -> str:
            return provider_id

        @property
        def applies_to_routes(self) -> tuple[str, ...]:
            return routes

        def get_suggestions(self, ctx: SuggestionContext, *, max_per_provider: int = 5) -> list[Suggestion]:
            return []

    return _Stub()


class TestEngineRegistration:
    def test_register_adds_provider(self) -> None:
        from src.modules.copilot.application.suggestions.engine import SuggestionEngine

        engine = SuggestionEngine()
        p = _make_provider("offer")
        engine.register(p)
        suggestions, breakdown, _ = engine.get_suggestions(_ctx("offer-studio"))
        assert isinstance(suggestions, list)

    def test_register_same_instance_twice_is_noop(self) -> None:
        from src.modules.copilot.application.suggestions.engine import SuggestionEngine

        engine = SuggestionEngine()
        p = _make_provider("offer")
        engine.register(p)
        engine.register(p)  # idempotent — no error
        assert len(engine._providers) == 1

    def test_register_different_instance_same_id_raises(self) -> None:
        from src.modules.copilot.application.suggestions.engine import SuggestionEngine

        engine = SuggestionEngine()
        engine.register(_make_provider("offer"))
        with pytest.raises(ValueError, match="offer"):
            engine.register(_make_provider("offer"))

    def test_empty_engine_returns_empty_suggestions(self) -> None:
        from src.modules.copilot.application.suggestions.engine import SuggestionEngine

        engine = SuggestionEngine()
        suggestions, breakdown, latency_ms = engine.get_suggestions(_ctx("offer-studio"))
        assert suggestions == []
        assert breakdown == {}
        assert latency_ms >= 0


def _ctx(route: str):
    from src.modules.copilot.domain.suggestion import SuggestionContext

    return SuggestionContext(
        tenant_id=uuid4(),
        user_id=None,
        conversation_id=None,
        current_route=route,
    )
