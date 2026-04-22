"""RoutingLogModel — SQLAlchemy model for copilot_routing_log table."""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class RoutingLogModel(Base):
    """One row per user-initiated chat request — records which tier was selected."""

    __tablename__ = "copilot_routing_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    message_id = Column(UUID(as_uuid=True), nullable=False)
    tier_selected = Column(String, nullable=False)
    classifier_used = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    confidence = Column(Numeric(4, 3), nullable=True)
    user_msg_length = Column(Integer, nullable=False)
    tools_available = Column(Integer, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<RoutingLog id={self.id} tier={self.tier_selected} tenant={self.tenant_id}>"
