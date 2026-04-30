"""TDD — BrandSuggestionProvider: heuristic, route-scoped, tenant-isolated.

Tests written RED first per ``tdd-mandatory.md``.
Uses mocks — no DB required.

PR-2-pure-expansion-providers / PI-2 S2.
"""

from __future__ import annotations

import re
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

# Voseo regex — canonical (from brand_summary_regen.py)
_VOSEO_RE = re.compile(
    r"\b(sos|tenés|podés|querés|sabés|hacés|venís|decís|mirá|dejá|poné|usá|hacé|"
    r"elegí|seleccioná|arrancá|empezá|agregá|configurá|revisá|escribí|guardá|subí|"
    r"bajá|abrí|volvé|andá|cambiá|ofrecés|cobrás|ejecutás|acompañás|activás|"
    r"desactivás|linkeá|listá|probá|mostrá|compartí|contá|explicá)\b",
    re.IGNORECASE,
)

_TENANT = uuid4()


def _ctx(route: str | None = "brand-studio", tenant_id=None):
    from src.modules.copilot.domain.suggestion import SuggestionContext

    return SuggestionContext(
        tenant_id=tenant_id or _TENANT,
        user_id=None,
        conversation_id=None,
        current_route=route,
    )


def _mock_port(
    brand_data: dict | None = None,
    persona_count: int = 1,
    personality_present: bool = True,
) -> MagicMock:
    """Return a mock BrandDataPort with configurable brand state."""
    from src.shared.links.ports.brand import BrandKnowledgeDTO

    port = MagicMock()
    port.get_brand_knowledge.return_value = BrandKnowledgeDTO(
        brand_data=brand_data if brand_data is not None else {},
        avatars=[],
        personality_profile=None,
    )
    port.get_buyer_persona_count.return_value = persona_count
    port.get_active_personality_profile_present.return_value = personality_present
    return port


def _full_brand_data() -> dict:
    """Brand data with all 4 required blocks populated."""
    return {
        "identity": {"brand_name": "ACME Corp"},
        "positioning": {"unique_value_proposition": "Unique value here"},
        "narrative": {"one_liner": "We help X achieve Y."},
        "brand_personality": {"archetype": "hero"},
    }


class TestBrandProviderMetadata:
    def test_brand_provider_metadata(self) -> None:
        """provider_id, provider_priority, applies_to_routes contract."""
        from src.modules.copilot.application.suggestions.providers.brand import (
            BrandSuggestionProvider,
        )

        p = BrandSuggestionProvider()
        assert p.provider_id == "brand"
        assert p.provider_priority == 10
        assert p.applies_to_routes == ("brand-studio",)


