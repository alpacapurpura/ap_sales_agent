"""Scheduler webhook idempotency log + audit (S8).

Inbound webhook payloads from external scheduler providers (Cal.com /
Calendly / Google Calendar push) land here once before fanning out to
domain events. The natural-key UNIQUE on
``(provider, tracking_id, event_type, occurred_at)`` enforces
idempotency at the DB layer — replays return ``200 duplicate`` from the
endpoint without firing new events.

Internal scheduler does NOT hit this table — its bookings come via own
endpoints + ``AppointmentEvent`` directly.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class SchedulerWebhookEventModel(Base):
    """Idempotency + audit row for one inbound scheduler webhook event."""

    __tablename__ = "scheduler_webhook_event"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(String(50), nullable=False)
    tracking_id = Column(String(255), nullable=True)
    event_type = Column(String(50), nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    lead_id = Column(UUID(as_uuid=True), nullable=True)
    payload_raw = Column(JSONB, nullable=False)
    received_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "tracking_id",
            "event_type",
            "occurred_at",
            name="uq_scheduler_webhook_dedup",
        ),
        Index("ix_scheduler_webhook_tenant", "tenant_id", "received_at"),
    )
