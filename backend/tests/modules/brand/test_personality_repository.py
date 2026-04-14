"""Tests for PersonalityProfileRepository — CRUD + tenant isolation."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from src.modules.brand.infrastructure.repositories.personality_repository import (
    PersonalityProfileRepository,
)
from tests.modules.conftest import TENANT_A, TENANT_B

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DEFAULT_DIMENSIONS = {
    "energy": 0.65,
    "warmth": 0.85,
    "humor": 0.6,
    "expressiveness": 0.7,
    "narrative": 0.5,
    "verbosity": 0.4,
}

_DEFAULT_LINGUISTIC = {
    "emoji_style": "frequent",
    "favorite_emojis": ["😊"],
    "greeting": "¡Hola!",
    "farewell": "¡Hasta pronto!",
    "filler_phrases": ["mira"],
    "avg_message_length": "short",
    "punctuation_style": "expressive",
    "humor_type": "playful",
    "unique_vocabulary": ["genial"],
}


def _create_profile(
    db: Session,
    *,
    tenant_id: uuid.UUID = TENANT_A,
    name: str = "Test Profile",
    profile_type: str = "preset",
    preset_key: str | None = "warm_close",
    dimensions: dict | None = None,
    linguistic_patterns: dict | None = None,
    sample_exchanges: list | None = None,
    negative_constraints: list | None = None,
    system_instruction: str | None = None,
):
    """Helper: persist a PersonalityProfileModel and return it."""
    repo = PersonalityProfileRepository(db)
    return repo.create(
        tenant_id=tenant_id,
        name=name,
        profile_type=profile_type,
        preset_key=preset_key,
        dimensions=dimensions or _DEFAULT_DIMENSIONS,
        linguistic_patterns=linguistic_patterns or _DEFAULT_LINGUISTIC,
        sample_exchanges=sample_exchanges or [],
        negative_constraints=negative_constraints or [],
        system_instruction=system_instruction,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPersonalityProfileRepository:
    """CRUD + tenant isolation tests for PersonalityProfileRepository."""

    # ------------------------------------------------------------------
    # create
    # ------------------------------------------------------------------

    def test_create_returns_model_with_correct_fields(self, db: Session) -> None:
        """create() persists a profile and returns a model with expected fields."""
        model = _create_profile(db, name="Warm Close", preset_key="warm_close")

        assert model.id is not None
        assert str(model.tenant_id) == str(TENANT_A)
        assert model.name == "Warm Close"
        assert model.profile_type == "preset"
        assert model.preset_key == "warm_close"
        assert model.is_active is False  # default
        assert model.deleted_at is None
        # JSONB fields stored and readable
        assert model.dimensions["energy"] == 0.65
        assert model.linguistic_patterns["emoji_style"] == "frequent"

    # ------------------------------------------------------------------
    # get_active — None when no active profile
    # ------------------------------------------------------------------

    def test_get_active_returns_none_when_no_active_profile(self, db: Session) -> None:
        """get_active() returns None when no profile is active for the tenant."""
        _create_profile(db)  # is_active defaults to False

        repo = PersonalityProfileRepository(db)
        result = repo.get_active(tenant_id=TENANT_A)

        assert result is None

    # ------------------------------------------------------------------
    # activate — deactivates other profiles for same tenant
    # ------------------------------------------------------------------

    def test_activate_deactivates_other_profiles(self, db: Session) -> None:
        """activate() sets target to active and all others for same tenant to inactive."""
        profile_a = _create_profile(db, name="Profile A")
        profile_b = _create_profile(db, name="Profile B")

        repo = PersonalityProfileRepository(db)
        repo.activate(profile_a.id, tenant_id=TENANT_A)

        active = repo.get_active(tenant_id=TENANT_A)
        assert active is not None
        assert str(active.id) == str(profile_a.id)

        # Activate B — A should be deactivated
        repo.activate(profile_b.id, tenant_id=TENANT_A)
        active_now = repo.get_active(tenant_id=TENANT_A)
        assert active_now is not None
        assert str(active_now.id) == str(profile_b.id)

        # A should now be inactive
        a_refreshed = repo.get_by_id(profile_a.id, tenant_id=TENANT_A)
        assert a_refreshed is not None
        assert a_refreshed.is_active is False

    # ------------------------------------------------------------------
    # soft_delete
    # ------------------------------------------------------------------

    def test_soft_delete_hides_profile_from_get_by_id(self, db: Session) -> None:
        """soft_delete() sets deleted_at; get_by_id returns None afterwards."""
        model = _create_profile(db, name="To Delete")

        repo = PersonalityProfileRepository(db)
        result = repo.soft_delete(model.id, tenant_id=TENANT_A)
        assert result is True

        not_found = repo.get_by_id(model.id, tenant_id=TENANT_A)
        assert not_found is None

    def test_soft_delete_nonexistent_returns_false(self, db: Session) -> None:
        """soft_delete() on a non-existent id returns False."""
        repo = PersonalityProfileRepository(db)
        assert repo.soft_delete(uuid.uuid4(), tenant_id=TENANT_A) is False

    # ------------------------------------------------------------------
    # tenant isolation
    # ------------------------------------------------------------------

    def test_get_by_id_tenant_isolation(self, db: Session) -> None:
        """get_by_id() returns None when queried with a different tenant_id."""
        model = _create_profile(db, tenant_id=TENANT_A)

        repo = PersonalityProfileRepository(db)
        # Correct tenant
        found = repo.get_by_id(model.id, tenant_id=TENANT_A)
        assert found is not None

        # Wrong tenant
        not_found = repo.get_by_id(model.id, tenant_id=TENANT_B)
        assert not_found is None

    def test_get_active_tenant_isolation(self, db: Session) -> None:
        """get_active() never leaks active profiles across tenants."""
        profile_a = _create_profile(db, tenant_id=TENANT_A)
        repo = PersonalityProfileRepository(db)
        repo.activate(profile_a.id, tenant_id=TENANT_A)

        # TENANT_B should have no active profile
        active_b = repo.get_active(tenant_id=TENANT_B)
        assert active_b is None

    # ------------------------------------------------------------------
    # update_dimensions
    # ------------------------------------------------------------------

    def test_update_dimensions_persists_changes(self, db: Session) -> None:
        """update_dimensions() patches dimensions, negative_constraints, and system_instruction."""
        model = _create_profile(db, name="Profile X")

        new_dimensions = {**_DEFAULT_DIMENSIONS, "energy": 0.95}
        new_constraints = ["NUNCA uses emojis.", "NUNCA uses exclamaciones."]
        new_instruction = "You are a calm, minimalist communicator."

        repo = PersonalityProfileRepository(db)
        updated = repo.update_dimensions(
            model.id,
            tenant_id=TENANT_A,
            dimensions=new_dimensions,
            negative_constraints=new_constraints,
            system_instruction=new_instruction,
        )

        assert updated is not None
        assert updated.dimensions["energy"] == 0.95
        assert len(updated.negative_constraints) == 2
        assert updated.system_instruction == new_instruction

    def test_update_dimensions_wrong_tenant_returns_none(self, db: Session) -> None:
        """update_dimensions() returns None when tenant_id does not match."""
        model = _create_profile(db, tenant_id=TENANT_A)

        repo = PersonalityProfileRepository(db)
        result = repo.update_dimensions(
            model.id,
            tenant_id=TENANT_B,
            dimensions=_DEFAULT_DIMENSIONS,
            negative_constraints=[],
            system_instruction=None,
        )
        assert result is None
