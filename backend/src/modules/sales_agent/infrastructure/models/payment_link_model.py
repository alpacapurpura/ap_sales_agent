"""Payment link SA model — S9.

One row per payment link the agent creates for a lead.
Status transitions: pending → paid / failed / cancelled / expired / refunded.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class PaymentLinkModel(Base):
    """Persistent record of a payment link issued by sales_agent."""

    __tablename__ = "payment_link"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    lead_id = Column(UUID(as_uuid=True), nullable=False)
    offer_id = Column(UUID(as_uuid=True), nullable=False)
    provider = Column(String(50), nullable=False)
    external_id = Column(String(255), nullable=False)
    url = Column(String(2048), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    metadata_ = Column("metadata", JSONB, nullable=False, default=dict, server_default="{}")
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
    expires_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "provider",
            "external_id",
            name="uq_payment_link_provider_external",
        ),
        Index("ix_payment_link_tenant_lead", "tenant_id", "lead_id"),
    )
