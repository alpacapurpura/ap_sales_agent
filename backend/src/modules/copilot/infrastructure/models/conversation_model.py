"""Copilot conversation SQLAlchemy model."""

import uuid
from datetime import timedelta

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base
from src.shared.domain.datetime_utils import utc_now

# Default retention period for conversation data (PII)
CONVERSATION_RETENTION_DAYS = 90


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
    expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        default=lambda: utc_now() + timedelta(days=CONVERSATION_RETENTION_DAYS),
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)
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

    # ── v2 columns (CONTRACT §1.1) ────────────────────────────────────────
    summary_updated_at = Column(DateTime(timezone=True), nullable=True)
    summary_dirty_at = Column(DateTime(timezone=True), nullable=True)
    message_count = Column(Integer, nullable=False, default=0, server_default="0")
    total_tokens = Column(Integer, nullable=False, default=0, server_default="0")
    last_tier_used = Column(String, nullable=True)
    title_auto_generated = Column(Boolean, nullable=False, default=False, server_default="false")
    archived_at = Column(DateTime(timezone=True), nullable=True)
    procedure_id = Column(UUID(as_uuid=True), nullable=True)
    procedure_state = Column(JSONB, nullable=True)
    plan_state = Column(JSONB, nullable=True)
    # F6 — unified workflow execution state (coexists with procedure_state
    # during cutover; see migration 071_copilot_workflow_state).
    workflow_state = Column(JSONB, nullable=True)

    # PI-5 PR-1 — Telegram channel support (D-PI5-007).
    # NULL = web (backward compat). 'telegram' = Telegram bot canal.
    channel_type = Column(String(32), nullable=True)
    channel_chat_id = Column(String(64), nullable=True)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<CopilotConversation id={self.id} tenant={self.tenant_id}>"
