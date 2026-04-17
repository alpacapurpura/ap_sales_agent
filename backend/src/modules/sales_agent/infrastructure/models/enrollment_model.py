"""SQLAlchemy model for the ``enrollments`` table (Phase 5)."""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class EnrollmentModel(Base):
    """SQLAlchemy model for enrollment persistence.

    Maps to :class:`src.modules.sales_agent.domain.enrollment.Enrollment`.
    Indexes are declared inline so the ``create_all`` codepath used by the
    test SQLite engine mirrors the production Postgres migration (048).
    """

    __tablename__ = "enrollments"
    __table_args__ = (
        Index("ix_enrollments_tenant", "tenant_id"),
        Index("ix_enrollments_offer", "tenant_id", "offer_id"),
        Index("ix_enrollments_edition", "tenant_id", "edition_id"),
        Index("ix_enrollments_contact", "tenant_id", "contact_id"),
        Index("ix_enrollments_status", "tenant_id", "status"),
        Index(
            "ix_enrollments_waitlist",
            "tenant_id",
            "offer_id",
            unique=False,
        ),
        Index("ix_enrollments_conversation", "conversation_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    offer_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    # Null when status == WAITLIST; FK without ondelete cascade so historical
    # rows are preserved if an edition is soft-cancelled.
    edition_id = Column(
        UUID(as_uuid=True),
        ForeignKey("launch_editions.id", ondelete="SET NULL"),
        nullable=True,
    )
    contact_id = Column(UUID(as_uuid=True), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), nullable=True)

    status = Column(String(32), nullable=False, default="intent", server_default="intent")

    pricing_tier_label = Column(String(64), nullable=True)
    pricing_amount = Column(Float, nullable=True)
    currency = Column(String(8), nullable=True)

    payment_provider = Column(String(32), nullable=True)
    payment_transaction_id = Column(String(256), nullable=True)
    payment_link_url = Column(Text, nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    source_channel = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)
    extra = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
