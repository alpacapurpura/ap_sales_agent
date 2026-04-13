"""Prompt Version SQLAlchemy model."""

import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class PromptVersion(Base):
    """Prompt Version."""

    __tablename__ = "prompt_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String, index=True, nullable=False)
    version = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)  # The actual prompt template
    is_active = Column(Boolean, default=True)
    change_reason = Column(String, nullable=True)
    author_id = Column(String, nullable=True)  # User ID or 'system'
    metadata_info = Column(JSONB, default=dict)  # target_node, target_model, etc.

    created_at = Column(DateTime(timezone=True), server_default=func.now())
