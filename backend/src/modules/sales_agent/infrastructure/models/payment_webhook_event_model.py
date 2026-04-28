"""Payment webhook idempotency log — S9.

Mirrors ``scheduler_webhook_event_model.py`` from S8.
Inbound payment webhook payloads land here once. The UNIQUE constraint
``(provider, external_id, event_type, occurred_at)`` enforces idempotency —
replays return ``200 duplicate`` without double-firing events.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class PaymentWebhookEventModel(Base):
    """Idempotency + audit row for one inbound payment webhook event."""

    __tablename__ = "payment_webhook_event"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    provider = Column(String(50), nullable=False)
    external_id = Column(String(255), nullable=False)
    event_type = Column(String(50), nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    payload = Column(JSONB, nullable=False, default=dict, server_default="{}")
    received_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "external_id",
            "event_type",
            "occurred_at",
            name="uq_payment_webhook_dedup",
        ),
        Index("ix_payment_webhook_tenant_received", "tenant_id", "received_at"),
    )
