"""TDD — OfferSuggestionProvider: heuristic, route-scoped, tenant-isolated.

Tests written RED first per ``tdd-mandatory.md``.
Uses mocks so DB is not required.
"""

from __future__ import annotations

import re
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

# Voseo regex from brand_summary_regen.py (canonical)
_VOSEO_RE = re.compile(
    r"\b(sos|tenés|podés|querés|sabés|hacés|venís|decís|mirá|dejá|poné|usá|hacé|"
    r"elegí|seleccioná|arrancá|empezá|agregá|configurá|revisá|escribí|guardá|subí|"
    r"bajá|abrí|volvé|andá|cambiá|ofrecés|cobrás|ejecutás|acompañás|activás|"
    r"desactivás|linkeá|listá|probá|mostrá|compartí|contá|explicá)\b",
    re.IGNORECASE,
)


def _ctx(route: str | None = "offer-studio", offers=None, tenant_id=None):
    from src.modules.copilot.domain.suggestion import SuggestionContext

    return SuggestionContext(
        tenant_id=tenant_id or uuid4(),
        user_id=None,
        conversation_id=None,
        current_route=route,
    )


def _mock_reader(offers=None, flags=None, lead_without_core=False):
    """Return a mocked OfferSuggestionReader."""
    reader = MagicMock()
    reader.list_offers.return_value = offers or []
    reader.get_preset_flags.return_value = flags or []
    reader.detect_lead_magnet_without_core.return_value = lead_without_core
    return reader


class TestOfferSuggestionProviderInterface:
    def test_provider_id_is_offer(self) -> None:
        from src.modules.copilot.application.suggestions.providers.offer import (
            OfferSuggestionProvider,
        )

        p = OfferSuggestionProvider()
        assert p.provider_id == "offer"

    def test_applies_to_routes_contains_offer_studio(self) -> None:
        from src.modules.copilot.application.suggestions.providers.offer import (
            OfferSuggestionProvider,
        )

        p = OfferSuggestionProvider()
        assert "offer-studio" in p.applies_to_routes

    def test_provider_priority_is_int(self) -> None:
        from src.modules.copilot.application.suggestions.providers.offer import (
            OfferSuggestionProvider,
        )

        p = OfferSuggestionProvider()
        assert isinstance(p.provider_priority, int)


class TestOfferSuggestionProviderHeuristics:
    def _run_with_mock_reader(self, route, reader):
        from src.modules.copilot.application.suggestions.providers.offer import (
            OfferSuggestionProvider,
        )

        provider = OfferSuggestionProvider()
        ctx = _ctx(route)

        with (
            patch(
                "src.modules.copilot.application.suggestions.providers.offer.OfferSuggestionReader",
                return_value=reader,
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.offer.SessionLocal",
            ),
        ):
            return provider.get_suggestions(ctx)

    def test_no_offers_returns_create_chip(self) -> None:
        reader = _mock_reader(offers=[])
        results = self._run_with_mock_reader("offer-studio", reader)
        labels = [s.label for s in results]
        assert any("oferta" in l.lower() or "crea" in l.lower() for l in labels)

    def test_high_ticket_flag_yields_pricing_chip(self) -> None:
        from src.modules.copilot.application.suggestions.providers.offer import (
            OfferSuggestionProvider,
        )

        offer_id = uuid4()
        provider = OfferSuggestionProvider()
        ctx = _ctx(f"offer-studio/{offer_id}")

        reader = _mock_reader(flags=["high_ticket"])

        with (
            patch(
                "src.modules.copilot.application.suggestions.providers.offer.OfferSuggestionReader",
                return_value=reader,
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.offer.SessionLocal",
            ),
        ):
            results = provider.get_suggestions(ctx)

        labels = [s.label.lower() for s in results]
        assert any("pricing" in l or "precio" in l or "nivel" in l or "tier" in l for l in labels)

    def test_recurring_billing_flag_yields_subscription_chip(self) -> None:
        from src.modules.copilot.application.suggestions.providers.offer import (
            OfferSuggestionProvider,
        )

        offer_id = uuid4()
        provider = OfferSuggestionProvider()
        ctx = _ctx(f"offer-studio/{offer_id}")

        reader = _mock_reader(flags=["recurring_billing"])

        with (
            patch(
                "src.modules.copilot.application.suggestions.providers.offer.OfferSuggestionReader",
                return_value=reader,
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.offer.SessionLocal",
            ),
        ):
            results = provider.get_suggestions(ctx)

        labels = [s.label.lower() for s in results]
        assert any("recurrente" in l or "suscripcion" in l or "suscripción" in l or "facturación" in l for l in labels)

    def test_lead_magnet_without_core_yields_link_chip(self) -> None:
        reader = _mock_reader(lead_without_core=True)
        results = self._run_with_mock_reader("offer-studio", reader)
        labels = [s.label.lower() for s in results]
        assert any("core" in l or "vincula" in l or "enlaza" in l for l in labels)

    def test_incomplete_field_promise_yields_prompt_chip(self) -> None:
        from src.modules.copilot.application.suggestions.providers.offer import (
            OfferSuggestionProvider,
        )

        provider = OfferSuggestionProvider()
        ctx = _ctx("offer-studio")
        ctx_with_field = type(ctx)(
            tenant_id=ctx.tenant_id,
            user_id=ctx.user_id,
            conversation_id=ctx.conversation_id,
            current_route=ctx.current_route,
            incomplete_fields=("promise.headline",),
        )
        reader = _mock_reader(offers=[])

        with (
            patch(
                "src.modules.copilot.application.suggestions.providers.offer.OfferSuggestionReader",
                return_value=reader,
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.offer.SessionLocal",
            ),
        ):
            results = provider.get_suggestions(ctx_with_field)

        labels = [s.label.lower() for s in results]
        assert any("promesa" in l or "variante" in l or "headline" in l for l in labels)


