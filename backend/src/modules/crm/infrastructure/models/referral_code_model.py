"""Referral code model for evangelist referral tracking."""

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class ReferralCodeModel(Base):
    __tablename__ = "referral_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customer_profiles.id"),
        nullable=False,
        index=True,
    )
    code = Column(String, nullable=False, unique=True, index=True)
    source = Column(String, default="internal")  # "internal" | "shopify" | "external"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("ix_referral_codes_tenant_customer", "tenant_id", "customer_id"),
    )
