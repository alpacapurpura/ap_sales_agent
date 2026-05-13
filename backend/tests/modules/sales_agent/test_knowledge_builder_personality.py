"""Tests for the slot 4 (AGENT_IDENTITY) / slot 5 (BRAND_VOICE) split (S7).

Post-S7 architecture:
- ``build_identity()`` populates slot 4 = WHO+WHAT (brand, offers, team, legal).
  NO voice. The legacy ``personality_instruction`` and ``style_anchors`` blocks
  were removed from ``agent_identity.j2`` because injecting per-tenant voice
  inside the cacheable prefix breaks OpenAI/Kimi/DeepSeek prompt cache routing.
- ``build_brand_voice()`` populates slot 5 = HOW
  (``PersonalityProfile.system_instruction`` compiled deterministically by
  ``PersonalityCompiler``). Falls back to legacy ``BrandIdentity.voice_tone``
  wrapped in a header when no profile is configured.
- ``StyleAnchorRetriever`` continues to be the per-turn anchor lookup; it is
  no longer wired through ``agent_identity.j2`` and will be re-attached in a
  later sprint via the volatile zone of ``compose_system_prompt``.

See ``.claude/rules/sales-agent-brand-voice.md`` for the full SSoT.
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from jinja2 import Environment, FileSystemLoader

from luana_core_sales_agent.application.services.style_anchor_retriever import (
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


def _make_brand_knowledge(brand_data: dict, personality_data: dict | None = None) -> Any:
    """Build a real BrandKnowledgeDTO."""
    from luana_core_platform.links.ports.brand import BrandKnowledgeDTO

    return BrandKnowledgeDTO(
        brand_data=brand_data,
        avatars=[],
        personality_profile=personality_data,
    )


def _patched_builder(brand_knowledge: Any) -> Any:
    """Build a TenantKnowledgeBuilder with patched dependencies for unit tests."""
    mock_brand_port = MagicMock()
    mock_brand_port.get_brand_knowledge.return_value = brand_knowledge
    mock_db = MagicMock()

    patches = [
        patch(
            "luana_core_sales_agent.application.services.knowledge_builder.create_brand_data_port",
            return_value=mock_brand_port,
        ),
        patch(
            "luana_core_sales_agent.application.services.knowledge_builder.get_offer_repository",
        ),
        patch("luana_core_sales_agent.application.services.knowledge_builder.SemanticRouter"),
    ]
    for p in patches:
        started = p.start()
        if hasattr(started, "return_value") and hasattr(started.return_value, "get_all_by_tenant"):
            started.return_value.get_all_by_tenant.return_value = []

    from luana_core_sales_agent.application.services.knowledge_builder import (
        TenantKnowledgeBuilder,
    )

    return TenantKnowledgeBuilder(mock_db), patches


def _stop_patches(patches: list) -> None:
    for p in patches:
        p.stop()


# ---------------------------------------------------------------------------
# 1. Slot 4 (AGENT_IDENTITY) NEVER includes per-tenant voice (S7)
# ---------------------------------------------------------------------------


class TestAgentIdentitySlot4HasNoVoice:
    """Slot 4 is WHO+WHAT only. Voice (HOW) lives in slot 5 BRAND_VOICE."""

    def test_build_identity_does_not_include_personality_instruction(self) -> None:
        """``build_identity`` must NOT inject system_instruction in slot 4 anymore."""
        brand_data = {
            "identity": {"brand_name": "Acme", "voice_tone": "old voice tone"},
            "strategy": {},
            "story": {},
            "team": [],
            "contact": {},
            "testimonials": [],
            "positioning": {},
        }
        personality_data = {"system_instruction": PERSONALITY_SYSTEM_INSTRUCTION}
        knowledge = _make_brand_knowledge(brand_data, personality_data)
        builder, patches = _patched_builder(knowledge)
        try:
            result = builder.build_identity(TENANT_ID)
        finally:
            _stop_patches(patches)

        # System instruction must NOT appear in slot 4.
        assert PERSONALITY_SYSTEM_INSTRUCTION not in result
        # Legacy voice_tone fallback must also NOT appear in slot 4.
        assert "old voice tone" not in result
        # Brand WHO/WHAT must still appear.
        assert "Acme" in result

    def test_build_identity_does_not_include_voice_tone_fallback(self) -> None:
        """Without a PersonalityProfile, slot 4 still has no voice block."""
        brand_data = {
            "identity": {"brand_name": "Acme", "voice_tone": "Very warm and professional"},
            "strategy": {},
            "story": {},
            "team": [],
            "contact": {},
            "testimonials": [],
            "positioning": {},
        }
        knowledge = _make_brand_knowledge(brand_data, None)
        builder, patches = _patched_builder(knowledge)
        try:
            result = builder.build_identity(TENANT_ID)
        finally:
            _stop_patches(patches)

        assert "Very warm and professional" not in result
        assert "Tu Voz y Tono" not in result
        assert "Acme" in result


# ---------------------------------------------------------------------------
# 2. Slot 5 (BRAND_VOICE) carries the voice (S7)
# ---------------------------------------------------------------------------


class TestBrandVoiceSlot5:
    """``build_brand_voice`` returns the SSoT voice text for slot 5."""

    def test_returns_personality_system_instruction_when_active(self) -> None:
        """Active PersonalityProfile.system_instruction → returned as-is for slot 5."""
        brand_data = {
            "identity": {"brand_name": "Acme", "voice_tone": "should be ignored"},
        }
        personality_data = {"system_instruction": PERSONALITY_SYSTEM_INSTRUCTION}
        knowledge = _make_brand_knowledge(brand_data, personality_data)
        builder, patches = _patched_builder(knowledge)
        try:
            voice = builder.build_brand_voice(TENANT_ID)
        finally:
            _stop_patches(patches)

        assert voice == PERSONALITY_SYSTEM_INSTRUCTION

    def test_falls_back_to_voice_tone_when_no_profile(self) -> None:
        """No profile → legacy voice_tone wrapped in 'Tu Voz y Tono' header."""
        brand_data = {
            "identity": {"brand_name": "Acme", "voice_tone": "Very warm and professional"},
        }
        knowledge = _make_brand_knowledge(brand_data, None)
        builder, patches = _patched_builder(knowledge)
        try:
            voice = builder.build_brand_voice(TENANT_ID)
        finally:
            _stop_patches(patches)

        assert voice is not None
        assert "Tu Voz y Tono" in voice
        assert "Very warm and professional" in voice

    def test_returns_none_when_neither_configured(self) -> None:
        """No profile and no voice_tone → None (graceful slot 5 degradation)."""
        brand_data = {"identity": {"brand_name": "Acme"}}
        knowledge = _make_brand_knowledge(brand_data, None)
        builder, patches = _patched_builder(knowledge)
        try:
            voice = builder.build_brand_voice(TENANT_ID)
        finally:
            _stop_patches(patches)

        assert voice is None

    def test_falls_back_to_voice_tone_when_profile_system_instruction_is_none(self) -> None:
        """Profile exists but its system_instruction is None → use voice_tone."""
        brand_data = {
            "identity": {"brand_name": "Acme", "voice_tone": "Casual and fun"},
        }
        personality_data = {"system_instruction": None}
        knowledge = _make_brand_knowledge(brand_data, personality_data)
        builder, patches = _patched_builder(knowledge)
        try:
            voice = builder.build_brand_voice(TENANT_ID)
        finally:
            _stop_patches(patches)

        assert voice is not None
        assert "Casual and fun" in voice


# ---------------------------------------------------------------------------
# 3. agent_identity.j2 template no longer renders voice or anchors
# ---------------------------------------------------------------------------


class TestAgentIdentityTemplatePostS7:
    """Template renders WHO+WHAT only after the S7 slot split."""

    def test_template_does_not_render_personality_instruction(self, jinja_env: Environment) -> None:
        """The personality_instruction block was moved to slot 5; template ignores the kwarg."""
        ctx = {
            **MINIMAL_IDENTITY_CONTEXT,
            "personality_instruction": PERSONALITY_SYSTEM_INSTRUCTION,
        }
        template = jinja_env.get_template("agent_identity.j2")
        result = template.render(**ctx)

        assert PERSONALITY_SYSTEM_INSTRUCTION not in result
        assert "TestBrand" in result

    def test_template_does_not_render_voice_tone_fallback(self, jinja_env: Environment) -> None:
        """Legacy voice_tone fallback was removed from agent_identity.j2."""
        ctx = {**MINIMAL_IDENTITY_CONTEXT, "personality_instruction": None}
        template = jinja_env.get_template("agent_identity.j2")
        result = template.render(**ctx)

        assert "Tu Voz y Tono" not in result
        assert "Professional and warm" not in result

    def test_template_does_not_render_style_anchors(self, jinja_env: Environment) -> None:
        """Style anchors block was removed from slot 4 (would break cache prefix)."""
        anchors = [
            {
                "context_type": "objection_price",
                "other_message": "Es muy caro para mí",
                "author_response": "Entiendo, ¿qué parte del valor no quedó clara?",
            },
        ]
        ctx = {
            **MINIMAL_IDENTITY_CONTEXT,
            "personality_instruction": None,
            "style_anchors": anchors,
        }
        template = jinja_env.get_template("agent_identity.j2")
        result = template.render(**ctx)

        assert "EJEMPLOS DE CÓMO RESPONDES" not in result

    def test_template_still_backward_compatible_without_new_keys(self, jinja_env: Environment) -> None:
        """Template renders without error when context misses optional keys."""
        template = jinja_env.get_template("agent_identity.j2")
        result = template.render(**MINIMAL_IDENTITY_CONTEXT)
        assert "TestBrand" in result


# ---------------------------------------------------------------------------
# 4. StyleAnchorRetriever unit tests (unchanged — wiring will be added later)
# ---------------------------------------------------------------------------


class TestStyleAnchorRetriever:
    """Unit tests for StyleAnchorRetriever (kept as-is until volatile-zone wiring)."""

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
