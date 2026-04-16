"""Tests for PersonalityProfile integration in TenantKnowledgeBuilder.

TDD: these tests define the expected behavior BEFORE implementation.

Tests:
1. test_personality_profile_loaded_when_active
2. test_fallback_to_voice_tone_when_no_profile
3. test_style_anchor_retriever_formats_correctly
4. test_style_anchor_retriever_graceful_degradation
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from jinja2 import Environment, FileSystemLoader

from src.modules.sales_agent.application.services.style_anchor_retriever import (
    StyleAnchorRetriever,
)

# ---------------------------------------------------------------------------
# Jinja2 environment (mirrors test_prompts.py pattern)
# ---------------------------------------------------------------------------

TEMPLATES_DIR = str(
    Path(__file__).parent
    / ".."
    / ".."
    / ".."
    / "src"
    / "modules"
    / "sales_agent"
    / "infrastructure"
    / "prompts"
    / "templates"
)


@pytest.fixture
def jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(Path(TEMPLATES_DIR).resolve())),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TENANT_ID = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")
PROFILE_ID = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")

PERSONALITY_SYSTEM_INSTRUCTION = (
    "Habla siempre en primera persona, con tono cercano y directo. "
    "Usa frases cortas. Sé muy específico con los números."
)

MINIMAL_IDENTITY_CONTEXT: dict[str, Any] = {
    "has_brand": True,
    "identity": {
        "brand_name": "TestBrand",
        "tagline": "We test things",
        "voice_tone": "Professional and warm",
        "communication_style": "Friendly",
    },
    "strategy": {"mission": "Test mission"},
    "positioning": {"unique_value_proposition": "Best tests"},
    "story": None,
    "has_team": False,
    "team": [],
    "has_avatars": False,
    "default_avatar": {},
    "avatars": [],
    "has_offers": False,
    "offers": [],
    "has_testimonials": False,
    "testimonials": [],
    "channel_type": "instagram",
}


def _make_brand_knowledge(brand_data: dict, personality_data: dict | None = None) -> MagicMock:
    """Build a mock BrandKnowledgeDTO."""
    from src.shared.links.ports.brand import BrandKnowledgeDTO

    return BrandKnowledgeDTO(
        brand_data=brand_data,
        avatars=[],
        personality_profile=personality_data,
    )


# ---------------------------------------------------------------------------
# 1. PersonalityProfile loaded into knowledge_builder when active
# ---------------------------------------------------------------------------


class TestKnowledgeBuilderPersonalityIntegration:
    """TenantKnowledgeBuilder uses PersonalityProfile.system_instruction when active."""

    def test_personality_profile_loaded_when_active(self) -> None:
        """When an active PersonalityProfile exists, build_identity uses system_instruction."""
        brand_data = {
            "identity": {"brand_name": "Acme", "voice_tone": "old_voice_tone_should_not_appear"},
            "strategy": {},
            "story": {},
            "team": [],
            "contact": {},
            "testimonials": [],
            "positioning": {},
        }
        personality_data = {"system_instruction": PERSONALITY_SYSTEM_INSTRUCTION}
        mock_brand_port = MagicMock()
        mock_brand_port.get_brand_knowledge.return_value = _make_brand_knowledge(brand_data, personality_data)

        mock_db = MagicMock()

        with (
            patch(
                "src.modules.sales_agent.application.services.knowledge_builder.create_brand_data_port",
                return_value=mock_brand_port,
            ),
            patch(
                "src.modules.sales_agent.application.services.knowledge_builder.get_offer_repository"
            ) as MockOfferRepo,
            patch("src.modules.sales_agent.application.services.knowledge_builder.SemanticRouter"),
        ):
            MockOfferRepo.return_value.get_all_by_tenant.return_value = []

            from src.modules.sales_agent.application.services.knowledge_builder import (
                TenantKnowledgeBuilder,
            )

            builder = TenantKnowledgeBuilder(mock_db)
            result = builder.build_identity(TENANT_ID)

        assert PERSONALITY_SYSTEM_INSTRUCTION in result
        assert "old_voice_tone_should_not_appear" not in result

    def test_fallback_to_voice_tone_when_no_profile(self) -> None:
        """When no PersonalityProfile exists, voice_tone from brand identity is used."""
        brand_data = {
            "identity": {"brand_name": "Acme", "voice_tone": "Very warm and professional"},
            "strategy": {},
            "story": {},
            "team": [],
            "contact": {},
            "testimonials": [],
            "positioning": {},
        }
        mock_brand_port = MagicMock()
        mock_brand_port.get_brand_knowledge.return_value = _make_brand_knowledge(brand_data, None)

        mock_db = MagicMock()

        with (
            patch(
                "src.modules.sales_agent.application.services.knowledge_builder.create_brand_data_port",
                return_value=mock_brand_port,
            ),
            patch(
                "src.modules.sales_agent.application.services.knowledge_builder.get_offer_repository"
            ) as MockOfferRepo,
            patch("src.modules.sales_agent.application.services.knowledge_builder.SemanticRouter"),
        ):
            MockOfferRepo.return_value.get_all_by_tenant.return_value = []

            from src.modules.sales_agent.application.services.knowledge_builder import (
                TenantKnowledgeBuilder,
            )

            builder = TenantKnowledgeBuilder(mock_db)
            result = builder.build_identity(TENANT_ID)

        assert "Very warm and professional" in result

    def test_personality_instruction_none_falls_back_to_voice_tone(self) -> None:
        """Profile exists and is active but system_instruction is None → voice_tone used."""
        brand_data = {
            "identity": {"brand_name": "Acme", "voice_tone": "Casual and fun"},
            "strategy": {},
            "story": {},
            "team": [],
            "contact": {},
            "testimonials": [],
            "positioning": {},
        }
        personality_data = {"system_instruction": None}
        mock_brand_port = MagicMock()
        mock_brand_port.get_brand_knowledge.return_value = _make_brand_knowledge(brand_data, personality_data)

        mock_db = MagicMock()

        with (
            patch(
                "src.modules.sales_agent.application.services.knowledge_builder.create_brand_data_port",
                return_value=mock_brand_port,
            ),
            patch(
                "src.modules.sales_agent.application.services.knowledge_builder.get_offer_repository"
            ) as MockOfferRepo,
            patch("src.modules.sales_agent.application.services.knowledge_builder.SemanticRouter"),
        ):
            MockOfferRepo.return_value.get_all_by_tenant.return_value = []

            from src.modules.sales_agent.application.services.knowledge_builder import (
                TenantKnowledgeBuilder,
            )

            builder = TenantKnowledgeBuilder(mock_db)
            result = builder.build_identity(TENANT_ID)

        assert "Casual and fun" in result


# ---------------------------------------------------------------------------
# 2. agent_identity.j2 template backward compatibility
# ---------------------------------------------------------------------------


class TestAgentIdentityTemplatePersonality:
    """Template renders correctly with/without personality_instruction."""

    def test_personality_instruction_takes_priority_over_voice_tone(self, jinja_env: Environment) -> None:
        """When personality_instruction is set, it replaces the voice_tone block."""
        ctx = {
            **MINIMAL_IDENTITY_CONTEXT,
            "personality_instruction": PERSONALITY_SYSTEM_INSTRUCTION,
        }
        template = jinja_env.get_template("agent_identity.j2")
        result = template.render(**ctx)

        assert PERSONALITY_SYSTEM_INSTRUCTION in result
        # The old voice_tone should NOT appear if personality_instruction is present
        assert "Tu Voz y Tono" not in result

    def test_voice_tone_rendered_when_no_personality_instruction(self, jinja_env: Environment) -> None:
        """When personality_instruction is absent/None, voice_tone is rendered."""
        ctx = {**MINIMAL_IDENTITY_CONTEXT, "personality_instruction": None}
        template = jinja_env.get_template("agent_identity.j2")
        result = template.render(**ctx)

        assert "Tu Voz y Tono" in result
        assert "Professional and warm" in result

    def test_style_anchors_rendered_when_present(self, jinja_env: Environment) -> None:
        """When style_anchors list is provided, few-shot examples appear in output."""
        anchors = [
            {
                "context_type": "objection_price",
                "other_message": "Es muy caro para mí",
                "author_response": "Entiendo, ¿qué parte del valor no quedó clara?",
            },
            {
                "context_type": "interest",
                "other_message": "¿Cuándo empieza el curso?",
                "author_response": "El próximo lunes, ¿te apunto?",
            },
        ]
        ctx = {
            **MINIMAL_IDENTITY_CONTEXT,
            "personality_instruction": None,
            "style_anchors": anchors,
        }
        template = jinja_env.get_template("agent_identity.j2")
        result = template.render(**ctx)

        assert "EJEMPLOS DE CÓMO RESPONDES" in result
        assert "Es muy caro para mí" in result
        assert "Entiendo, ¿qué parte del valor no quedó clara?" in result
        assert "¿Cuándo empieza el curso?" in result

    def test_no_style_anchors_section_when_absent(self, jinja_env: Environment) -> None:
        """When style_anchors is not provided, the examples section is absent."""
        ctx = {**MINIMAL_IDENTITY_CONTEXT, "personality_instruction": None}
        template = jinja_env.get_template("agent_identity.j2")
        result = template.render(**ctx)

        assert "EJEMPLOS DE CÓMO RESPONDES" not in result

    def test_no_style_anchors_section_when_empty_list(self, jinja_env: Environment) -> None:
        """When style_anchors is an empty list, the examples section is absent."""
        ctx = {
            **MINIMAL_IDENTITY_CONTEXT,
            "personality_instruction": None,
            "style_anchors": [],
        }
        template = jinja_env.get_template("agent_identity.j2")
        result = template.render(**ctx)

        assert "EJEMPLOS DE CÓMO RESPONDES" not in result

    def test_template_still_backward_compatible_without_new_keys(self, jinja_env: Environment) -> None:
        """Template renders without error when new context keys are not provided at all."""
        # MINIMAL_IDENTITY_CONTEXT does NOT have personality_instruction or style_anchors
        template = jinja_env.get_template("agent_identity.j2")
        # Should not raise UndefinedError
        result = template.render(**MINIMAL_IDENTITY_CONTEXT)
        assert "TestBrand" in result


# ---------------------------------------------------------------------------
# 3. StyleAnchorRetriever unit tests
# ---------------------------------------------------------------------------


class TestStyleAnchorRetriever:
    """Unit tests for StyleAnchorRetriever."""

    def test_format_as_few_shot_with_anchors(self) -> None:
        """format_as_few_shot produces correct few-shot text for a list of anchors."""
        mock_store = MagicMock()
        retriever = StyleAnchorRetriever(style_anchor_store=mock_store)

        anchors = [
            {
                "context_type": "objection_price",
                "other_message": "¿Por qué es tan caro?",
                "author_response": "Porque el resultado es de por vida.",
                "score": 0.92,
            },
            {
                "context_type": "interest",
                "other_message": "¿Me puedes contar más?",
                "author_response": "Claro, ¿qué parte te interesa más?",
                "score": 0.87,
            },
        ]

        result = retriever.format_as_few_shot(anchors)

        assert "EJEMPLOS DE CÓMO RESPONDES" in result
        assert "[objection_price]" in result
        assert "¿Por qué es tan caro?" in result
        assert "Porque el resultado es de por vida." in result
        assert "[interest]" in result
        assert "¿Me puedes contar más?" in result

    def test_format_as_few_shot_returns_empty_string_for_no_anchors(self) -> None:
        """format_as_few_shot returns empty string when anchors list is empty."""
        mock_store = MagicMock()
        retriever = StyleAnchorRetriever(style_anchor_store=mock_store)

        assert retriever.format_as_few_shot([]) == ""

    @pytest.mark.asyncio
    async def test_retrieve_calls_store_search_similar(self) -> None:
        """retrieve() delegates to StyleAnchorStore.search_similar with correct args."""
        mock_store = AsyncMock()
        mock_store.search_similar.return_value = [
            {
                "context_type": "greeting",
                "other_message": "Hola",
                "author_response": "¡Hola! ¿Qué tal?",
                "score": 0.95,
            }
        ]

        retriever = StyleAnchorRetriever(style_anchor_store=mock_store)
        results = await retriever.retrieve(
            tenant_id=TENANT_ID,
            profile_id=PROFILE_ID,
            prospect_message="Hola, quiero información",
            top_k=3,
        )

        mock_store.search_similar.assert_called_once_with(
            tenant_id=TENANT_ID,
            profile_id=PROFILE_ID,
            query_text="Hola, quiero información",
            top_k=3,
        )
        assert len(results) == 1
        assert results[0]["context_type"] == "greeting"

    @pytest.mark.asyncio
    async def test_style_anchor_retriever_graceful_degradation(self) -> None:
        """Returns empty list (not exception) when Qdrant store raises any error."""
        mock_store = AsyncMock()
        mock_store.search_similar.side_effect = Exception("Qdrant connection refused")

        retriever = StyleAnchorRetriever(style_anchor_store=mock_store)
        results = await retriever.retrieve(
            tenant_id=TENANT_ID,
            profile_id=PROFILE_ID,
            prospect_message="Quiero comprar",
            top_k=3,
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_retrieve_uses_default_top_k_of_3(self) -> None:
        """retrieve() uses top_k=3 as default when not specified."""
        mock_store = AsyncMock()
        mock_store.search_similar.return_value = []

        retriever = StyleAnchorRetriever(style_anchor_store=mock_store)
        await retriever.retrieve(
            tenant_id=TENANT_ID,
            profile_id=PROFILE_ID,
            prospect_message="Hola",
        )

        mock_store.search_similar.assert_called_once_with(
            tenant_id=TENANT_ID,
            profile_id=PROFILE_ID,
            query_text="Hola",
            top_k=3,
        )
