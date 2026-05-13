"""SQLAlchemy model for ad_offer_associations."""

import uuid

from luana_core_platform.domain.base_entity import Base
from sqlalchemy import Column, DateTime, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


class AdOfferAssociationModel(Base):
    """Association between a Meta target (campaign/ad set) and an Offer."""

    __tablename__ = "ad_offer_associations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    provider = Column(String(50), nullable=False, default="meta")

    # 'campaign' or 'ad_set' — supports CBO structures where ad sets own budget.
    target_type = Column(String(20), nullable=False)

    # external_id of ad_campaigns.external_id or ad_sets.external_id.
    target_external_id = Column(String(255), nullable=False)

    # Logical FK to products.id; NULL when association_type is "excluded_branding".
    offer_id = Column(UUID(as_uuid=True), nullable=True)

    # See AssociationType enum.
    association_type = Column(String(50), nullable=False)

    # 'high'|'medium'|'low' for auto-detected; NULL for manual/excluded.
    confidence = Column(String(20), nullable=True)

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # NOTE: the unique-per-active constraint lives only in the PostgreSQL
    # migration (partial index with `WHERE deleted_at IS NULL`). We do NOT
    # declare it unique at ORM level so SQLite (used by tests) does not
    # enforce a full-table unique, which would conflict with soft-deleted
    # rows still sharing the same (tenant_id, target_type, external_id).
    # The application layer (AssociationRepository.create) enforces the
    # invariant by soft-deleting the prior active row before inserting.
    __table_args__ = (
        Index(
            "ix_ad_offer_tenant_target",
            "tenant_id",
            "target_type",
            "target_external_id",
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index("ix_ad_offer_tenant_offer", "tenant_id", "offer_id"),
    )
