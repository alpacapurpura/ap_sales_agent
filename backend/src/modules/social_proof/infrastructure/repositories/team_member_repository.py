"""Repository for TeamMember CRUD with mandatory tenant isolation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from pydantic import ValidationError
from sqlalchemy import select

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

from luana_core_platform.domain.datetime_utils import utc_now
from luana_core_social_proof.domain.team_member import TeamMember
from luana_core_social_proof.infrastructure.models.team_member_model import (
    TeamMemberModel,
)

logger = structlog.get_logger()


class TeamMemberRepository:
    """CRUD repository for TeamMember, tenant-scoped on every query."""

    def __init__(self, db: Session) -> None:
        """Store the database session for subsequent queries."""
        self.db = db

    def create(self, entity: TeamMember) -> TeamMember:
        """Persist and return the validated entity."""
        row = TeamMemberModel(
            id=entity.id,
            tenant_id=entity.tenant_id,
            user_id=entity.user_id,
            name=entity.name,
            role=entity.role,
            bio=entity.bio,
            headshot_url=entity.headshot_url,
            is_primary_voice=entity.is_primary_voice,
            gender=entity.gender,
            communication_style=entity.communication_style,
            personal_website=entity.personal_website,
            personal_linkedin=entity.personal_linkedin,
            personal_instagram=entity.personal_instagram,
            personal_tiktok=entity.personal_tiktok,
            personal_facebook=entity.personal_facebook,
            work_whatsapp=entity.work_whatsapp,
            gallery=entity.gallery,
            sort_order=entity.sort_order,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return TeamMember.model_validate(row)

    def get_by_id(self, tenant_id: UUID, entity_id: UUID) -> TeamMember | None:
        """Return a single entity by id, or ``None`` when not found."""
        stmt = select(TeamMemberModel).where(
            TeamMemberModel.tenant_id == tenant_id,
            TeamMemberModel.id == entity_id,
            TeamMemberModel.deleted_at.is_(None),
        )
        row = self.db.execute(stmt).scalars().first()
        return self._safe_validate(row) if row else None

    def list_by_tenant(self, tenant_id: UUID) -> list[TeamMember]:
        """List active entities for a tenant."""
        stmt = (
            select(TeamMemberModel)
            .where(
                TeamMemberModel.tenant_id == tenant_id,
                TeamMemberModel.deleted_at.is_(None),
            )
            .order_by(TeamMemberModel.sort_order.asc(), TeamMemberModel.created_at.asc())
        )
        rows = self.db.execute(stmt).scalars().all()
        return [v for v in (self._safe_validate(r) for r in rows) if v is not None]

    def list_by_ids(self, tenant_id: UUID, ids: list[UUID]) -> list[TeamMember]:
        """Batch-load entities by id for a tenant (used by the resolver)."""
        if not ids:
            return []
        stmt = select(TeamMemberModel).where(
            TeamMemberModel.tenant_id == tenant_id,
            TeamMemberModel.id.in_(ids),
            TeamMemberModel.deleted_at.is_(None),
        )
        rows = self.db.execute(stmt).scalars().all()
        return [v for v in (self._safe_validate(r) for r in rows) if v is not None]

    def update(
        self,
        tenant_id: UUID,
        entity_id: UUID,
        updates: dict,
    ) -> TeamMember | None:
        """Apply partial updates and return the refreshed entity."""
        stmt = select(TeamMemberModel).where(
            TeamMemberModel.tenant_id == tenant_id,
            TeamMemberModel.id == entity_id,
            TeamMemberModel.deleted_at.is_(None),
        )
        row = self.db.execute(stmt).scalars().first()
        if row is None:
            return None
        for key, value in updates.items():
            if hasattr(row, key):
                setattr(row, key, value)
        self.db.commit()
        self.db.refresh(row)
        return TeamMember.model_validate(row)

    def soft_delete(self, tenant_id: UUID, entity_id: UUID) -> bool:
        """Soft-delete by setting ``deleted_at``. Returns ``True`` on success."""
        stmt = select(TeamMemberModel).where(
            TeamMemberModel.tenant_id == tenant_id,
            TeamMemberModel.id == entity_id,
            TeamMemberModel.deleted_at.is_(None),
        )
        row = self.db.execute(stmt).scalars().first()
        if row is None:
            return False
        row.deleted_at = utc_now()
        self.db.commit()
        return True

    @staticmethod
    def _safe_validate(row: TeamMemberModel | None) -> TeamMember | None:
        if row is None:
            return None
        try:
            return TeamMember.model_validate(row)
        except ValidationError:
            logger.warning(
                "team_member.corrupt_row_skipped",
                team_member_id=str(row.id),
                tenant_id=str(row.tenant_id),
            )
            return None
