import uuid

from sqlalchemy import Column, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class AgentTrace(Base):
    __tablename__ = "agent_traces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Links (Loose coupling - No Foreign Keys to other modules)
    user_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )  # Generic User ID (maps to Lead ID)
    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    session_id = Column(String, nullable=True, index=True)
    node_name = Column(String, nullable=False)

    input_state = Column(JSONB, default=dict)
    output_state = Column(JSONB, default=dict)
    execution_time_ms = Column(Float, nullable=True)

    # RL / Feedback Loop
    action = Column(String, nullable=True)
    reward = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    llm_logs = relationship(
        "LLMLog",
        back_populates="trace",
        cascade="all, delete-orphan",
    )
