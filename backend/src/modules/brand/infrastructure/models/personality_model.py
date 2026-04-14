"""PersonalityProfile SQLAlchemy model."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func, text

from src.shared.domain.base_entity import Base


class PersonalityProfileModel(Base):
    """SQLAlchemy model for personality_profiles table."""

    __tablename__ = "personality_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    offer_id = Column(UUID(as_uuid=True), nullable=True)
    avatar_id = Column(UUID(as_uuid=True), nullable=True)

    name = Column(String(255), nullable=False)
    profile_type = Column(String(20), nullable=False, default="preset")
    preset_key = Column(String(50), nullable=True)
    is_active = Column(Boolean, nullable=False, default=False)

    # Three pillars stored as JSONB
    dimensions = Column(JSONB, nullable=False, server_default=text("'{}'"))
    linguistic_patterns = Column(JSONB, nullable=False, server_default=text("'{}'"))
    sample_exchanges = Column(JSONB, nullable=False, server_default=text("'[]'"))
    negative_constraints = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # Compiled instruction
    system_instruction = Column(Text, nullable=True)

    # Provenance / metadata
    source_metadata = Column(JSONB, nullable=False, server_default=text("'{}'"))

    # Qdrant integration
    qdrant_collection = Column(String(100), nullable=True)
    anchor_count = Column(Integer, nullable=False, default=0)

    # LLM wiring
    llm_provider = Column(String(50), nullable=True)
    llm_model = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)
