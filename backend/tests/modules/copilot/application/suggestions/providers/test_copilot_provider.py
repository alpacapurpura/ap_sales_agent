"""TDD — CopilotSuggestionProvider: transversal, low-priority fallback.

Tests written RED first per ``tdd-mandatory.md``.
Uses mocks — no DB required.

PR-2-pure-expansion-providers / PI-2 S2.
"""

from __future__ import annotations

import re
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

_VOSEO_RE = re.compile(
    r"\b(sos|tenés|podés|querés|sabés|hacés|venís|decís|mirá|dejá|poné|usá|hacé|"
    r"elegí|seleccioná|arrancá|empezá|agregá|configurá|revisá|escribí|guardá|subí|"
    r"bajá|abrí|volvé|andá|cambiá|ofrecés|cobrás|ejecutás|acompañás|activás|"
    r"desactivás|linkeá|listá|probá|mostrá|compartí|contá|explicá)\b",
    re.IGNORECASE,
)

_TENANT = uuid4()


def _ctx(
    route: str | None = None,
    conversation_id=None,
    recent_message_ids=(),
    tenant_id=None,
):
    from src.modules.copilot.domain.suggestion import SuggestionContext

    return SuggestionContext(
        tenant_id=tenant_id or _TENANT,
        user_id=None,
        conversation_id=conversation_id,
        current_route=route,
        recent_message_ids=recent_message_ids,
    )


def _mock_module_registry(route_prefixes: list[str] | None = None) -> dict:
    """Return a mock module registry dict."""
    from src.modules.copilot.domain.module_registry import ModuleDescriptor

    prefixes = route_prefixes or ["brand-studio", "offer-studio", "sales", "growth-studio"]
    return {prefix: MagicMock(spec=ModuleDescriptor, route_prefix=prefix) for prefix in prefixes}


def _mock_brand_port(brand_data: dict | None = None, personality_present: bool = True) -> MagicMock:
    from src.shared.links.ports.brand import BrandKnowledgeDTO

    port = MagicMock()
    port.get_brand_knowledge.return_value = BrandKnowledgeDTO(
        brand_data=brand_data
        or {"identity": {"brand_name": "ACME"}, "positioning": {"unique_value_proposition": "UVP"}},
        avatars=[],
        personality_profile={"id": str(uuid4())} if personality_present else None,
    )
    port.get_buyer_persona_count.return_value = 1
    port.get_active_personality_profile_present.return_value = personality_present
    return port


def _mock_offer_repo(offer_count: int = 1) -> MagicMock:
    repo = MagicMock()
    repo.get_all_by_tenant.return_value = [MagicMock() for _ in range(offer_count)]
    return repo


class TestCopilotProviderMetadata:
    def test_copilot_provider_metadata(self) -> None:
        """provider_id=copilot, priority=5, applies_to_routes=() (always active)."""
        from src.modules.copilot.application.suggestions.providers.copilot import (
            CopilotSuggestionProvider,
        )

        p = CopilotSuggestionProvider()
        assert p.provider_id == "copilot"
        assert p.provider_priority == 5
        assert p.applies_to_routes == ()


