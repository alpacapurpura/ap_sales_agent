import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class LandingPageModel(Base):
    __tablename__ = "landing_pages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    offer_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=True)

    # slug is unique per-tenant (not globally). The DB-level constraint is a
    # partial unique index created in migration 024_fix_landing_pages_schema.
    slug = Column(String, nullable=False)
    config = Column(JSONB, default={})

    is_published = Column(Boolean, default=False)

    # Generation snapshot (offer header refactor — see CONTRACT 2026-04-11).
    # `is_outdated` is NOT stored — it's computed at read time as
    # `landing.generated_at < offer.updated_at` by the offer service.
    generated_at = Column(DateTime(timezone=True), nullable=True)
    offer_snapshot_version = Column(String, nullable=True)
    generation_job_id = Column(UUID(as_uuid=True), nullable=True)
    generation_job_status = Column(String, nullable=True)
    generation_error = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_landing_pages_tenant_id", "tenant_id"),
        Index("ix_landing_pages_deleted_at", "deleted_at"),
    )