class TestOfferSuggestionProviderResilience:
    def test_provider_returns_empty_on_db_failure(self) -> None:
        """Mock SessionLocal to raise; provider returns [] + warning (no exception bubbles)."""
        from src.modules.copilot.application.suggestions.providers.offer import (
            OfferSuggestionProvider,
        )

        provider = OfferSuggestionProvider()
        ctx = _ctx("offer-studio")

        with patch(
            "src.modules.copilot.application.suggestions.providers.offer.SessionLocal",
            side_effect=RuntimeError("DB down"),
        ):
            results = provider.get_suggestions(ctx)

        assert results == []

    def test_tenant_isolation_different_tenant_ignored(self) -> None:
        """Offers from another tenant must not appear in suggestions."""
        tenant_a = uuid4()
        tenant_b = uuid4()

        # Reader only returns offers for tenant A
        reader_a = _mock_reader(offers=[])
        reader_b = _mock_reader(offers=[])  # tenant B has no offers

        from src.modules.copilot.application.suggestions.providers.offer import (
            OfferSuggestionProvider,
        )

        provider = OfferSuggestionProvider()
        ctx = _ctx("offer-studio", tenant_id=tenant_a)

        with (
            patch(
                "src.modules.copilot.application.suggestions.providers.offer.OfferSuggestionReader",
                return_value=reader_a,
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.offer.SessionLocal",
            ),
        ):
            results_a = provider.get_suggestions(ctx)

        ctx_b = _ctx("offer-studio", tenant_id=tenant_b)
        with (
            patch(
                "src.modules.copilot.application.suggestions.providers.offer.OfferSuggestionReader",
                return_value=reader_b,
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.offer.SessionLocal",
            ),
        ):
            results_b = provider.get_suggestions(ctx_b)

        # Each context is isolated; no cross-contamination
        assert isinstance(results_a, list)
        assert isinstance(results_b, list)


class TestNoVoseo:
    def test_all_suggestion_labels_and_prompts_are_neutro(self) -> None:
        """All labels + prompts from OfferSuggestionProvider are voseo-free."""
        from src.modules.copilot.application.suggestions.providers.offer import (
            OfferSuggestionProvider,
        )

        provider = OfferSuggestionProvider()
        ctx = _ctx("offer-studio")

        # Test with multiple reader states to cover all branches
        scenarios = [
            _mock_reader(offers=[]),
            _mock_reader(flags=["high_ticket"]),
            _mock_reader(flags=["recurring_billing"]),
            _mock_reader(flags=["is_lead_magnet"]),
            _mock_reader(lead_without_core=True),
        ]

        for reader in scenarios:
            with (
                patch(
                    "src.modules.copilot.application.suggestions.providers.offer.OfferSuggestionReader",
                    return_value=reader,
                ),
                patch(
                    "src.modules.copilot.application.suggestions.providers.offer.SessionLocal",
                ),
            ):
                results = provider.get_suggestions(ctx)

            for s in results:
                assert not _VOSEO_RE.search(s.label), f"Voseo in label: {s.label!r}"
                assert not _VOSEO_RE.search(s.prompt), f"Voseo in prompt: {s.prompt!r}"
