"""SQLAlchemy model for external product → internal offer mappings.

Maps products from external platforms (Shopify, Stripe, etc.) to internal
Offer IDs so webhooks and ETL can resolve which Offer a sale belongs to.
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class ExternalProductMappingModel(Base):
    """SQLAlchemy model for external product mapping table."""

    __tablename__ = "external_product_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    offer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.id"),
        nullable=False,
    )
    source = Column(String, nullable=False)  # "shopify", "stripe", ...
    external_id = Column(String, nullable=False)  # e.g. Shopify product_id
    external_name = Column(String, nullable=True)  # e.g. Shopify product title
    external_variant_id = Column(String, nullable=True)
    metadata_info = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "source",
            "external_id",
            name="uq_external_product_mapping_tenant_source_ext",
        ),
    )
