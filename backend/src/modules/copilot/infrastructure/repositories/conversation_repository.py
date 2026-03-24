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
