"""SQLAlchemy model for the copilot trace-event table.

Each row is one observable event inside a ``/copilot/chat`` turn. See the
migration (``059_copilot_trace_event``) for the event-type catalog and the
recorder service (``application/observability/trace_recorder.py``) for the
write path.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class CopilotTraceEventModel(Base):
    """SQLAlchemy model mapping to the ``copilot_trace_event`` table."""

    __tablename__ = "copilot_trace_event"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    conversation_id = Column(UUID(as_uuid=True), nullable=True)
    message_id = Column(UUID(as_uuid=True), nullable=True)
    turn_id = Column(UUID(as_uuid=True), nullable=False)
    span_id = Column(UUID(as_uuid=True), nullable=False)
    parent_span_id = Column(UUID(as_uuid=True), nullable=True)
    event_type = Column(String(32), nullable=False)
    name = Column(String(128), nullable=True)
    data = Column(JSONB, nullable=False, default=dict)
    duration_ms = Column(Integer, nullable=True)
    status = Column(String(16), nullable=False, default="ok")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        Index("ix_copilot_trace_event_conversation", "conversation_id", "created_at"),
        Index("ix_copilot_trace_event_turn", "turn_id", "created_at"),
        Index("ix_copilot_trace_event_tenant_time", "tenant_id", "created_at"),
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<CopilotTraceEvent id={self.id} type={self.event_type} status={self.status}>"
