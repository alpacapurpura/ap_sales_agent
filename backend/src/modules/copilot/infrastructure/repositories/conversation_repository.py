"""Copilot conversation repository."""

from datetime import UTC
from uuid import UUID

import structlog
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.modules.copilot.infrastructure.models.conversation_model import (
    CopilotConversationModel,
)
from src.shared.domain.datetime_utils import utc_now

logger = structlog.get_logger()


class ConversationRepository:
    """Repository for conversation persistence."""

    def __init__(self, db: Session) -> None:
        """Initialize conversation repository."""
        self.db = db

    def create(
        self,
        *,
        conversation_id: UUID,
        tenant_id: UUID,
        user_id: UUID,
        title: str | None = None,
    ) -> CopilotConversationModel:
        """Execute create operation."""
        conv = CopilotConversationModel(
            id=conversation_id,
            tenant_id=tenant_id,
            user_id=user_id,
            title=title,
            messages=[],
        )
        self.db.add(conv)
        self.db.flush()
        return conv

    def get_by_id(
        self,
        conversation_id: UUID,
        tenant_id: UUID,
        user_id: UUID | None = None,
    ) -> CopilotConversationModel | None:
        """Return by id, filtered by tenant and optionally by user.

        When user_id is provided, acts as an ownership check — prevents
        cross-user conversation access within the same tenant.
        """
        conditions = [
            CopilotConversationModel.id == conversation_id,
            CopilotConversationModel.tenant_id == tenant_id,
            CopilotConversationModel.deleted_at.is_(None),
        ]
        if user_id is not None:
            conditions.append(CopilotConversationModel.user_id == user_id)

        stmt = select(CopilotConversationModel).where(*conditions)
        return self.db.execute(stmt).scalars().first()

    def append_messages(
        self,
        conversation_id: UUID,
        tenant_id: UUID,
        new_messages: list,
        *,
        user_id: UUID | None = None,
    ) -> None:
        """Execute append messages operation.

        When user_id is provided, validates ownership before appending.
        """
        conv = self.get_by_id(conversation_id, tenant_id, user_id)
        if not conv:
            logger.warning(
                "conversation_not_found",
                conversation_id=str(conversation_id),
                tenant_id=str(tenant_id),
            )
            return
        existing = list(conv.messages or [])
        existing.extend(new_messages)
        conv.messages = existing
        self.db.flush()

    def update_title(
        self,
        conversation_id: UUID,
        tenant_id: UUID,
        title: str,
        *,
        user_id: UUID | None = None,
    ) -> None:
        """Update title, validating ownership when user_id is provided."""
        conv = self.get_by_id(conversation_id, tenant_id, user_id)
        if conv:
            conv.title = title
            self.db.flush()

    def list_by_tenant_user(
        self,
        tenant_id: UUID,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[CopilotConversationModel]:
        """List by tenant user."""
        stmt = (
            select(CopilotConversationModel)
            .where(
                CopilotConversationModel.tenant_id == tenant_id,
                CopilotConversationModel.user_id == user_id,
                CopilotConversationModel.deleted_at.is_(None),
            )
            .order_by(CopilotConversationModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars().all())

    def cleanup_expired_conversations(self) -> int:
        """Soft-delete conversations past their expires_at.

        Returns the number of soft-deleted rows.
        Uses bulk UPDATE for efficiency — no need to load rows into memory.
        """
        now = utc_now()
        stmt = (
            update(CopilotConversationModel)
            .where(
                CopilotConversationModel.expires_at.isnot(None),
                CopilotConversationModel.expires_at <= now,
                CopilotConversationModel.deleted_at.is_(None),
            )
            .values(deleted_at=now)
        )
        result = self.db.execute(stmt)
        return result.rowcount

    # ── Cross-tenant methods (admin) ─────────────────────────────────────

    def list_by_tenant(
        self,
        tenant_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[CopilotConversationModel]:
        """List conversations for a tenant (all users)."""
        stmt = (
            select(CopilotConversationModel)
            .where(
                CopilotConversationModel.tenant_id == tenant_id,
                CopilotConversationModel.deleted_at.is_(None),
            )
            .order_by(CopilotConversationModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_all_paginated(
        self,
        tenant_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CopilotConversationModel]:
        """List conversations, optionally filtered by tenant."""
        stmt = (
            select(CopilotConversationModel)
            .where(CopilotConversationModel.deleted_at.is_(None))
            .order_by(CopilotConversationModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if tenant_id:
            stmt = stmt.where(CopilotConversationModel.tenant_id == tenant_id)
        return list(self.db.execute(stmt).scalars().all())

    def count_all(self, tenant_id: UUID | None = None) -> int:
        """Count conversations, optionally filtered by tenant."""
        from sqlalchemy import func

        stmt = (
            select(func.count())
            .select_from(CopilotConversationModel)
            .where(
                CopilotConversationModel.deleted_at.is_(None),
            )
        )
        if tenant_id:
            stmt = stmt.where(CopilotConversationModel.tenant_id == tenant_id)
        return self.db.execute(stmt).scalar() or 0

    def get_global_stats(self, days: int = 30) -> dict:
        """Global conversation stats for admin dashboard."""
        from datetime import datetime, timedelta

        from sqlalchemy import func

        cutoff = datetime.now(UTC) - timedelta(days=days)

        total = (
            self.db.execute(
                select(func.count())
                .select_from(CopilotConversationModel)
                .where(
                    CopilotConversationModel.created_at >= cutoff,
                    CopilotConversationModel.deleted_at.is_(None),
                ),
            ).scalar()
            or 0
        )

        tenants_with_convs = (
            self.db.execute(
                select(
                    func.count(func.distinct(CopilotConversationModel.tenant_id)),
                ).where(
                    CopilotConversationModel.created_at >= cutoff,
                    CopilotConversationModel.deleted_at.is_(None),
                ),
            ).scalar()
            or 0
        )

        return {
            "total": total,
            "tenants_with_conversations": tenants_with_convs,
        }
