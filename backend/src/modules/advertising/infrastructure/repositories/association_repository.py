"""Repository for AdOfferAssociationModel — advertising module internal."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.modules.advertising.domain.enums import (
    AssociationTargetType,
    AssociationType,
)
from src.modules.advertising.infrastructure.models.ad_offer_association_model import (
    AdOfferAssociationModel,
)


class AssociationRepository:
    """Data-access layer for ad_offer_associations."""

    def __init__(self, db: Session):
        self._db = db

    # ── Reads ────────────────────────────────────────────────────────────
    def list_active(
        self,
        tenant_id: UUID,
        target_type: AssociationTargetType | None = None,
        offer_id: UUID | None = None,
    ) -> list[AdOfferAssociationModel]:
        """Return all active (non-deleted) associations for a tenant."""
        stmt = select(AdOfferAssociationModel).where(
            AdOfferAssociationModel.tenant_id == tenant_id,
            AdOfferAssociationModel.deleted_at.is_(None),
        )
        if target_type is not None:
            stmt = stmt.where(AdOfferAssociationModel.target_type == target_type.value)
        if offer_id is not None:
            stmt = stmt.where(AdOfferAssociationModel.offer_id == offer_id)
        stmt = stmt.order_by(AdOfferAssociationModel.created_at.desc())
        result = self._db.execute(stmt)
        return list(result.scalars().all())

    def get_active_by_target(
        self,
        tenant_id: UUID,
        target_type: AssociationTargetType,
        target_external_id: str,
    ) -> AdOfferAssociationModel | None:
        """Return the currently active association for a specific target."""
        stmt = select(AdOfferAssociationModel).where(
            AdOfferAssociationModel.tenant_id == tenant_id,
            AdOfferAssociationModel.target_type == target_type.value,
            AdOfferAssociationModel.target_external_id == target_external_id,
            AdOfferAssociationModel.deleted_at.is_(None),
        )
        result = self._db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_id(
        self, tenant_id: UUID, association_id: UUID
    ) -> AdOfferAssociationModel | None:
        """Return association by id scoped to tenant (any status)."""
        stmt = select(AdOfferAssociationModel).where(
            AdOfferAssociationModel.id == association_id,
            AdOfferAssociationModel.tenant_id == tenant_id,
        )
        result = self._db.execute(stmt)
        return result.scalar_one_or_none()

    # ── Writes ───────────────────────────────────────────────────────────
    def create(
        self,
        *,
        tenant_id: UUID,
        target_type: AssociationTargetType,
        target_external_id: str,
        offer_id: UUID | None,
        association_type: AssociationType,
        confidence: str | None = None,
        notes: str | None = None,
    ) -> AdOfferAssociationModel:
        """Create a new association, soft-deleting any previous active one.

        Enforces the unique-per-active invariant application-side so the
        test SQLite dialect (which ignores partial indexes) behaves the
        same as PostgreSQL in production.
        """
        existing = self.get_active_by_target(tenant_id, target_type, target_external_id)
        if existing is not None:
            existing.deleted_at = datetime.now(timezone.utc)
            self._db.flush()

        new_row = AdOfferAssociationModel(
            id=uuid4(),
            tenant_id=tenant_id,
            provider="meta",
            target_type=target_type.value,
            target_external_id=target_external_id,
            offer_id=offer_id,
            association_type=association_type.value,
            confidence=confidence,
            notes=notes,
        )
        self._db.add(new_row)
        self._db.flush()
        self._db.refresh(new_row)
        return new_row

    def soft_delete(self, tenant_id: UUID, association_id: UUID) -> bool:
        """Soft-delete an association. Returns True if a row was updated."""
        stmt = (
            update(AdOfferAssociationModel)
            .where(
                AdOfferAssociationModel.id == association_id,
                AdOfferAssociationModel.tenant_id == tenant_id,
                AdOfferAssociationModel.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(timezone.utc))
        )
        result = self._db.execute(stmt)
        self._db.flush()
        return bool(result.rowcount)
