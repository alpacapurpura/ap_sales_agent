"""Message SQLAlchemy model."""

import uuid as uuid_mod
from typing import Any

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class MessageModel(Base):
    """SQLAlchemy model for message table."""

    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_mod.uuid4)
    user_id = Column(
        "user_id",
        UUID(as_uuid=True),
        ForeignKey("leads.id"),
        nullable=True,
        index=True,
    )
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    role = Column("role", String, nullable=False)  # user / assistant / system
    content = Column(Text, nullable=False)
    channel = Column(String, nullable=True)  # whatsapp / telegram
    sender_source = Column(
        String(20),
        nullable=False,
        server_default="auto",
    )  # auto / human_direct / human_instruction
    product_context_id = Column(UUID(as_uuid=True), nullable=True)
    external_id = Column(
        String,
        nullable=True,
    )  # Message ID from channel (e.g. ManyChat)

    metadata_log = Column("metadata_log", JSONB, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    lead = relationship("LeadModel", back_populates="messages", foreign_keys=[user_id])

    # Aliases for backward compatibility with code using old names
    @property
    def lead_id(self) -> uuid_mod.UUID | None:
        """Lead id."""
        return self.user_id

    @property
    def sender_type(self) -> str | None:
        """Sender type."""
        return self.role

    @property
    def metadata_info(self) -> dict[str, Any] | None:
        """Metadata info."""
        return self.metadata_log