class TestCopilotProviderRules:
    def test_copilot_provider_no_conversation_emits_first_chat_chip(self) -> None:
        """conversation_id is None → 'Empieza tu primer chat' chip."""
        from src.modules.copilot.application.suggestions.providers.copilot import (
            CopilotSuggestionProvider,
        )

        registry = _mock_module_registry()
        brand_port = _mock_brand_port()
        offer_repo = _mock_offer_repo(offer_count=1)
        with (
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.get_module_registry",
                return_value=registry,
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.SessionLocal",
                return_value=MagicMock(),
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.create_brand_data_port",
                return_value=brand_port,
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.get_offer_repository",
                return_value=offer_repo,
            ),
        ):
            p = CopilotSuggestionProvider()
            chips = p.get_suggestions(_ctx(conversation_id=None, route="brand-studio"))

        labels = [c.label for c in chips]
        assert any("chat" in l.lower() or "copiloto" in l.lower() for l in labels), (
            f"Expected first-chat chip in {labels}"
        )

    def test_copilot_provider_empty_conversation_emits_resume_chip(self) -> None:
        """conv_id set + recent_message_ids=() → 'Retoma' chip."""
        from src.modules.copilot.application.suggestions.providers.copilot import (
            CopilotSuggestionProvider,
        )

        registry = _mock_module_registry()
        brand_port = _mock_brand_port()
        offer_repo = _mock_offer_repo(offer_count=1)
        conv_id = uuid4()
        with (
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.get_module_registry",
                return_value=registry,
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.SessionLocal",
                return_value=MagicMock(),
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.create_brand_data_port",
                return_value=brand_port,
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.get_offer_repository",
                return_value=offer_repo,
            ),
        ):
            p = CopilotSuggestionProvider()
            chips = p.get_suggestions(_ctx(conversation_id=conv_id, recent_message_ids=(), route="brand-studio"))

        labels = [c.label for c in chips]
        assert any("retoma" in l.lower() or "conversación" in l.lower() for l in labels), (
            f"Expected resume chip in {labels}"
        )

    def test_copilot_provider_no_route_emits_explore_chip(self) -> None:
        """current_route=None → 'Explorar capacidades' chip."""
        from src.modules.copilot.application.suggestions.providers.copilot import (
            CopilotSuggestionProvider,
        )

        registry = _mock_module_registry()
        brand_port = _mock_brand_port()
        offer_repo = _mock_offer_repo(offer_count=1)
        with (
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.get_module_registry",
                return_value=registry,
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.SessionLocal",
                return_value=MagicMock(),
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.create_brand_data_port",
                return_value=brand_port,
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.get_offer_repository",
                return_value=offer_repo,
            ),
        ):
            p = CopilotSuggestionProvider()
            # has conv but no route
            chips = p.get_suggestions(_ctx(conversation_id=uuid4(), recent_message_ids=(uuid4(),), route=None))

        labels = [c.label for c in chips]
        assert any("explorar" in l.lower() or "capacidades" in l.lower() for l in labels), (
            f"Expected explore chip in {labels}"
        )

    def test_copilot_provider_unknown_route_emits_navigate_back_chip(self) -> None:
        """route=unknown-x + registry no match → 'Volver' chip."""
        from src.modules.copilot.application.suggestions.providers.copilot import (
            CopilotSuggestionProvider,
        )

        registry = _mock_module_registry(route_prefixes=["brand-studio", "offer-studio"])
        brand_port = _mock_brand_port()
        offer_repo = _mock_offer_repo(offer_count=1)
        with (
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.get_module_registry",
                return_value=registry,
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.SessionLocal",
                return_value=MagicMock(),
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.create_brand_data_port",
                return_value=brand_port,
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.get_offer_repository",
                return_value=offer_repo,
            ),
        ):
            p = CopilotSuggestionProvider()
            chips = p.get_suggestions(
                _ctx(conversation_id=uuid4(), recent_message_ids=(uuid4(),), route="unknown-feature-xyz")
            )

        labels = [c.label for c in chips]
        assert any("volver" in l.lower() or "módulo" in l.lower() for l in labels), (
            f"Expected navigate-back chip in {labels}"
        )

    def test_copilot_provider_low_setup_emits_onboarding_chip(self) -> None:
        """count_completed_modules <= 1 → 'Completa tu setup' chip."""
        from src.modules.copilot.application.suggestions.providers.copilot import (
            CopilotSuggestionProvider,
        )

        registry = _mock_module_registry()
        # Brand incomplete (no brand_name), no offers, no personality
        brand_port = _mock_brand_port(brand_data={}, personality_present=False)
        offer_repo = _mock_offer_repo(offer_count=0)  # no offers
        with (
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.get_module_registry",
                return_value=registry,
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.SessionLocal",
                return_value=MagicMock(),
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.create_brand_data_port",
                return_value=brand_port,
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.get_offer_repository",
                return_value=offer_repo,
            ),
        ):
            p = CopilotSuggestionProvider()
            # Has conv with messages, has known route
            chips = p.get_suggestions(
                _ctx(conversation_id=uuid4(), recent_message_ids=(uuid4(),), route="brand-studio")
            )

        labels = [c.label for c in chips]
        assert any("setup" in l.lower() or "completa" in l.lower() or "configura" in l.lower() for l in labels), (
            f"Expected onboarding chip in {labels}"
        )

    def test_copilot_provider_exception_returns_empty_list(self) -> None:
        """Exception in any internal call → returns []."""
        from src.modules.copilot.application.suggestions.providers.copilot import (
            CopilotSuggestionProvider,
        )

        with (
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.get_module_registry",
                side_effect=RuntimeError("registry unavailable"),
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.SessionLocal",
                return_value=MagicMock(),
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.create_brand_data_port",
                return_value=MagicMock(),
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.get_offer_repository",
                return_value=MagicMock(),
            ),
        ):
            p = CopilotSuggestionProvider()
            chips = p.get_suggestions(_ctx())

        assert chips == []

    def test_copilot_provider_tenant_isolation(self) -> None:
        """Every DB read uses ctx.tenant_id — no cross-tenant leak."""
        from src.modules.copilot.application.suggestions.providers.copilot import (
            CopilotSuggestionProvider,
        )

        tenant_a = uuid4()
        registry = _mock_module_registry()
        brand_port = _mock_brand_port()
        offer_repo = _mock_offer_repo(offer_count=1)
        with (
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.get_module_registry",
                return_value=registry,
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.SessionLocal",
                return_value=MagicMock(),
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.create_brand_data_port",
                return_value=brand_port,
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.get_offer_repository",
                return_value=offer_repo,
            ),
        ):
            p = CopilotSuggestionProvider()
            p.get_suggestions(
                _ctx(tenant_id=tenant_a, conversation_id=uuid4(), recent_message_ids=(uuid4(),), route="brand-studio")
            )

        # Offer repo should be called with tenant_a
        offer_repo.get_all_by_tenant.assert_called_once_with(tenant_a)


class TestCopilotProviderSpanishNeutro:
    def test_no_voseo_in_chips(self) -> None:
        """All chip labels/prompts respect Spanish neutro LatAm."""
        from src.modules.copilot.application.suggestions.providers.copilot import (
            CopilotSuggestionProvider,
        )

        registry = _mock_module_registry(route_prefixes=["brand-studio"])
        brand_port = _mock_brand_port(brand_data={}, personality_present=False)
        offer_repo = _mock_offer_repo(offer_count=0)
        with (
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.get_module_registry",
                return_value=registry,
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.SessionLocal",
                return_value=MagicMock(),
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.create_brand_data_port",
                return_value=brand_port,
            ),
            patch(
                "src.modules.copilot.application.suggestions.providers.copilot.get_offer_repository",
                return_value=offer_repo,
            ),
        ):
            p = CopilotSuggestionProvider()
            chips = p.get_suggestions(_ctx(conversation_id=None, route=None))

        for chip in chips:
            assert not _VOSEO_RE.search(chip.label), f"Voseo in label: {chip.label!r}"
            assert not _VOSEO_RE.search(chip.prompt), f"Voseo in prompt: {chip.prompt!r}"
