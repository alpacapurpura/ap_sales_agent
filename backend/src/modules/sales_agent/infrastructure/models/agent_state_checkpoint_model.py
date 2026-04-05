import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from src.shared.domain.base_entity import Base


class AgentStateCheckpointModel(Base):
    """
    Persists the sales agent's accumulated state across conversation turns.

    Each active checkpoint represents the latest known state for a given
    tenant + lead pair.  When a session times out (6 h gap), the old
    checkpoint is soft-deactivated and a fresh one is created on the next
    interaction.
    """

    __tablename__ = "agent_state_checkpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    lead_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    customer_profile_id = Column(UUID(as_uuid=True), nullable=True)
    channel_type = Column(String(50), nullable=True)

    # Conversation State
    current_stage = Column(String(50), nullable=False, default="rapport")
    lead_score = Column(Integer, nullable=False, default=0)
    lead_data = Column(JSONB, nullable=False, default=dict)
    buying_signals = Column(JSONB, nullable=False, default=list)
    objection_history = Column(JSONB, nullable=False, default=list)
    qualification_answers = Column(JSONB, nullable=False, default=dict)
    turn_count = Column(Integer, nullable=False, default=0)
    last_specialist = Column(String(50), nullable=True)
    close_strategy = Column(String(50), nullable=True)
    metadata_info = Column(JSONB, nullable=True)

    # Closer Studio — handler control
    handler_mode = Column(String(20), nullable=False, default="ai")
    paused_at = Column(DateTime, nullable=True)
    paused_by = Column(UUID(as_uuid=True), nullable=True)
    resume_objective = Column(Text, nullable=True)

    # Closer Studio — frozen detection
    frozen_reason = Column(String(100), nullable=True)
    frozen_at = Column(DateTime, nullable=True)
    frozen_diagnosis = Column(JSONB, nullable=True)

    # Closer Studio — unread tracking
    last_human_message_at = Column(DateTime, nullable=True)
    unread_count = Column(Integer, nullable=False, default=0)

    # Lifecycle
    is_active = Column(Boolean, nullable=False, default=True)
    deleted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_checkpoint_tenant_lead_active", "tenant_id", "lead_id", "is_active"),
        Index("ix_checkpoint_handler_mode", "tenant_id", "handler_mode", "is_active"),
        Index("ix_checkpoint_frozen", "tenant_id", "frozen_at", "is_active"),
    )
