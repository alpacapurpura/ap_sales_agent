"""Tests for PersonalityService — preset selection, get_active, update_dimensions."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from src.modules.brand.application.services.personality_service import PersonalityService
from tests.modules.conftest import TENANT_A

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def service(db: Session) -> PersonalityService:
    """PersonalityService with no Qdrant (Qdrant is optional in unit tests)."""
    return PersonalityService(db=db)


@pytest.fixture
def seed_tenant(db: Session) -> None:
    """Ensure TENANT_A exists in the DB so FK constraints are satisfied (if any)."""
    # The personality_profiles table has no FK to tenants in the test schema
    # (SQLite doesn't enforce FK by default), so this fixture is a no-op here.
    # We keep it for forward compatibility.


class TestGetActive:
    def test_get_active_returns_none_initially(self, service: PersonalityService) -> None:
        """get_active() returns None when no profile has been created yet."""
        result = service.get_active(TENANT_A)
        assert result is None


class TestSelectPreset:
    def test_select_preset_creates_active_profile(self, service: PersonalityService) -> None:
        """select_preset() creates a profile and immediately activates it."""
        profile = service.select_preset(TENANT_A, "warm_close")

        assert profile is not None
        assert profile.preset_key == "warm_close"
        assert profile.profile_type == "preset"
        assert profile.is_active is True
        assert str(profile.tenant_id) == str(TENANT_A)

    def test_select_preset_active_is_returned_by_get_active(self, service: PersonalityService) -> None:
        """After select_preset(), get_active() returns the newly created profile."""
        created = service.select_preset(TENANT_A, "warm_close")

        active = service.get_active(TENANT_A)

        assert active is not None
        assert str(active.id) == str(created.id)

    def test_select_preset_stores_name(self, service: PersonalityService) -> None:
        """select_preset() stores the preset's display name on the profile."""
        profile = service.select_preset(TENANT_A, "electric")

        assert profile.name == "Eléctrica y Expresiva"

    def test_select_preset_all_six_presets_work(self, service: PersonalityService, db: Session) -> None:
        """Every preset key in PERSONALITY_PRESETS can be selected without error."""
        from src.modules.brand.domain.personality import PERSONALITY_PRESETS

        for key in PERSONALITY_PRESETS:
            svc = PersonalityService(db=db)
            profile = svc.select_preset(uuid.uuid4(), key)
            assert profile.preset_key == key

    # ------------------------------------------------------------------
    # test_select_preset_compiles_instruction
    # ------------------------------------------------------------------

    def test_select_preset_compiles_instruction(self, service: PersonalityService) -> None:
        """select_preset() populates system_instruction and it contains expected blocks."""
        profile = service.select_preset(TENANT_A, "warm_close")

        instruction = profile.system_instruction
        assert instruction is not None
        assert len(instruction) > 100  # non-trivial content
        # PersonalityCompiler emits these block headers
        assert "BLOQUE 1" in instruction
        assert "BLOQUE 2" in instruction
        assert "BLOQUE 5" in instruction

    def test_select_preset_compiles_linguistic_block(self, service: PersonalityService) -> None:
        """The compiled instruction includes the greeting from linguistic_patterns."""
        profile = service.select_preset(TENANT_A, "warm_close")

        # warm_close greeting is "¡Hola! ¿Cómo estás?"
        assert "¡Hola!" in (profile.system_instruction or "")

    def test_select_unknown_preset_raises_value_error(self, service: PersonalityService) -> None:
        """select_preset() raises ValueError for an unknown preset key."""
        with pytest.raises(ValueError, match="Unknown preset"):
            service.select_preset(TENANT_A, "nonexistent_preset_xyz")

    def test_select_second_preset_deactivates_first(self, service: PersonalityService) -> None:
        """Selecting a second preset deactivates the first."""
        first = service.select_preset(TENANT_A, "warm_close")
        second = service.select_preset(TENANT_A, "electric")

        active = service.get_active(TENANT_A)
        assert active is not None
        assert str(active.id) == str(second.id)

        # Reload first from DB to check it is now inactive
        from src.modules.brand.infrastructure.repositories.personality_repository import (
            PersonalityProfileRepository,
        )

        repo = PersonalityProfileRepository(service.db)
        first_refreshed = repo.get_by_id(first.id, tenant_id=TENANT_A)
        assert first_refreshed is not None
        assert first_refreshed.is_active is False


class TestUpdateDimensions:
    def test_update_dimensions_recompiles_instruction(self, service: PersonalityService) -> None:
        """update_dimensions() changes energy from 0.65 to 0.1; instruction reflects new level."""
        profile = service.select_preset(TENANT_A, "warm_close")

        # Original energy = 0.65 → "alta" level (words like "¡vamos!", "¡dale!")
        original_instruction = profile.system_instruction or ""

        # Change energy to very low (0.1 → "muy_baja" level)
        new_dims = {
            "energy": 0.1,
            "warmth": 0.85,
            "humor": 0.6,
            "expressiveness": 0.7,
            "narrative": 0.5,
            "verbosity": 0.4,
        }
        updated = service.update_dimensions(profile.id, TENANT_A, new_dims)

        assert updated is not None
        new_instruction = updated.system_instruction or ""

        # Instruction must have changed
        assert new_instruction != original_instruction

        # Low energy (0.1 → muy_baja) triggers negative constraints about exclamaciones
        assert "NUNCA" in new_instruction or "exclamaci" in new_instruction.lower()

    def test_update_dimensions_preserves_linguistic_patterns(self, service: PersonalityService) -> None:
        """update_dimensions() keeps linguistic_patterns block from original preset."""
        profile = service.select_preset(TENANT_A, "warm_close")

        new_dims = {
            "energy": 0.5,
            "warmth": 0.5,
            "humor": 0.5,
            "expressiveness": 0.5,
            "narrative": 0.5,
            "verbosity": 0.5,
        }
        updated = service.update_dimensions(profile.id, TENANT_A, new_dims)

        assert updated is not None
        # BLOQUE 2 uses linguistic_patterns — greeting should still appear
        assert "BLOQUE 2" in (updated.system_instruction or "")

    def test_update_dimensions_nonexistent_profile_returns_none(self, service: PersonalityService) -> None:
        """update_dimensions() returns None for a profile that does not exist."""
        new_dims = {
            "energy": 0.5,
            "warmth": 0.5,
            "humor": 0.5,
            "expressiveness": 0.5,
            "narrative": 0.5,
            "verbosity": 0.5,
        }
        result = service.update_dimensions(uuid.uuid4(), TENANT_A, new_dims)
        assert result is None

    def test_update_dimensions_wrong_tenant_returns_none(self, service: PersonalityService) -> None:
        """update_dimensions() returns None when tenant_id does not match."""
        other_tenant = uuid.UUID("eeee0000-0000-0000-0000-000000000099")
        profile = service.select_preset(TENANT_A, "warm_close")

        new_dims = {
            "energy": 0.5,
            "warmth": 0.5,
            "humor": 0.5,
            "expressiveness": 0.5,
            "narrative": 0.5,
            "verbosity": 0.5,
        }
        result = service.update_dimensions(profile.id, other_tenant, new_dims)
        assert result is None
