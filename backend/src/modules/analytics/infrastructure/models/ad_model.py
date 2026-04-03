"""SQLAlchemy model for ads table."""

import uuid

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class AdModel(Base):
    __tablename__ = "ads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    provider = Column(String(50), nullable=False, default="meta")
    external_id = Column(String(255), nullable=False)
    campaign_external_id = Column(String(255), nullable=False)
    ad_set_external_id = Column(String(255), nullable=False)
    name = Column(String(500), nullable=False)
    status = Column(String(50))
    effective_status = Column(String(50))
    creative_id = Column(String(255))
    creative_thumbnail_url = Column(Text)
    creative_image_url = Column(Text)
    creative_video_id = Column(String(255))
    creative_title = Column(String(500))
    creative_body = Column(Text)
    creative_cta = Column(String(100))
    creative_link_url = Column(Text)
    preview_shareable_link = Column(Text)
    extra = Column(JSONB, server_default="{}")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))
