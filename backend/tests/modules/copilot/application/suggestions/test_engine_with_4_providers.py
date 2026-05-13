"""TDD — Engine integration with 4 providers.

Tests written RED first per ``tdd-mandatory.md``.
Uses mock providers to avoid DB dependency.

PR-2-pure-expansion-providers / PI-2 S2.
"""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from luana_core_copilot.application.suggestions.engine import SuggestionEngine
from luana_core_copilot.domain.suggestion import Suggestion, SuggestionCategory, SuggestionContext


def _ctx(route: str | None = None, tenant_id=None, conversation_id=None, recent_messages=()):
    return SuggestionContext(
        tenant_id=tenant_id or uuid4(),
        user_id=None,
        conversation_id=conversation_id,
        current_route=route,
        recent_message_ids=recent_messages,
    )


def _make_provider(
    provider_id: str,
    priority: int,
    routes: tuple[str, ...],
    chips: list[Suggestion],
) -> MagicMock:
    p = MagicMock()
    p.provider_id = provider_id
    p.provider_priority = priority
    p.applies_to_routes = routes
    p.get_suggestions.return_value = chips
    return p


def _chip(label: str, confidence: float = 0.75, source: str = "test") -> Suggestion:
    return Suggestion(
        label=label,
        prompt=f"Prompt for {label}",
        confidence=confidence,
        category=SuggestionCategory.ACTION,
        source_module=source,
    )


class TestEngineWith4Providers:
    def test_engine_route_brand_studio_returns_brand_chips_not_offer(self) -> None:
        """ctx route=brand-studio → brand chips visible, offer chips skipped (route filter)."""
        offer_chip = _chip("Offer chip", 0.90, "offer")
        brand_chip = _chip("Brand chip", 0.85, "brand")

        offer_p = _make_provider("offer", 0, ("offer-studio",), [offer_chip])
        brand_p = _make_provider("brand", 10, ("brand-studio",), [brand_chip])
        copilot_p = _make_provider("copilot", 5, (), [])

        engine = SuggestionEngine(providers=[offer_p, brand_p, copilot_p])
        chips, breakdown, _ = engine.get_suggestions(_ctx(route="brand-studio"))

        labels = [c.label for c in chips]
        assert "Brand chip" in labels
        assert "Offer chip" not in labels

    def test_engine_route_sales_returns_sales_chips_plus_copilot(self) -> None:
        """ctx route=sales → sales chips + copilot fallback chips."""
        sales_chip = _chip("Sin leads", 0.88, "sales_agent")
        copilot_chip = _chip("Completa setup", 0.56, "copilot")

        sales_p = _make_provider("sales_agent", 10, ("sales",), [sales_chip])
        copilot_p = _make_provider("copilot", 5, (), [copilot_chip])

        engine = SuggestionEngine(providers=[sales_p, copilot_p])
        chips, breakdown, _ = engine.get_suggestions(_ctx(route="sales"))

        labels = [c.label for c in chips]
        assert "Sin leads" in labels
        assert "Completa setup" in labels

    def test_engine_unknown_route_returns_only_copilot_chips(self) -> None:
        """ctx route=unknown-xyz → only copilot (always-active) contributes."""
        offer_chip = _chip("Offer chip", 0.90, "offer")
        brand_chip = _chip("Brand chip", 0.85, "brand")
        copilot_chip = _chip("Explorar capacidades", 0.60, "copilot")

        offer_p = _make_provider("offer", 0, ("offer-studio",), [offer_chip])
        brand_p = _make_provider("brand", 10, ("brand-studio",), [brand_chip])
        copilot_p = _make_provider("copilot", 5, (), [copilot_chip])

        engine = SuggestionEngine(providers=[offer_p, brand_p, copilot_p])
        chips, _, _ = engine.get_suggestions(_ctx(route="unknown-xyz"))

        labels = [c.label for c in chips]
        assert "Offer chip" not in labels
        assert "Brand chip" not in labels
        assert "Explorar capacidades" in labels

    def test_engine_route_offer_studio_keeps_offer_provider_dominant(self) -> None:
        """Backwards compat: offer chips still surface on offer-studio route."""
        offer_chip = _chip("Crea tu primera oferta", 0.85, "offer")
        copilot_chip = _chip("Copilot fallback", 0.56, "copilot")

        offer_p = _make_provider("offer", 0, ("offer-studio",), [offer_chip])
        copilot_p = _make_provider("copilot", 5, (), [copilot_chip])

        engine = SuggestionEngine(providers=[offer_p, copilot_p])
        chips, _, _ = engine.get_suggestions(_ctx(route="offer-studio"))

        labels = [c.label for c in chips]
        assert "Crea tu primera oferta" in labels

    def test_engine_caps_at_5_total(self) -> None:
        """Engine returns at most 5 chips regardless of provider output."""
        many_chips = [_chip(f"Chip {i}", 0.8 - i * 0.05) for i in range(10)]
        p = _make_provider("brand", 10, (), many_chips)

        engine = SuggestionEngine(providers=[p], max_total=5)
        chips, _, _ = engine.get_suggestions(_ctx(route="brand-studio"))

        assert len(chips) <= 5

    def test_engine_provider_breakdown_per_provider_id(self) -> None:
        """Breakdown dict contains an entry for each provider that contributed."""
        brand_chip = _chip("Brand chip", 0.85, "brand")
        copilot_chip = _chip("Copilot chip", 0.56, "copilot")

        brand_p = _make_provider("brand", 10, ("brand-studio",), [brand_chip])
        copilot_p = _make_provider("copilot", 5, (), [copilot_chip])

        engine = SuggestionEngine(providers=[brand_p, copilot_p])
        _, breakdown, _ = engine.get_suggestions(_ctx(route="brand-studio"))

        assert "brand" in breakdown
        assert "copilot" in breakdown
        assert breakdown["brand"] == 1
        assert breakdown["copilot"] == 1

    def test_engine_provider_priority_breaks_tie(self) -> None:
        """Two chips same confidence + different providers → higher priority wins rank."""
        high_chip = _chip("High priority chip", 0.70, "brand")
        low_chip = _chip("Low priority chip", 0.70, "copilot")

        high_p = _make_provider("brand", 10, (), [high_chip])
        low_p = _make_provider("copilot", 5, (), [low_chip])

        engine = SuggestionEngine(providers=[low_p, high_p])  # reversed registration
        chips, _, _ = engine.get_suggestions(_ctx(route="brand-studio"))

        # High priority (brand=10) should rank before copilot (=5) on tied confidence
        assert chips[0].label == "High priority chip", f"Expected high-priority chip first, got {chips[0].label!r}"