class TestBrandProviderRules:
    def test_brand_provider_empty_brand_emits_identity_chip(self) -> None:
        """Empty brand_data (no identity.brand_name) → 'Empieza por tu marca' chip."""
        from src.modules.copilot.application.suggestions.providers.brand import (
            BrandSuggestionProvider,
        )

        port = _mock_port(brand_data={}, persona_count=0, personality_present=False)
        with (
            patch(
                "src.modules.copilot.application.suggestions.providers.brand.SessionLocal",
            ) as mock_session,
            patch(
                "src.modules.copilot.application.suggestions.providers.brand.create_brand_data_port",
                return_value=port,
            ),
        ):
            mock_session.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_session.return_value.__exit__ = MagicMock(return_value=False)
            mock_session.return_value = MagicMock()
            p = BrandSuggestionProvider()
            chips = p.get_suggestions(_ctx())

        labels = [c.label for c in chips]
        assert "Empieza por tu marca" in labels

    def test_brand_provider_missing_uvp_emits_positioning_chip(self) -> None:
        """Brand with identity.brand_name but no positioning.UVP → positioning chip."""
        from src.modules.copilot.application.suggestions.providers.brand import (
            BrandSuggestionProvider,
        )

        brand_data = {
            "identity": {"brand_name": "ACME"},
            "positioning": {},
        }
        port = _mock_port(brand_data=brand_data, persona_count=1, personality_present=True)
        with (
            patch(
                "src.modules.copilot.application.suggestions.providers.brand.SessionLocal",
                return_value=MagicMock(),
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.brand.create_brand_data_port",
                return_value=port,
            ),
        ):
            p = BrandSuggestionProvider()
            chips = p.get_suggestions(_ctx())

        labels = [c.label for c in chips]
        assert "Define tu propuesta única" in labels

    def test_brand_provider_missing_archetype_emits_archetype_chip(self) -> None:
        """Brand with identity+positioning but no archetype → archetype chip."""
        from src.modules.copilot.application.suggestions.providers.brand import (
            BrandSuggestionProvider,
        )

        brand_data = {
            "identity": {"brand_name": "ACME"},
            "positioning": {"unique_value_proposition": "UVP here"},
            "narrative": {"one_liner": "One liner here"},
            "brand_personality": {},
        }
        port = _mock_port(brand_data=brand_data, persona_count=1, personality_present=True)
        with (
            patch(
                "src.modules.copilot.application.suggestions.providers.brand.SessionLocal",
                return_value=MagicMock(),
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.brand.create_brand_data_port",
                return_value=port,
            ),
        ):
            p = BrandSuggestionProvider()
            chips = p.get_suggestions(_ctx())

        labels = [c.label for c in chips]
        assert "Elige tu arquetipo de marca" in labels

    def test_brand_provider_no_buyer_persona_emits_persona_chip(self) -> None:
        """buyer_persona_count=0 → 'Crea tu buyer persona principal' chip."""
        from src.modules.copilot.application.suggestions.providers.brand import (
            BrandSuggestionProvider,
        )

        port = _mock_port(
            brand_data=_full_brand_data(),
            persona_count=0,
            personality_present=True,
        )
        with (
            patch(
                "src.modules.copilot.application.suggestions.providers.brand.SessionLocal",
                return_value=MagicMock(),
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.brand.create_brand_data_port",
                return_value=port,
            ),
        ):
            p = BrandSuggestionProvider()
            chips = p.get_suggestions(_ctx())

        labels = [c.label for c in chips]
        assert "Crea tu buyer persona principal" in labels

    def test_brand_provider_no_personality_profile_emits_voice_chip(self) -> None:
        """get_active_personality_profile_present=False → 'Configura la voz' chip."""
        from src.modules.copilot.application.suggestions.providers.brand import (
            BrandSuggestionProvider,
        )

        port = _mock_port(
            brand_data=_full_brand_data(),
            persona_count=1,
            personality_present=False,
        )
        with (
            patch(
                "src.modules.copilot.application.suggestions.providers.brand.SessionLocal",
                return_value=MagicMock(),
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.brand.create_brand_data_port",
                return_value=port,
            ),
        ):
            p = BrandSuggestionProvider()
            chips = p.get_suggestions(_ctx())

        labels = [c.label for c in chips]
        assert "Configura la voz del agente" in labels

    def test_brand_provider_full_brand_emits_zero_chips(self) -> None:
        """All blocks complete → returns []."""
        from src.modules.copilot.application.suggestions.providers.brand import (
            BrandSuggestionProvider,
        )

        port = _mock_port(
            brand_data=_full_brand_data(),
            persona_count=2,
            personality_present=True,
        )
        with (
            patch(
                "src.modules.copilot.application.suggestions.providers.brand.SessionLocal",
                return_value=MagicMock(),
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.brand.create_brand_data_port",
                return_value=port,
            ),
        ):
            p = BrandSuggestionProvider()
            chips = p.get_suggestions(_ctx())

        assert chips == []

    def test_brand_provider_port_exception_returns_empty_list(self) -> None:
        """Port raises → caught + structlog warning + returns []."""
        from src.modules.copilot.application.suggestions.providers.brand import (
            BrandSuggestionProvider,
        )

        port = MagicMock()
        port.get_brand_knowledge.side_effect = RuntimeError("DB unreachable")
        with (
            patch(
                "src.modules.copilot.application.suggestions.providers.brand.SessionLocal",
                return_value=MagicMock(),
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.brand.create_brand_data_port",
                return_value=port,
            ),
        ):
            p = BrandSuggestionProvider()
            chips = p.get_suggestions(_ctx())

        assert chips == []

    def test_brand_provider_tenant_isolation(self) -> None:
        """Provider passes tenant_id from ctx to port — no cross-tenant leak."""
        from src.modules.copilot.application.suggestions.providers.brand import (
            BrandSuggestionProvider,
        )

        tenant_a = uuid4()
        port = _mock_port(brand_data=_full_brand_data(), persona_count=1, personality_present=True)
        with (
            patch(
                "src.modules.copilot.application.suggestions.providers.brand.SessionLocal",
                return_value=MagicMock(),
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.brand.create_brand_data_port",
                return_value=port,
            ),
        ):
            p = BrandSuggestionProvider()
            p.get_suggestions(_ctx(tenant_id=tenant_a))

        port.get_brand_knowledge.assert_called_once_with(tenant_a)
        port.get_buyer_persona_count.assert_called_once_with(tenant_a)
        port.get_active_personality_profile_present.assert_called_once_with(tenant_a)


class TestBrandProviderSpanishNeutro:
    def test_no_voseo_in_chip_labels_and_prompts(self) -> None:
        """All chip labels and prompts respect Spanish neutro LatAm (no voseo)."""
        from src.modules.copilot.application.suggestions.providers.brand import (
            BrandSuggestionProvider,
        )

        port = _mock_port(brand_data={}, persona_count=0, personality_present=False)
        with (
            patch(
                "src.modules.copilot.application.suggestions.providers.brand.SessionLocal",
                return_value=MagicMock(),
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.brand.create_brand_data_port",
                return_value=port,
            ),
        ):
            p = BrandSuggestionProvider()
            chips = p.get_suggestions(_ctx())

        for chip in chips:
            assert not _VOSEO_RE.search(chip.label), f"Voseo in label: {chip.label!r}"
            assert not _VOSEO_RE.search(chip.prompt), f"Voseo in prompt: {chip.prompt!r}"
