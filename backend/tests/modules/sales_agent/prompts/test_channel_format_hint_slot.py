"""S5 — slot 6 ``CHANNEL_FORMAT_HINT`` populated from the channel registry.

When ``state.channel_type`` is set, ``build_specialist_system_prompt`` reads
the ``structure_hint`` from ``shared.agent_observability.channels`` and
injects it in the cacheable prefix (slot 6, before CACHE_BOUNDARY_MARKER).

# [SALES-AGENT-CHANNEL-REGISTRY-S5]
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest

from luana_core_sales_agent.application.orchestrator.state import create_initial_state
from luana_core_sales_agent.application.prompts.compose import (
    CACHE_BOUNDARY_MARKER,
    SpecialistRole,
    build_specialist_system_prompt,
)
from luana_core_channels.format import (
    get_channel_format,
    reset_registry_for_tests,
)


@pytest.fixture(autouse=True)
def _reset():
    reset_registry_for_tests()
    yield
    reset_registry_for_tests()


def _state(**overrides: Any) -> dict[str, Any]:
    state = create_initial_state(
        user_id=str(uuid.uuid4()),
        tenant_id=str(uuid.uuid4()),
        agent_identity="# Identity\nTest tenant identity.",
        tenant_config={"brand_name": "Test"},
        channel_type="whatsapp",
    )
    state.update(overrides)
    return state


class TestChannelFormatHintSlotPopulated:
    def test_whatsapp_hint_appears_in_prompt(self) -> None:
        prompt = build_specialist_system_prompt(_state(channel_type="whatsapp"), SpecialistRole.QUALIFIER)
        wa_hint = get_channel_format("whatsapp").structure_hint
        assert wa_hint, "whatsapp baseline must declare structure_hint"
        # First sentence (or distinctive substring) of the hint must appear.
        first_chunk = wa_hint.split(".")[0][:60].strip()
        assert first_chunk and first_chunk in prompt, (
            f"Expected channel structure_hint snippet in prompt; missing {first_chunk!r}."
        )

    def test_telegram_hint_differs_from_whatsapp(self) -> None:
        wa = build_specialist_system_prompt(_state(channel_type="whatsapp"), SpecialistRole.QUALIFIER)
        tg = build_specialist_system_prompt(_state(channel_type="telegram"), SpecialistRole.QUALIFIER)
        assert wa != tg, "different channels should yield different prompts"

    def test_hint_lands_before_cache_boundary(self) -> None:
        prompt = build_specialist_system_prompt(_state(channel_type="whatsapp"), SpecialistRole.QUALIFIER)
        wa_hint = get_channel_format("whatsapp").structure_hint.split(".")[0][:40].strip()
        boundary_idx = prompt.index(CACHE_BOUNDARY_MARKER)
        hint_idx = prompt.find(wa_hint)
        assert hint_idx != -1
        assert hint_idx < boundary_idx, "channel hint must land in cacheable prefix"

    def test_no_channel_type_means_empty_slot(self) -> None:
        """Without channel_type the slot stays empty (no fallback noise)."""
        state = _state(channel_type=None)
        prompt = build_specialist_system_prompt(state, SpecialistRole.QUALIFIER)
        # No channel hint phrase — but prompt still composed.
        assert prompt
        # Defensive: if AgentState defaults to None, slot should be empty.
        # We check by composing the same state with an explicit channel
        # and confirming the prompts differ.
        prompt_with = build_specialist_system_prompt(_state(channel_type="whatsapp"), SpecialistRole.QUALIFIER)
        assert prompt != prompt_with

    def test_unknown_channel_uses_chat_hint(self) -> None:
        """Unknown channel falls back to ``chat`` — get_channel_format
        already enforces fallback; the prompt slot should reflect chat hint."""
        state = _state(channel_type="zzz_unknown")
        prompt = build_specialist_system_prompt(state, SpecialistRole.QUALIFIER)
        chat_hint = get_channel_format("chat").structure_hint.split(".")[0][:30].strip()
        assert chat_hint in prompt

    def test_alias_instagram_resolves(self) -> None:
        """Sales AgentState uses ``instagram`` as channel_type; registry must
        resolve to ``instagram_dm`` baseline so slot 6 reflects IG hint."""
        state = _state(channel_type="instagram")
        prompt = build_specialist_system_prompt(state, SpecialistRole.QUALIFIER)
        ig_hint = get_channel_format("instagram_dm").structure_hint.split(".")[0][:30].strip()
        assert ig_hint in prompt


class TestChannelHintCacheableInvariant:
    """Slot 6 lands in cacheable prefix → multiple turns same channel = same bytes."""

    def test_same_channel_same_prefix(self) -> None:
        a = build_specialist_system_prompt(_state(channel_type="whatsapp"), SpecialistRole.QUALIFIER)
        b = build_specialist_system_prompt(_state(channel_type="whatsapp"), SpecialistRole.QUALIFIER)
        prefix_a = a.split(CACHE_BOUNDARY_MARKER, maxsplit=1)[0]
        prefix_b = b.split(CACHE_BOUNDARY_MARKER, maxsplit=1)[0]
        assert prefix_a == prefix_b

    def test_volatile_change_does_not_alter_channel_slot(self) -> None:
        a = build_specialist_system_prompt(
            _state(channel_type="whatsapp", lead_score=10),
            SpecialistRole.QUALIFIER,
        )
        b = build_specialist_system_prompt(
            _state(channel_type="whatsapp", lead_score=99),
            SpecialistRole.QUALIFIER,
        )
        prefix_a = a.split(CACHE_BOUNDARY_MARKER, maxsplit=1)[0]
        prefix_b = b.split(CACHE_BOUNDARY_MARKER, maxsplit=1)[0]
        assert prefix_a == prefix_b
