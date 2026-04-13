"""SQLAlchemy model for launch_editions table."""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class LaunchEditionModel(Base):
    """SQLAlchemy model for launch edition table."""

    __tablename__ = "launch_editions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offer_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)

    edition_name = Column(String, nullable=False)
    edition_number = Column(Integer, nullable=False)

    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    registration_start = Column(DateTime(timezone=True), nullable=True)
    registration_end = Column(DateTime(timezone=True), nullable=True)
    timezone = Column(String, default="UTC")

    pricing_override = Column(JSONB, nullable=True)
    capacity = Column(Integer, nullable=True)
    enrollment_count = Column(Integer, default=0)

    status = Column(String, default="draft")
    location_override = Column(JSONB, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
