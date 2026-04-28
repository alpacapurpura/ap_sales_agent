"""Tests for PersonalityService — preset selection, get_active, update_dimensions, clone, activate, migrate."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from src.modules.brand.application.services.personality_service import PersonalityService
from tests.modules.conftest import TENANT_A

TENANT_B = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")

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


# ---------------------------------------------------------------------------
# Tests for service.activate() — new method, idempotent activation
# ---------------------------------------------------------------------------


class TestActivate:
    """activate() makes a profile active; idempotent; tenant-isolated."""

    def test_activate_first_time(self, service: PersonalityService) -> None:
        """activate() activates an inactive profile and returns it."""
        # Create a profile (preset creates inactive profile first, then activates)
        # We want a profile that is already inactive to test activate directly.
        profile = service.select_preset(TENANT_A, "serene")
        # Immediately deactivate it to test activate() in isolation
        from src.modules.brand.infrastructure.repositories.personality_repository import (
            PersonalityProfileRepository,
        )

        repo = PersonalityProfileRepository(service.db)
        profile_model = repo.get_by_id(profile.id, tenant_id=TENANT_A)
        assert profile_model is not None
        profile_model.is_active = False
        service.db.commit()

        # Now test activate
        result = service.activate(profile_id=profile.id, tenant_id=TENANT_A)
        assert result is not None
        assert result.is_active is True
        assert str(result.id) == str(profile.id)

    def test_activate_idempotent(self, service: PersonalityService) -> None:
        """Calling activate() on an already-active profile returns it unchanged."""
        profile = service.select_preset(TENANT_A, "direct")
        assert profile.is_active is True

        result = service.activate(profile_id=profile.id, tenant_id=TENANT_A)
        assert result is not None
        assert result.is_active is True
        assert str(result.id) == str(profile.id)

    def test_activate_deactivates_previous_active(self, service: PersonalityService) -> None:
        """activate() deactivates the previously active profile."""
        first = service.select_preset(TENANT_A, "warm_close")
        second = service.select_preset(TENANT_A, "electric")

        # second is now active, first is inactive
        # re-activate first
        result = service.activate(profile_id=first.id, tenant_id=TENANT_A)
        assert result is not None
        assert result.is_active is True

        # second should now be inactive
        from src.modules.brand.infrastructure.repositories.personality_repository import (
            PersonalityProfileRepository,
        )

        repo = PersonalityProfileRepository(service.db)
        second_refreshed = repo.get_by_id(second.id, tenant_id=TENANT_A)
        assert second_refreshed is not None
        assert second_refreshed.is_active is False

    def test_activate_wrong_tenant_returns_none(self, service: PersonalityService) -> None:
        """activate() returns None when profile belongs to a different tenant."""
        profile = service.select_preset(TENANT_A, "minimalist")

        result = service.activate(profile_id=profile.id, tenant_id=TENANT_B)
        assert result is None

    def test_activate_nonexistent_profile_returns_none(self, service: PersonalityService) -> None:
        """activate() returns None for a profile that does not exist."""
        result = service.activate(profile_id=uuid.uuid4(), tenant_id=TENANT_A)
        assert result is None


# ---------------------------------------------------------------------------
# Tests for service.clone_from_material() — LangGraph-driven clone pipeline
# ---------------------------------------------------------------------------


class TestCloneFromMaterial:
    """clone_from_material() runs pipeline, persists inactive profile."""

    @pytest.mark.asyncio
    async def test_clone_raises_value_error_if_both_inputs_empty(self, service: PersonalityService) -> None:
        """clone_from_material() raises ValueError when both text_input and file_bytes are None."""
        with pytest.raises(ValueError, match=r"text_input.*file_bytes|file_bytes.*text_input|input"):
            await service.clone_from_material(
                tenant_id=TENANT_A,
                text_input=None,
                file_bytes=None,
                file_name=None,
                user_name=None,
            )

    @pytest.mark.asyncio
    async def test_clone_raises_value_error_for_insufficient_messages(self, service: PersonalityService) -> None:
        """clone_from_material() raises ValueError when text has fewer than 10 messages."""
        few_messages = "\n".join([f"Mensaje {i}" for i in range(5)])
        with pytest.raises(ValueError, match=r"al menos 10|mensaje"):
            await service.clone_from_material(
                tenant_id=TENANT_A,
                text_input=few_messages,
                file_bytes=None,
                file_name=None,
                user_name=None,
            )

    @pytest.mark.asyncio
    async def test_clone_raises_value_error_when_both_text_and_file_provided(self, service: PersonalityService) -> None:
        """clone_from_material() raises ValueError when both text and file are provided."""
        text = "\n".join([f"Mensaje {i}" for i in range(15)])
        with pytest.raises(ValueError, match=r"texto.*archivo|archivo.*texto|ambos"):
            await service.clone_from_material(
                tenant_id=TENANT_A,
                text_input=text,
                file_bytes=b"some content",
                file_name="chat.txt",
                user_name=None,
            )

    @pytest.mark.asyncio
    async def test_clone_success_creates_inactive_profile(self, service: PersonalityService) -> None:
        """clone_from_material() creates an inactive profile on pipeline success."""
        # Mock the LangGraph pipeline
        mock_state = {
            "personality_dimensions": {
                "energy": 0.6,
                "warmth": 0.7,
                "humor": 0.5,
                "expressiveness": 0.5,
                "narrative": 0.4,
                "verbosity": 0.5,
            },
            "personality_linguistic_patterns": {
                "emoji_style": "moderate",
                "favorite_emojis": ["😊"],
                "greeting": "¡Hola!",
                "farewell": "¡Hasta pronto!",
                "filler_phrases": ["mira"],
                "avg_message_length": "medium",
                "punctuation_style": "standard",
                "humor_type": "natural",
                "unique_vocabulary": ["genial"],
            },
            "personality_sample_exchanges": [
                {
                    "context": "greeting",
                    "other_message": "Hola",
                    "author_response": "¡Hola! 😊",
                }
            ],
            "personality_confidence": 0.8,
            "system_instruction": "BLOQUE 1 — test instruction",
            "error": None,
        }

        text = "\n".join([f"Mensaje de ejemplo número {i}" for i in range(15)])

        with patch("src.modules.brand.application.services.personality_service.personality_app") as mock_app:
            mock_app.ainvoke = AsyncMock(return_value=mock_state)

            profile = await service.clone_from_material(
                tenant_id=TENANT_A,
                text_input=text,
                file_bytes=None,
                file_name=None,
                user_name="Test User",
            )

        assert profile is not None
        assert profile.is_active is False
        assert profile.profile_type == "cloned"
        assert str(profile.tenant_id) == str(TENANT_A)

    @pytest.mark.asyncio
    async def test_clone_pipeline_failure_raises_runtime_error(self, service: PersonalityService) -> None:
        """clone_from_material() raises RuntimeError when pipeline returns error state."""
        text = "\n".join([f"Mensaje {i}" for i in range(15)])

        mock_state = {"error": "LLM timeout", "personality_dimensions": None}

        with patch("src.modules.brand.application.services.personality_service.personality_app") as mock_app:
            mock_app.ainvoke = AsyncMock(return_value=mock_state)

            with pytest.raises(RuntimeError, match=r"pipeline|analizar"):
                await service.clone_from_material(
                    tenant_id=TENANT_A,
                    text_input=text,
                    file_bytes=None,
                    file_name=None,
                    user_name=None,
                )


# ---------------------------------------------------------------------------
# Tests for service.migrate_from_voice_tone() — legacy voice_tone → preset mapping
# ---------------------------------------------------------------------------


class TestMigrateFromVoiceTone:
    """migrate_from_voice_tone() maps legacy voice_tone text to a PersonalityProfile."""

    @pytest.mark.asyncio
    async def test_migrate_raises_value_error_for_empty_text(self, service: PersonalityService) -> None:
        """migrate_from_voice_tone() raises ValueError for empty input."""
        with pytest.raises(ValueError, match=r"vacío|empty|voice_tone"):
            await service.migrate_from_voice_tone(
                tenant_id=TENANT_A,
                voice_tone_text="",
            )

    @pytest.mark.asyncio
    async def test_migrate_success_creates_migrated_profile(self, service: PersonalityService) -> None:
        """migrate_from_voice_tone() creates an active profile with correct metadata."""
        voice_tone = "Soy muy cálida, cercana, con humor ligero y mucho entusiasmo genuino."

        with patch("src.modules.brand.application.services.personality_service.find_nearest_preset") as mock_find:
            mock_find.return_value = ("warm_close", 0.85)

            profile, preset_key, confidence = await service.migrate_from_voice_tone(
                tenant_id=TENANT_A,
                voice_tone_text=voice_tone,
            )

        assert profile is not None
        assert profile.profile_type == "migrated_from_voice_tone"
        assert profile.source_metadata.get("legacy_text") == voice_tone
        assert profile.is_active is True
        assert preset_key == "warm_close"
        assert 0.0 <= confidence <= 1.0

    @pytest.mark.asyncio
    async def test_migrate_no_preset_match_still_creates_profile(self, service: PersonalityService) -> None:
        """migrate_from_voice_tone() creates profile even when no preset matches (None confidence)."""
        voice_tone = "Tono de voz muy específico sin match claro"

        with patch("src.modules.brand.application.services.personality_service.find_nearest_preset") as mock_find:
            mock_find.return_value = (None, 0.0)

            profile, preset_key, confidence = await service.migrate_from_voice_tone(
                tenant_id=TENANT_A,
                voice_tone_text=voice_tone,
            )

        assert profile is not None
        assert profile.profile_type == "migrated_from_voice_tone"
        assert preset_key is None
        assert confidence == 0.0
