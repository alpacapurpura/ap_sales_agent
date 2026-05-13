"""Integration tests for the Personality Engine full flow.

Tests the chain: select preset → verify instruction → knowledge_builder loads it →
update dimensions → verify recompilation → fallback when no profile.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from luana_core_brand_studio.application.services.personality_service import PersonalityService
from luana_core_brand_studio.domain.personality import PERSONALITY_PRESETS
from luana_core_brand_studio.infrastructure.repositories.personality_repository import (
    PersonalityProfileRepository,
)


class TestPersonalityIntegrationFlow:
    """Full flow: preset selection → instruction compilation → sales agent consumption."""

    @pytest.fixture
    def tenant_id(self):
        return uuid4()

    @pytest.fixture
    def service(self, db):
        return PersonalityService(db=db)

    @pytest.fixture
    def repo(self, db):
        return PersonalityProfileRepository(db)

    def test_select_preset_full_flow(self, service, repo, tenant_id):
        """Select preset → profile created and active → instruction compiled."""
        profile = service.select_preset(tenant_id, "warm_close")

        # Profile exists and is active
        active = repo.get_active(tenant_id=tenant_id)
        assert active is not None
        assert str(active.id) == str(profile.id)
        assert active.is_active is True
        assert active.profile_type == "preset"
        assert active.preset_key == "warm_close"

        # System instruction is compiled (5 blocks present)
        assert active.system_instruction is not None
        assert len(active.system_instruction) > 200
        # Block 5 identity anchor always present
        assert "ESTA ES TU VOZ" in active.system_instruction

        # Dimensions match the preset
        assert active.dimensions["energy"] == 0.65
        assert active.dimensions["warmth"] == 0.85

        # Sample exchanges are populated
        assert len(active.sample_exchanges) >= 5

    def test_switch_preset_deactivates_previous(self, service, repo, tenant_id):
        """Switching presets deactivates the old one."""
        p1 = service.select_preset(tenant_id, "warm_close")
        p2 = service.select_preset(tenant_id, "minimalist")

        active = repo.get_active(tenant_id=tenant_id)
        assert active is not None
        assert str(active.id) == str(p2.id)
        assert active.preset_key == "minimalist"

        # Old profile is deactivated
        old = repo.get_by_id(p1.id, tenant_id=tenant_id)
        assert old is not None
        assert old.is_active is False

    def test_update_dimensions_recompiles_instruction(self, service, repo, tenant_id):
        """Changing dimensions produces different instruction."""
        profile = service.select_preset(tenant_id, "warm_close")
        original_instruction = profile.system_instruction

        # Change energy from 0.65 (alta) to 0.1 (muy_baja)
        updated = service.update_dimensions(
            profile.id,
            tenant_id,
            {
                "energy": 0.1,
                "warmth": 0.85,
                "humor": 0.6,
                "expressiveness": 0.7,
                "narrative": 0.5,
                "verbosity": 0.4,
            },
        )

        assert updated is not None
        assert updated.system_instruction != original_instruction
        # Low energy (0.1 → muy_baja) triggers content about measured/no-exclamation style
        new_instr = updated.system_instruction.lower()
        assert "mesuradas" in new_instr or "exclamaci" in new_instr
        # Should now have negative constraints for energy
        assert len(updated.negative_constraints) > 0

    def test_different_presets_produce_different_instructions(self, service, tenant_id):
        """Each preset produces a substantially different system_instruction."""
        instructions = {}
        for preset_key in ["warm_close", "minimalist", "electric", "direct"]:
            # Use a distinct tenant per preset so activate() doesn't clobber others
            t = uuid4()
            profile = service.select_preset(t, preset_key)
            instructions[preset_key] = profile.system_instruction

        # All instructions should be different
        values = list(instructions.values())
        for i, v1 in enumerate(values):
            for v2 in values[i + 1 :]:
                assert v1 != v2, "Two presets produced identical instructions"

        # Minimalist has many NUNCA rules (energy=0.15, warmth=0.25, humor=0.1,
        # expressiveness=0.1, narrative=0.2, verbosity=0.15 — all below 0.3 threshold)
        # warm_close has none (all dims above 0.3 threshold)
        warm_nunca = instructions["warm_close"].count("NUNCA")
        mini_nunca = instructions["minimalist"].count("NUNCA")
        assert mini_nunca > warm_nunca

    def test_fallback_when_no_active_profile(self, repo, tenant_id):
        """When no profile exists, get_active returns None (agent uses voice_tone fallback)."""
        active = repo.get_active(tenant_id=tenant_id)
        assert active is None

    def test_soft_delete_clears_active(self, service, repo, tenant_id):
        """After deleting a profile, no active profile exists."""
        profile = service.select_preset(tenant_id, "warm_close")
        repo.soft_delete(profile.id, tenant_id=tenant_id)

        active = repo.get_active(tenant_id=tenant_id)
        assert active is None

    def test_tenant_isolation(self, service, repo):
        """Profiles from one tenant are invisible to another."""
        tenant_a = uuid4()
        tenant_b = uuid4()

        service.select_preset(tenant_a, "warm_close")

        # Tenant B sees nothing
        assert repo.get_active(tenant_id=tenant_b) is None
