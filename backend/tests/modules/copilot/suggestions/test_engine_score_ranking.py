"""TDD — SuggestionEngine: ranking, caps, route filter, provider exception.

Tests written RED first per ``tdd-mandatory.md``.
"""

from __future__ import annotations

from uuid import uuid4

import pytest


def _ctx(route: str | None = "offer-studio"):
    from luana_core_copilot.domain.suggestion import SuggestionContext

    return SuggestionContext(
        tenant_id=uuid4(),
        user_id=None,
        conversation_id=None,
        current_route=route,
    )


def _make_suggestions(*labels_and_confidences):
    """Return list of Suggestion objects from (label, confidence) pairs."""
    from luana_core_copilot.domain.suggestion import Suggestion

    return [
        Suggestion(label=label, prompt=label, confidence=conf, source_module="test")
        for label, conf in labels_and_confidences
    ]


def _make_provider(pid, routes, suggestions_or_exc):
    from luana_core_copilot.domain.suggestion import SuggestionContext, Suggestion

    class _Stub:
        @property
        def provider_id(self):
            return pid

        @property
        def provider_priority(self) -> int:
            return 0

        @property
        def applies_to_routes(self):
            return routes

        def get_suggestions(self, ctx: SuggestionContext, *, max_per_provider=5) -> list[Suggestion]:
            if isinstance(suggestions_or_exc, Exception):
                raise suggestions_or_exc
            return suggestions_or_exc[:max_per_provider]

    return _Stub()


class TestEngineScoreRanking:
    def test_results_sorted_confidence_desc(self) -> None:
        from luana_core_copilot.application.suggestions.engine import SuggestionEngine

        engine = SuggestionEngine(max_total=10)
        low = _make_suggestions(("Low", 0.2), ("Mid", 0.5))
        high = _make_suggestions(
            ("High", 0.9),
        )
        engine.register(_make_provider("a", (), low))
        engine.register(_make_provider("b", (), high))

        results, _, _ = engine.get_suggestions(_ctx())
        confidences = [s.confidence for s in results]
        assert confidences == sorted(confidences, reverse=True)

    def test_max_total_cap_respected(self) -> None:
        from luana_core_copilot.application.suggestions.engine import SuggestionEngine

        engine = SuggestionEngine(max_total=2)
        suggestions = _make_suggestions(("A", 0.9), ("B", 0.8), ("C", 0.7))
        engine.register(_make_provider("x", (), suggestions))

        results, _, _ = engine.get_suggestions(_ctx())
        assert len(results) <= 2

    def test_max_per_provider_cap_respected(self) -> None:
        from luana_core_copilot.application.suggestions.engine import SuggestionEngine

        engine = SuggestionEngine(max_total=10, max_per_provider=2)
        suggestions = _make_suggestions(("A", 0.9), ("B", 0.8), ("C", 0.7))

        call_args = {}

        from luana_core_copilot.domain.suggestion import SuggestionContext, Suggestion

        class _CountingProvider:
            @property
            def provider_id(self):
                return "counter"

            @property
            def provider_priority(self) -> int:
                return 0

            @property
            def applies_to_routes(self):
                return ()

            def get_suggestions(self, ctx: SuggestionContext, *, max_per_provider=5) -> list[Suggestion]:
                call_args["max_per_provider"] = max_per_provider
                return suggestions[:max_per_provider]

        engine.register(_CountingProvider())
        engine.get_suggestions(_ctx())
        assert call_args["max_per_provider"] == 2

    def test_route_filter_skips_non_matching(self) -> None:
        from luana_core_copilot.application.suggestions.engine import SuggestionEngine

        engine = SuggestionEngine()
        brand_only = _make_suggestions(("Brand chip", 0.9))
        engine.register(_make_provider("brand", ("brand-studio",), brand_only))

        results, _, _ = engine.get_suggestions(_ctx("offer-studio"))
        assert results == []

    def test_route_filter_matches_prefix(self) -> None:
        from luana_core_copilot.application.suggestions.engine import SuggestionEngine

        engine = SuggestionEngine()
        offer_chip = _make_suggestions(("Offer chip", 0.9))
        engine.register(_make_provider("offer", ("offer-studio",), offer_chip))

        # exact match
        results, _, _ = engine.get_suggestions(_ctx("offer-studio"))
        assert len(results) == 1

        # prefix match (sub-route)
        results2, _, _ = engine.get_suggestions(_ctx("offer-studio/some-id"))
        assert len(results2) == 1

    def test_no_route_filter_always_active(self) -> None:
        from luana_core_copilot.application.suggestions.engine import SuggestionEngine

        engine = SuggestionEngine()
        universal = _make_suggestions(("Universal", 0.5))
        engine.register(_make_provider("uni", (), universal))

        results, _, _ = engine.get_suggestions(_ctx("any-route"))
        assert len(results) == 1

        results2, _, _ = engine.get_suggestions(_ctx(None))
        assert len(results2) == 1

    def test_provider_exception_is_swallowed(self) -> None:
        from luana_core_copilot.application.suggestions.engine import SuggestionEngine

        engine = SuggestionEngine()
        engine.register(_make_provider("bad", (), RuntimeError("boom")))
        good_chip = _make_suggestions(("Good", 0.8))
        engine.register(_make_provider("good", (), good_chip))

        results, breakdown, _ = engine.get_suggestions(_ctx())
        # bad provider doesn't propagate; good provider still contributes
        assert any(s.label == "Good" for s in results)
        assert "bad" not in breakdown

    def test_breakdown_counts_per_provider(self) -> None:
        from luana_core_copilot.application.suggestions.engine import SuggestionEngine

        engine = SuggestionEngine(max_total=10)
        engine.register(_make_provider("a", (), _make_suggestions(("A1", 0.9), ("A2", 0.8))))
        engine.register(
            _make_provider(
                "b",
                (),
                _make_suggestions(
                    ("B1", 0.7),
                ),
            )
        )

        _, breakdown, _ = engine.get_suggestions(_ctx())
        assert breakdown == {"a": 2, "b": 1}

    def test_latency_ms_is_non_negative(self) -> None:
        from luana_core_copilot.application.suggestions.engine import SuggestionEngine

        engine = SuggestionEngine()
        _, _, latency = engine.get_suggestions(_ctx())
        assert latency >= 0


class TestProviderPriority:
    def test_tie_break_uses_provider_priority_desc(self) -> None:
        """Q3 decision: tie-break confidence DESC → provider_priority DESC → registration order."""
        from luana_core_copilot.application.suggestions.engine import SuggestionEngine
        from luana_core_copilot.domain.suggestion import Suggestion, SuggestionContext

        engine = SuggestionEngine(max_total=10)

        class _PriorityProvider:
            def __init__(self, pid, prio, label):
                self._pid = pid
                self._prio = prio
                self._label = label

            @property
            def provider_id(self):
                return self._pid

            @property
            def provider_priority(self) -> int:
                return self._prio

            @property
            def applies_to_routes(self):
                return ()

            def get_suggestions(self, ctx: SuggestionContext, *, max_per_provider=5) -> list[Suggestion]:
                return [Suggestion(label=self._label, prompt=self._label, confidence=0.5, source_module=self._pid)]

        # Register low-priority first, high-priority second
        engine.register(_PriorityProvider("low", 0, "Low priority"))
        engine.register(_PriorityProvider("high", 10, "High priority"))

        results, _, _ = engine.get_suggestions(_ctx())
        # Both have confidence 0.5, so priority breaks the tie: high should come first
        assert results[0].label == "High priority"
