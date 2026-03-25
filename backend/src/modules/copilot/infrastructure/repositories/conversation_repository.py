from typing import List, Optional
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.copilot.infrastructure.models.conversation_model import (
    CopilotConversationModel,
)

logger = structlog.get_logger()


class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        conversation_id: UUID,
        tenant_id: UUID,
        user_id: UUID,
        title: Optional[str] = None,
    ) -> CopilotConversationModel:
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
        self, conversation_id: UUID, tenant_id: UUID
    ) -> Optional[CopilotConversationModel]:
        stmt = select(CopilotConversationModel).where(
            CopilotConversationModel.id == conversation_id,
            CopilotConversationModel.tenant_id == tenant_id,
        )
        return self.db.execute(stmt).scalars().first()

    def append_messages(
        self,
        conversation_id: UUID,
        tenant_id: UUID,
        new_messages: list,
    ) -> None:
        conv = self.get_by_id(conversation_id, tenant_id)
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
        self, conversation_id: UUID, tenant_id: UUID, title: str
    ) -> None:
        conv = self.get_by_id(conversation_id, tenant_id)
        if conv:
            conv.title = title
            self.db.flush()

    def list_by_tenant_user(
        self,
        tenant_id: UUID,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> List[CopilotConversationModel]:
        stmt = (
            select(CopilotConversationModel)
            .where(
                CopilotConversationModel.tenant_id == tenant_id,
                CopilotConversationModel.user_id == user_id,
            )
            .order_by(CopilotConversationModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars().all())

    # ── Cross-tenant methods (admin) ─────────────────────────────────────

    def list_by_tenant(
        self,
        tenant_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> List[CopilotConversationModel]:
        """List conversations for a tenant (all users)."""
        stmt = (
            select(CopilotConversationModel)
            .where(CopilotConversationModel.tenant_id == tenant_id)
            .order_by(CopilotConversationModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_all_paginated(
        self,
        tenant_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[CopilotConversationModel]:
        """List conversations, optionally filtered by tenant."""
        stmt = (
            select(CopilotConversationModel)
            .order_by(CopilotConversationModel.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if tenant_id:
            stmt = stmt.where(CopilotConversationModel.tenant_id == tenant_id)
        return list(self.db.execute(stmt).scalars().all())

    def count_all(self, tenant_id: Optional[UUID] = None) -> int:
        """Count conversations, optionally filtered by tenant."""
        from sqlalchemy import func
        stmt = select(func.count()).select_from(CopilotConversationModel)
        if tenant_id:
            stmt = stmt.where(CopilotConversationModel.tenant_id == tenant_id)
        return self.db.execute(stmt).scalar() or 0

    def get_global_stats(self, days: int = 30) -> dict:
        """Global conversation stats for admin dashboard."""
        from sqlalchemy import func
        from datetime import datetime, timedelta, timezone

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        total = self.db.execute(
            select(func.count())
            .select_from(CopilotConversationModel)
            .where(CopilotConversationModel.created_at >= cutoff)
        ).scalar() or 0

        tenants_with_convs = self.db.execute(
            select(func.count(func.distinct(CopilotConversationModel.tenant_id)))
            .where(CopilotConversationModel.created_at >= cutoff)
        ).scalar() or 0

        return {
            "total": total,
            "tenants_with_conversations": tenants_with_convs,
        }
