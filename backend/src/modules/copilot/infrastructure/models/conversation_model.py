"""Copilot conversation SQLAlchemy model."""

import uuid

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class CopilotConversationModel(Base):
    """SQLAlchemy model for copilot conversation."""

    __tablename__ = "copilot_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    title = Column(String(255), nullable=True)
    messages = Column(JSONB, nullable=False, default=list)
    client_context = Column(JSONB, nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<CopilotConversation id={self.id} tenant={self.tenant_id}>"
