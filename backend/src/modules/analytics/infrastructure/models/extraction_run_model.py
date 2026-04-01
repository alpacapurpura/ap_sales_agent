"""Extraction run table — tracks each ETL extraction execution."""

import uuid

from sqlalchemy import Column, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class ExtractionRunModel(Base):
    __tablename__ = "extraction_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    provider = Column(String, nullable=False)
    status = Column(String, nullable=False, server_default="pending")

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    error = Column(Text, nullable=True)
    metrics_count = Column(Integer, server_default="0")
    duration_seconds = Column(Float, nullable=True)
    rows_extracted = Column(Integer, server_default="0")
    rate_limit_headroom = Column(Float, nullable=True)
    sub_extractor_failures = Column(JSONB, server_default="[]")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index(
            "ix_extraction_tenant_provider_status",
            "tenant_id",
            "provider",
            "status",
        ),
    )
