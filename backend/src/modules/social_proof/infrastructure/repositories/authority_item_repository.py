"""Repository for AuthorityItem CRUD with mandatory tenant isolation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from pydantic import ValidationError
from sqlalchemy import select

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

from src.modules.social_proof.domain.authority_item import AuthorityItem
from src.modules.social_proof.infrastructure.models.authority_item_model import (
    AuthorityItemModel,
)
from src.shared.domain.datetime_utils import utc_now

logger = structlog.get_logger()


class AuthorityItemRepository:
    """CRUD repository for AuthorityItem, tenant-scoped on every query."""

    def __init__(self, db: Session) -> None:
        """Store the database session for subsequent queries."""
        self.db = db

    def create(self, entity: AuthorityItem) -> AuthorityItem:
        """Persist and return the validated entity."""
        row = AuthorityItemModel(
            id=entity.id,
            tenant_id=entity.tenant_id,
            user_id=entity.user_id,
            entity_name=entity.entity_name,
            authority_type=entity.authority_type.value,
            context=entity.context,
            proof_url=entity.proof_url,
            logo_url=entity.logo_url,
            obtained_at=entity.obtained_at,
            expires_at=entity.expires_at,
            is_active=entity.is_active,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return AuthorityItem.model_validate(row)

    def get_by_id(self, tenant_id: UUID, entity_id: UUID) -> AuthorityItem | None:
        """Return a single entity by id, or ``None`` when not found."""
        stmt = select(AuthorityItemModel).where(
            AuthorityItemModel.tenant_id == tenant_id,
            AuthorityItemModel.id == entity_id,
            AuthorityItemModel.deleted_at.is_(None),
        )
        row = self.db.execute(stmt).scalars().first()
        return self._safe_validate(row) if row else None

    def list_by_tenant(
        self,
        tenant_id: UUID,
        *,
        active_only: bool = True,
    ) -> list[AuthorityItem]:
        """List active entities for a tenant."""
        stmt = select(AuthorityItemModel).where(
            AuthorityItemModel.tenant_id == tenant_id,
            AuthorityItemModel.deleted_at.is_(None),
        )
        if active_only:
            stmt = stmt.where(AuthorityItemModel.is_active.is_(True))
        stmt = stmt.order_by(AuthorityItemModel.created_at.desc())
        rows = self.db.execute(stmt).scalars().all()
        return [v for v in (self._safe_validate(r) for r in rows) if v is not None]

    def list_by_ids(self, tenant_id: UUID, ids: list[UUID]) -> list[AuthorityItem]:
        """Batch-load entities by id for a tenant (used by the resolver)."""
        if not ids:
            return []
        stmt = select(AuthorityItemModel).where(
            AuthorityItemModel.tenant_id == tenant_id,
            AuthorityItemModel.id.in_(ids),
            AuthorityItemModel.deleted_at.is_(None),
        )
        rows = self.db.execute(stmt).scalars().all()
        return [v for v in (self._safe_validate(r) for r in rows) if v is not None]

    def update(
        self,
        tenant_id: UUID,
        entity_id: UUID,
        updates: dict,
    ) -> AuthorityItem | None:
        """Apply partial updates and return the refreshed entity."""
        stmt = select(AuthorityItemModel).where(
            AuthorityItemModel.tenant_id == tenant_id,
            AuthorityItemModel.id == entity_id,
            AuthorityItemModel.deleted_at.is_(None),
        )
        row = self.db.execute(stmt).scalars().first()
        if row is None:
            return None
        for key, value in updates.items():
            if hasattr(row, key):
                setattr(row, key, value)
        self.db.commit()
        self.db.refresh(row)
        return AuthorityItem.model_validate(row)

    def soft_delete(self, tenant_id: UUID, entity_id: UUID) -> bool:
        """Soft-delete by setting ``deleted_at``. Returns ``True`` on success."""
        stmt = select(AuthorityItemModel).where(
            AuthorityItemModel.tenant_id == tenant_id,
            AuthorityItemModel.id == entity_id,
            AuthorityItemModel.deleted_at.is_(None),
        )
        row = self.db.execute(stmt).scalars().first()
        if row is None:
            return False
        row.deleted_at = utc_now()
        self.db.commit()
        return True

    @staticmethod
    def _safe_validate(row: AuthorityItemModel | None) -> AuthorityItem | None:
        if row is None:
            return None
        try:
            return AuthorityItem.model_validate(row)
        except ValidationError:
            logger.warning(
                "authority_item.corrupt_row_skipped",
                authority_item_id=str(row.id),
                tenant_id=str(row.tenant_id),
            )
            return None
