"""PR-7 Sub-A.5 — Slot 7 CAMPAIGN_CONTEXT compose tests.

Asserts:
- ``outbound_mode=False`` → slot 7 ausente del output prompt.
- ``outbound_mode=True`` + instructions → slot 7 emitted POST channel_format_hint.
- Cache prefix slots 1-6 byte-equal across modes (cache prefix per-tenant invariant).

# [SALES-AGENT-OUTBOUND-PR7]
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest

from luana_core_sales_agent.application.orchestrator.state import create_initial_state
from luana_core_sales_agent.application.prompts.compose import (
    CACHE_BOUNDARY_MARKER,
    CACHEABLE_FRAGMENTS,
    PROMPT_FRAGMENT_ORDER,
    PromptFragment,
    SpecialistRole,
    build_specialist_system_prompt,
)


def _base_state(**overrides: Any) -> dict:
    """Minimal AgentState with consistent identity + voice slots set."""
    state = create_initial_state(
        user_id=str(uuid4()),
        tenant_id=str(uuid4()),
        agent_identity="# Identidad del tenant\n\nNegocio: Test Tenant LATAM",
        brand_voice="# Voz de marca\n\nTono cálido y directo, tú no vos.",
        channel_type="telegram",
    )
    state.update(overrides)
    return state


class TestCampaignContextEnumOrdering:
    """Slot 7 must be POST channel_format_hint and inside CACHEABLE_FRAGMENTS."""

    def test_campaign_context_enum_value_exists(self) -> None:
        assert PromptFragment.CAMPAIGN_CONTEXT.value == "campaign_context"

    def test_campaign_context_in_cacheable_fragments(self) -> None:
        assert PromptFragment.CAMPAIGN_CONTEXT in CACHEABLE_FRAGMENTS

    def test_campaign_context_is_last_cacheable(self) -> None:
        """Slot 7 == ultimo cacheable, POST CHANNEL_FORMAT_HINT (slot 6)."""
        assert CACHEABLE_FRAGMENTS[-1] is PromptFragment.CAMPAIGN_CONTEXT
        assert CACHEABLE_FRAGMENTS[-2] is PromptFragment.CHANNEL_FORMAT_HINT

    def test_campaign_context_in_prompt_fragment_order(self) -> None:
        assert PromptFragment.CAMPAIGN_CONTEXT in PROMPT_FRAGMENT_ORDER


class TestSlot7AbsentInbound:
    """outbound_mode=False (default) → slot 7 not emitted."""

    def test_inbound_default_no_campaign_context_block(self) -> None:
        state = _base_state()
        prompt = build_specialist_system_prompt(state, SpecialistRole.QUALIFIER)
        assert "Contexto de campaña" not in prompt
        assert "Instrucciones de campaña" not in prompt

    def test_outbound_false_explicit_no_campaign_context_block(self) -> None:
        state = _base_state(
            outbound_mode=False,
            campaign_instructions="Promo 30% off — esto NO debe aparecer",
        )
        prompt = build_specialist_system_prompt(state, SpecialistRole.QUALIFIER)
        assert "Contexto de campaña" not in prompt
        assert "Promo 30% off" not in prompt

    def test_outbound_true_empty_instructions_no_block(self) -> None:
        state = _base_state(outbound_mode=True, campaign_instructions="")
        prompt = build_specialist_system_prompt(state, SpecialistRole.QUALIFIER)
        assert "Contexto de campaña" not in prompt

    def test_outbound_true_whitespace_instructions_no_block(self) -> None:
        state = _base_state(outbound_mode=True, campaign_instructions="   \n\n  ")
        prompt = build_specialist_system_prompt(state, SpecialistRole.QUALIFIER)
        assert "Contexto de campaña" not in prompt


class TestSlot7EmittedOutbound:
    """outbound_mode=True + instructions → slot 7 emitted POST channel_format_hint."""

    def test_outbound_true_emits_campaign_context(self) -> None:
        state = _base_state(
            outbound_mode=True,
            campaign_instructions="Promo Black Friday 30% off hasta el viernes.",
        )
        prompt = build_specialist_system_prompt(state, SpecialistRole.CLOSER)
        assert "# Contexto de campaña" in prompt
        assert "Promo Black Friday 30% off" in prompt

    def test_slot_7_post_slot_6_channel_format(self) -> None:
        """Slot ordering: CHANNEL_FORMAT_HINT must appear BEFORE CAMPAIGN_CONTEXT."""
        state = _base_state(
            outbound_mode=True,
            campaign_instructions="Test instructions",
        )
        prompt = build_specialist_system_prompt(state, SpecialistRole.CLOSER)
        # Telegram canal active → slot 6 contiene "Reglas del canal"
        idx_channel = prompt.find("Reglas del canal")
        idx_campaign = prompt.find("# Contexto de campaña")
        assert idx_channel >= 0, "channel_format_hint should be present"
        assert idx_campaign >= 0, "campaign_context should be present"
        assert idx_channel < idx_campaign, "slot 6 channel must come BEFORE slot 7 campaign"

    def test_slot_7_pre_cache_boundary(self) -> None:
        """Slot 7 cacheable → must come BEFORE CACHE_BOUNDARY_MARKER."""
        state = _base_state(
            outbound_mode=True,
            campaign_instructions="Test instructions",
        )
        prompt = build_specialist_system_prompt(state, SpecialistRole.CLOSER)
        idx_campaign = prompt.find("# Contexto de campaña")
        idx_boundary = prompt.find(CACHE_BOUNDARY_MARKER)
        assert idx_campaign >= 0
        assert idx_boundary >= 0
        assert idx_campaign < idx_boundary, "campaign_context cacheable goes BEFORE boundary"


class TestCachePrefixInvariance:
    """Slots 1-6 byte-equal across inbound/outbound for same tenant.

    Cache prefix per-tenant invariance is the SACRA invariant from
    sales-agent-brand-voice.md — adding outbound mode must NOT invalidate
    inbound's cache prefix.
    """

    def test_slots_1_6_byte_equal_inbound_vs_outbound(self) -> None:
        tenant_id = str(uuid4())
        common = {
            "user_id": str(uuid4()),
            "tenant_id": tenant_id,
            "agent_identity": "# Identidad\n\nTenant ABC",
            "brand_voice": "# Voz\n\nCálido y directo",
            "channel_type": "telegram",
        }

        state_inbound = create_initial_state(**common, outbound_mode=False)
        state_outbound = create_initial_state(
            **common,
            outbound_mode=True,
            campaign_instructions="Promo X",
            campaign_id=uuid4(),
        )

        prompt_inbound = build_specialist_system_prompt(state_inbound, SpecialistRole.QUALIFIER)
        prompt_outbound = build_specialist_system_prompt(state_outbound, SpecialistRole.QUALIFIER)

        # Slice prefix: from start to "# Contexto de campaña" in outbound,
        # equivalent slice in inbound (which ends before boundary marker).
        idx_campaign_out = prompt_outbound.find("# Contexto de campaña")
        prefix_outbound = prompt_outbound[:idx_campaign_out].rstrip()
        # Inbound has no slot 7 → prefix ends at boundary marker
        idx_boundary_in = prompt_inbound.find(CACHE_BOUNDARY_MARKER)
        prefix_inbound = prompt_inbound[:idx_boundary_in].rstrip() if idx_boundary_in >= 0 else prompt_inbound.rstrip()

        # Slots 1-6 must be byte-equal
        assert prefix_inbound == prefix_outbound, (
            "Cache prefix slots 1-6 must be byte-equal across inbound/outbound "
            "for the same tenant — outbound additive cannot invalidate inbound cache."
        )


class TestCampaignContextContent:
    """The slot 7 block must contain instructions verbatim and proper framing."""

    def test_includes_outbound_framing_text(self) -> None:
        state = _base_state(
            outbound_mode=True,
            campaign_instructions="Brief XYZ",
        )
        prompt = build_specialist_system_prompt(state, SpecialistRole.CLOSER)
        # Framing
        assert "Estás iniciando una conversación outbound" in prompt
        assert "primer turno" in prompt
        # Instructions verbatim (Decision: NO LLM rewrite)
        assert "Brief XYZ" in prompt

    def test_no_tenant_name_interpolation_mid_block(self) -> None:
        """SACRA invariant: NO {tenant_name} mid-block (cache invalidation rule)."""
        state = _base_state(
            outbound_mode=True,
            campaign_instructions="Hola, soy {{tenant_name}} y tengo una promo",
        )
        prompt = build_specialist_system_prompt(state, SpecialistRole.CLOSER)
        # Instructions emitted verbatim — but builder must NOT inject tenant_name
        # The `{{tenant_name}}` is just user-provided text passing through.
        # Verifies that the BUILDER does not interpolate any tenant identifier
        # outside of slot 4 (AGENT_IDENTITY).
        assert "{{tenant_name}}" in prompt  # passes through as-is (no jinja eval)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
