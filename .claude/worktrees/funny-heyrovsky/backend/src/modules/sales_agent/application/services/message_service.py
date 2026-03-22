from typing import List
from sqlalchemy.orm import Session
from uuid import UUID
from src.modules.sales_agent.domain.message import Message
from src.modules.sales_agent.domain.enums import MessageSender
from src.modules.sales_agent.infrastructure.repositories.message_repository import MessageRepository
 
class MessageService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = MessageRepository(db)

    def save_message(self, content: str, sender: MessageSender, lead_id: UUID, tenant_id: UUID, channel: str = None, metadata: dict = None) -> Message:
        import uuid
        new_message = Message(
            id=uuid.uuid4(),
            content=content,
            sender_type=sender,
            lead_id=lead_id,
            tenant_id=tenant_id,
            channel=channel,
            metadata_info=metadata or {}
        )
        return self.repository.create(new_message)

    def get_history(self, lead_id: UUID, limit: int = 50) -> List[Message]:
        return self.repository.get_history(lead_id, limit)
