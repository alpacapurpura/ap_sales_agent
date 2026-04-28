"""SQLAlchemy model for ``sales_agent_routing_log``.

Mirror of ``copilot_routing_log`` plus ``lead_id`` + ``channel_type``
+ ``stage`` + ``lead_score``. One row per supervisor decision that
routes to a specialist (qualifier / product_expert / closer / escalate
/ tool_executor / respond).

Powered by the S4 ``sales-routing`` admin page.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class SalesAgentRoutingLogModel(Base):
    """ORM mapping for ``sales_agent_routing_log``."""

    __tablename__ = "sales_agent_routing_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    lead_id = Column(UUID(as_uuid=True), nullable=False)
    channel_type = Column(String(32), nullable=False)
    turn_id = Column(UUID(as_uuid=True), nullable=False)

    stage = Column(String(32), nullable=False)
    lead_score = Column(Integer, nullable=True)
    tier_selected = Column(Text, nullable=False)
    specialist_routed = Column(Text, nullable=False)
    reason = Column(Text, nullable=False)
    confidence = Column(Numeric(4, 3), nullable=True)
    user_msg_length = Column(Integer, nullable=False)
    tools_available = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
