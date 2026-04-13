"""SQLAlchemy model for BuyerPersona."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class BuyerPersonaModel(Base):
    """SQLAlchemy model mapping to the ``buyer_personas`` table."""

    __tablename__ = "buyer_personas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(255), nullable=False)
    tagline = Column(Text, nullable=True)
    scope = Column(String(20), nullable=False, default="GLOBAL")
    offer_id = Column(UUID(as_uuid=True), nullable=True)
    is_primary = Column(Boolean, nullable=False, default=False)

    # Profile fields (JSONB)
    demographics = Column(JSONB, nullable=False, default=dict)
    psychographics = Column(JSONB, nullable=False, default=dict)
    pain_points = Column(JSONB, nullable=False, default=list)
    desires = Column(JSONB, nullable=False, default=list)
    objections = Column(JSONB, nullable=False, default=list)
    preferred_channels = Column(JSONB, nullable=False, default=list)
    buyer_journey = Column(JSONB, nullable=False, default=dict)
    purchase_triggers = Column(JSONB, nullable=False, default=list)
    anti_patterns = Column(JSONB, nullable=False, default=list)

    # Metadata
    completeness_score = Column(Float, nullable=False, default=0.0)
    interview_session_id = Column(UUID(as_uuid=True), nullable=True)

    # Lifecycle
    is_active = Column(Boolean, nullable=False, default=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
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

    __table_args__ = (Index("ix_buyer_personas_tenant_scope", "tenant_id", "scope"),)
