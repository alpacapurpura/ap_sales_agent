"""Message repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.sales_agent.domain.enums import MessageSender
from src.modules.sales_agent.domain.message import Message
from src.modules.sales_agent.infrastructure.models.message_model import MessageModel


class MessageRepository:
    """Repository for message persistence."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
        self.db = db

    def _to_domain(self, model: MessageModel) -> Message:
        return Message(
            id=model.id,
            tenant_id=model.tenant_id,
            lead_id=model.lead_id,
            sender_type=MessageSender(model.sender_type),
            content=model.content,
            channel=model.channel,
            external_id=model.external_id,
            metadata_info=model.metadata_info or {},
            created_at=model.created_at,
        )

    def _to_model(self, message: Message) -> MessageModel:
        return MessageModel(
            id=message.id,
            tenant_id=message.tenant_id,
            user_id=message.lead_id,  # Use actual column name
            role=message.sender_type.value,  # Use actual column name
            content=message.content,
            channel=message.channel,
            external_id=message.external_id,
            metadata_log=message.metadata_info,  # Use actual column name
        )

    def create(self, message: Message) -> Message:
        """Create."""
        model = self._to_model(message)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def get_history(
        self,
        lead_id: UUID,
        tenant_id: UUID,
        limit: int = 50,
    ) -> list[Message]:
        """Retrieve history."""
        models = (
            self.db.execute(
                select(MessageModel)
                .where(
                    MessageModel.user_id == lead_id,
                    MessageModel.tenant_id == tenant_id,
                )
                .order_by(MessageModel.created_at.asc())
                .limit(limit),
            )
            .scalars()
            .all()
        )
        return [self._to_domain(m) for m in models]
