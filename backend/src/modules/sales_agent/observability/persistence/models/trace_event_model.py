"""SQLAlchemy model for ``sales_agent_trace_event``.

Mirror of the copilot trace-event row shape plus ``lead_id`` +
``channel_type``. Each row is one significant event inside a sales
turn: ``turn_start`` / ``turn_end`` / ``llm_call`` (mirror) /
``tool_call`` / ``node_enter`` / ``node_exit`` / ``error`` /
``domain_event``.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class SalesAgentTraceEventModel(Base):
    """ORM mapping for ``sales_agent_trace_event``."""

    __tablename__ = "sales_agent_trace_event"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    lead_id = Column(UUID(as_uuid=True), nullable=False)
    channel_type = Column(String(32), nullable=False)
    turn_id = Column(UUID(as_uuid=True), nullable=False)
    span_id = Column(UUID(as_uuid=True), nullable=False)
    parent_span_id = Column(UUID(as_uuid=True), nullable=True)

    event_type = Column(String(32), nullable=False)
    name = Column(String(128), nullable=True)
    data = Column(JSONB, nullable=False, default=dict)
    duration_ms = Column(Integer, nullable=True)
    status = Column(String(16), nullable=False, default="ok")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        """Return a debug-friendly summary."""
        return (
            f"<SalesAgentTraceEvent id={self.id} event_type={self.event_type} "
            f"lead_id={self.lead_id} status={self.status}>"
        )
