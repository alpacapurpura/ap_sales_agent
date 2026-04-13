"""Repository for BuyerPersona CRUD with tenant isolation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

from src.modules.brand.domain.buyer_persona import BuyerPersona
from src.modules.brand.infrastructure.models.buyer_persona_model import (
    BuyerPersonaModel,
)
from src.shared.domain.datetime_utils import utc_now


class BuyerPersonaRepository:
    """CRUD repository for BuyerPersona with mandatory tenant isolation."""

    def __init__(self, db: Session) -> None:
        """Initialize with a database session."""
        self.db = db

    def create(self, persona: BuyerPersona) -> BuyerPersona:
        """Persist a new BuyerPersona and return the validated entity."""
        db_model = BuyerPersonaModel(
            id=persona.id,
            tenant_id=persona.tenant_id,
            user_id=persona.user_id,
            name=persona.name,
            tagline=persona.tagline,
            scope=persona.scope,
            offer_id=persona.offer_id,
            is_primary=persona.is_primary,
            demographics=persona.demographics,
            psychographics=persona.psychographics,
            pain_points=persona.pain_points,
            desires=persona.desires,
            objections=persona.objections,
            preferred_channels=persona.preferred_channels,
            buyer_journey=persona.buyer_journey,
            purchase_triggers=persona.purchase_triggers,
            anti_patterns=persona.anti_patterns,
            completeness_score=persona.completeness_score,
            interview_session_id=persona.interview_session_id,
            is_active=persona.is_active,
        )
        self.db.add(db_model)
        self.db.commit()
        self.db.refresh(db_model)
        return BuyerPersona.model_validate(db_model)

    def get_by_id(self, tenant_id: UUID, persona_id: UUID) -> BuyerPersona | None:
        """Return a single persona by id, or ``None`` if not found."""
        stmt = select(BuyerPersonaModel).where(
            BuyerPersonaModel.tenant_id == tenant_id,
            BuyerPersonaModel.id == persona_id,
            BuyerPersonaModel.deleted_at.is_(None),
        )
        result = self.db.execute(stmt)
        model = result.scalars().first()
        if model:
            return BuyerPersona.model_validate(model)
        return None

    def list_by_tenant(
        self,
        tenant_id: UUID,
        scope: str | None = None,
    ) -> list[BuyerPersona]:
        """List active personas for a tenant, optionally filtered by scope."""
        stmt = select(BuyerPersonaModel).where(
            BuyerPersonaModel.tenant_id == tenant_id,
            BuyerPersonaModel.deleted_at.is_(None),
        )
        if scope:
            stmt = stmt.where(BuyerPersonaModel.scope == scope)
        result = self.db.execute(stmt)
        models = result.scalars().all()
        return [BuyerPersona.model_validate(m) for m in models]

    def update(
        self,
        tenant_id: UUID,
        persona_id: UUID,
        updates: dict,
    ) -> BuyerPersona | None:
        """Apply partial updates and return the refreshed entity."""
        stmt = select(BuyerPersonaModel).where(
            BuyerPersonaModel.tenant_id == tenant_id,
            BuyerPersonaModel.id == persona_id,
            BuyerPersonaModel.deleted_at.is_(None),
        )
        result = self.db.execute(stmt)
        model = result.scalars().first()
        if not model:
            return None

        for key, value in updates.items():
            if hasattr(model, key) and value is not None:
                setattr(model, key, value)

        self.db.commit()
        self.db.refresh(model)
        return BuyerPersona.model_validate(model)

    def soft_delete(self, tenant_id: UUID, persona_id: UUID) -> bool:
        """Soft-delete a persona by setting ``deleted_at``."""
        stmt = select(BuyerPersonaModel).where(
            BuyerPersonaModel.tenant_id == tenant_id,
            BuyerPersonaModel.id == persona_id,
            BuyerPersonaModel.deleted_at.is_(None),
        )
        result = self.db.execute(stmt)
        model = result.scalars().first()
        if not model:
            return False

        model.deleted_at = utc_now()
        self.db.commit()
        return True
