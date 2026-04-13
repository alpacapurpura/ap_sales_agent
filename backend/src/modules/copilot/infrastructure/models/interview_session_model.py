"""SQLAlchemy model for interview_sessions table."""

import uuid

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class InterviewSessionModel(Base):
    __tablename__ = "interview_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    domain = Column(String(50), nullable=False, default="brand")
    config_snapshot = Column(JSONB, nullable=False, default=dict)
    conversation_id = Column(UUID(as_uuid=True), nullable=True)
    mapa_global = Column(JSONB, nullable=False, default=dict)
    bloque_actual = Column(String(100), nullable=False, default="")
    bloques_completados = Column(JSONB, nullable=False, default=list)
    status = Column(String(20), nullable=False, default="active")
    messages_count = Column(Integer, nullable=False, default=0)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<InterviewSessionModel id={self.id} tenant={self.tenant_id} domain={self.domain}>"
