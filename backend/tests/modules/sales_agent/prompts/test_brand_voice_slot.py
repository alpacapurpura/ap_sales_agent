"""S7 — slot 5 BRAND_VOICE wiring tests.

Verifies:
- ``PromptFragment.BRAND_VOICE`` exists and replaced legacy ``OFFER_SUMMARY``.
- ``compose_system_prompt`` renders ``state['brand_voice']`` in slot 5.
- Slot 5 lives in the cacheable prefix (before CACHE_BOUNDARY_MARKER).
- Slot 4 ``agent_identity`` and slot 5 ``brand_voice`` can both be empty
  without breaking the composition.
"""

from __future__ import annotations

from luana_core_sales_agent.application.prompts.compose import (
    CACHE_BOUNDARY_MARKER,
    CACHEABLE_FRAGMENTS,
    PromptFragment,
    SpecialistRole,
    build_specialist_system_prompt,
    compose_system_prompt,
)


def _make_state(**overrides):
    base = {
        "agent_identity": "## WHO+WHAT\nBrand Acme.",
        "brand_voice": "## BLOQUE 1 — REGLAS DE PERSONALIDAD\nWarm and direct.",
        "channel_type": None,
        "current_state": "rapport",
        "lead_score": 0,
        "turn_count": 0,
        "buying_signals": [],
        "objection_history": [],
        "qualification_answers": {},
        "session_gap_hours": None,
        "last_session_summary": None,
        "consecutive_questions": 0,
    }
    base.update(overrides)
    return base


class TestBrandVoiceSlot5:
    def test_brand_voice_fragment_in_cacheable_prefix(self) -> None:
        """Slot 5 is registered as cacheable (before the cache boundary)."""
        assert PromptFragment.BRAND_VOICE in CACHEABLE_FRAGMENTS

    def test_compose_renders_brand_voice_in_slot_5(self) -> None:
        """``compose_system_prompt`` includes brand_voice content."""
        result = compose_system_prompt(
            {
                PromptFragment.STATIC_IDENTITY: "## STATIC",
                PromptFragment.AGENT_IDENTITY: "## WHO+WHAT",
                PromptFragment.BRAND_VOICE: "## VOICE BLOCK",
            }
        )
        assert "## VOICE BLOCK" in result
        # Voice must come AFTER agent_identity in cache prefix order.
        idx_who = result.index("## WHO+WHAT")
        idx_voice = result.index("## VOICE BLOCK")
        assert idx_who < idx_voice

    def test_brand_voice_lives_before_cache_boundary(self) -> None:
        """Stable slot must appear in the cacheable prefix half."""
        state = _make_state()
        rendered = build_specialist_system_prompt(state, SpecialistRole.QUALIFIER)
        # Brand voice text must appear before the boundary marker.
        boundary = rendered.find(CACHE_BOUNDARY_MARKER)
        voice_idx = rendered.find(state["brand_voice"])
        assert voice_idx >= 0
        assert boundary == -1 or voice_idx < boundary

    def test_empty_brand_voice_does_not_break_composition(self) -> None:
        """When tenant has no voice configured, slot 5 stays empty without crashing."""
        state = _make_state(brand_voice=None)
        rendered = build_specialist_system_prompt(state, SpecialistRole.QUALIFIER)
        assert "## WHO+WHAT" in rendered

    def test_no_legacy_offer_summary_attribute(self) -> None:
        """The renamed slot must not expose the legacy name."""
        assert not hasattr(PromptFragment, "OFFER_SUMMARY")
