"""SQLAlchemy model for ad_recommendations table."""

import uuid

from sqlalchemy import Column, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class AdRecommendationModel(Base):
    """SQLAlchemy model for ad recommendation."""

    __tablename__ = "ad_recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    provider = Column(String(50), nullable=False, default="meta")
    source = Column(String(50), nullable=False, default="account")
    recommendation_type = Column(String(100), nullable=False)
    object_ids = Column(JSONB, server_default="[]")
    title = Column(String(500))
    body = Column(Text)
    blame_field = Column(String(100))
    importance = Column(String(20))
    confidence = Column(String(20))
    lift_estimate = Column(String(100))
    opportunity_score = Column(Float)
    url = Column(Text)
    recommendation_signature = Column(String(500))
    extra = Column(JSONB, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))
