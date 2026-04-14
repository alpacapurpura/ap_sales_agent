"""Repository for PersonalityProfile CRUD with mandatory tenant isolation."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from src.modules.brand.infrastructure.models.personality_model import (
    PersonalityProfileModel,
)
from src.shared.domain.datetime_utils import utc_now

logger = structlog.get_logger()


class PersonalityProfileRepository:
    """CRUD repository for PersonalityProfile with mandatory tenant isolation.

    All public methods accept ``tenant_id`` and filter by it — no query ever
    returns data from another tenant.
    """

    def __init__(self, db: Session) -> None:
        """Initialize with a synchronous database session."""
        self.db = db

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def create(
        self,
        *,
        tenant_id: uuid.UUID,
        name: str,
        profile_type: str,
        dimensions: dict,
        linguistic_patterns: dict,
        sample_exchanges: list,
        negative_constraints: list,
        system_instruction: str | None = None,
        preset_key: str | None = None,
        source_metadata: dict | None = None,
        qdrant_collection: str | None = None,
        anchor_count: int = 0,
        llm_provider: str | None = None,
        llm_model: str | None = None,
    ) -> PersonalityProfileModel:
        """Persist a new PersonalityProfile and return the ORM model."""
        model = PersonalityProfileModel(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            name=name,
            profile_type=profile_type,
            preset_key=preset_key,
            is_active=False,
            dimensions=dimensions,
            linguistic_patterns=linguistic_patterns,
            sample_exchanges=sample_exchanges,
            negative_constraints=negative_constraints,
            system_instruction=system_instruction,
            source_metadata=source_metadata or {},
            qdrant_collection=qdrant_collection,
            anchor_count=anchor_count,
            llm_provider=llm_provider,
            llm_model=llm_model,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        logger.info(
            "personality_profile_created",
            tenant_id=str(tenant_id),
            profile_id=str(model.id),
            profile_type=profile_type,
        )
        return model

    def activate(self, profile_id: uuid.UUID, *, tenant_id: uuid.UUID) -> None:
        """Set target profile to active; deactivate all others for the same tenant.

        Only affects global profiles (offer_id IS NULL, avatar_id IS NULL).
        """
        # Deactivate all active profiles for this tenant (global scope)
        stmt_all = select(PersonalityProfileModel).where(
            PersonalityProfileModel.tenant_id == tenant_id,
            PersonalityProfileModel.is_active.is_(True),
            PersonalityProfileModel.offer_id.is_(None),
            PersonalityProfileModel.avatar_id.is_(None),
            PersonalityProfileModel.deleted_at.is_(None),
        )
        result = self.db.execute(stmt_all)
        for model in result.scalars().all():
            model.is_active = False

        # Activate target
        stmt_target = select(PersonalityProfileModel).where(
            PersonalityProfileModel.id == profile_id,
            PersonalityProfileModel.tenant_id == tenant_id,
            PersonalityProfileModel.deleted_at.is_(None),
        )
        result_target = self.db.execute(stmt_target)
        target = result_target.scalars().first()
        if target:
            target.is_active = True

        self.db.commit()
        logger.info(
            "personality_profile_activated",
            tenant_id=str(tenant_id),
            profile_id=str(profile_id),
        )

    def update_dimensions(
        self,
        profile_id: uuid.UUID,
        *,
        tenant_id: uuid.UUID,
        dimensions: dict,
        negative_constraints: list,
        system_instruction: str | None,
    ) -> PersonalityProfileModel | None:
        """Update dimensions, negative_constraints, and system_instruction.

        Returns ``None`` if the profile does not exist or belongs to a different tenant.
        """
        stmt = select(PersonalityProfileModel).where(
            PersonalityProfileModel.id == profile_id,
            PersonalityProfileModel.tenant_id == tenant_id,
            PersonalityProfileModel.deleted_at.is_(None),
        )
        result = self.db.execute(stmt)
        model = result.scalars().first()
        if not model:
            return None

        model.dimensions = dimensions
        model.negative_constraints = negative_constraints
        model.system_instruction = system_instruction

        self.db.commit()
        self.db.refresh(model)
        return model

    def soft_delete(self, profile_id: uuid.UUID, *, tenant_id: uuid.UUID) -> bool:
        """Soft-delete by setting ``deleted_at``.

        Returns ``True`` if the row was found and deleted, ``False`` otherwise.
        """
        stmt = select(PersonalityProfileModel).where(
            PersonalityProfileModel.id == profile_id,
            PersonalityProfileModel.tenant_id == tenant_id,
            PersonalityProfileModel.deleted_at.is_(None),
        )
        result = self.db.execute(stmt)
        model = result.scalars().first()
        if not model:
            return False

        model.deleted_at = utc_now()
        self.db.commit()
        logger.info(
            "personality_profile_soft_deleted",
            tenant_id=str(tenant_id),
            profile_id=str(profile_id),
        )
        return True

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_by_id(
        self,
        profile_id: uuid.UUID,
        *,
        tenant_id: uuid.UUID,
    ) -> PersonalityProfileModel | None:
        """Return a single profile by id scoped to tenant, excluding soft-deleted."""
        stmt = select(PersonalityProfileModel).where(
            PersonalityProfileModel.id == profile_id,
            PersonalityProfileModel.tenant_id == tenant_id,
            PersonalityProfileModel.deleted_at.is_(None),
        )
        result = self.db.execute(stmt)
        return result.scalars().first()

    def get_active(self, *, tenant_id: uuid.UUID) -> PersonalityProfileModel | None:
        """Return the currently active global profile for the tenant, or ``None``."""
        stmt = select(PersonalityProfileModel).where(
            PersonalityProfileModel.tenant_id == tenant_id,
            PersonalityProfileModel.is_active.is_(True),
            PersonalityProfileModel.offer_id.is_(None),
            PersonalityProfileModel.avatar_id.is_(None),
            PersonalityProfileModel.deleted_at.is_(None),
        )
        result = self.db.execute(stmt)
        return result.scalars().first()
