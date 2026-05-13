"""Repository for asset ↔ entity links."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import structlog
from luana_core_assets.domain.entity import AssetLink
from luana_core_assets.infrastructure.models.asset_link_model import AssetLinkModel
from luana_core_platform.domain.datetime_utils import utc_now
from sqlalchemy import select

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

logger = structlog.get_logger()


class AssetLinkRepository:
    """Persist and query polymorphic links between assets and domain entities."""

    def __init__(self, db: Session) -> None:
        """Initialize."""
        self.db = db

    def _to_domain(self, model: AssetLinkModel) -> AssetLink:
        return AssetLink(
            id=model.id,
            tenant_id=model.tenant_id,
            asset_id=model.asset_id,
            entity_type=model.entity_type,
            entity_id=model.entity_id,
            role=model.role,
            created_at=model.created_at,
            deleted_at=model.deleted_at,
        )

    def create(
        self,
        *,
        tenant_id: UUID,
        asset_id: UUID,
        entity_type: str,
        entity_id: UUID,
        role: str,
    ) -> AssetLink:
        """Create a link — or re-use an existing active one (idempotent)."""
        existing = self._find_active(
            tenant_id=tenant_id,
            asset_id=asset_id,
            entity_type=entity_type,
            entity_id=entity_id,
            role=role,
        )
        if existing is not None:
            return self._to_domain(existing)

        model = AssetLinkModel(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            asset_id=asset_id,
            entity_type=entity_type,
            entity_id=entity_id,
            role=role,
        )
        self.db.add(model)
        self.db.flush()
        return self._to_domain(model)

    def list_for_asset(self, *, tenant_id: UUID, asset_id: UUID) -> list[AssetLink]:
        """All active links pointing to a given asset."""
        stmt = select(AssetLinkModel).where(
            AssetLinkModel.tenant_id == tenant_id,
            AssetLinkModel.asset_id == asset_id,
            AssetLinkModel.deleted_at.is_(None),
        )
        return [self._to_domain(m) for m in self.db.execute(stmt).scalars().all()]

    def list_for_entity(
        self,
        *,
        tenant_id: UUID,
        entity_type: str,
        entity_id: UUID,
        role: str | None = None,
    ) -> list[AssetLink]:
        """All active links pointing at a given domain entity, optionally by role."""
        stmt = select(AssetLinkModel).where(
            AssetLinkModel.tenant_id == tenant_id,
            AssetLinkModel.entity_type == entity_type,
            AssetLinkModel.entity_id == entity_id,
            AssetLinkModel.deleted_at.is_(None),
        )
        if role is not None:
            stmt = stmt.where(AssetLinkModel.role == role)
        return [self._to_domain(m) for m in self.db.execute(stmt).scalars().all()]

    def unlink(
        self,
        *,
        tenant_id: UUID,
        asset_id: UUID,
        entity_type: str,
        entity_id: UUID,
        role: str,
    ) -> bool:
        """Soft-delete a link. Returns True if a row was affected."""
        model = self._find_active(
            tenant_id=tenant_id,
            asset_id=asset_id,
            entity_type=entity_type,
            entity_id=entity_id,
            role=role,
        )
        if model is None:
            return False
        model.deleted_at = utc_now()
        self.db.flush()
        return True

    def _find_active(
        self,
        *,
        tenant_id: UUID,
        asset_id: UUID,
        entity_type: str,
        entity_id: UUID,
        role: str,
    ) -> AssetLinkModel | None:
        stmt = select(AssetLinkModel).where(
            AssetLinkModel.tenant_id == tenant_id,
            AssetLinkModel.asset_id == asset_id,
            AssetLinkModel.entity_type == entity_type,
            AssetLinkModel.entity_id == entity_id,
            AssetLinkModel.role == role,
            AssetLinkModel.deleted_at.is_(None),
        )
        return self.db.execute(stmt).scalars().first()
