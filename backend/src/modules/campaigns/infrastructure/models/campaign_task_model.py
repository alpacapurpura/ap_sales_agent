"""SQLAlchemy model for CampaignTask entity.

Performance-critical for worker queue polling at 1000+ tenants.
Partial index WHERE status IN ('pending','scheduled') is declared in the migration
(raw SQL) rather than here, since SQLAlchemy's partial index support requires
specific dialect handling. The UniqueConstraint for idempotency is also in migration.
"""

from __future__ import annotations

import datetime as dt
from uuid import UUID

from sqlalchemy import DateTime, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.domain.base_entity import Base


class CampaignTaskModel(Base):
    """SQLAlchemy 2.0 model for the campaign_task table.

    Worker queue performance critical — see migration 111 for partial index.
    """

    __tablename__ = "campaign_task"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    campaign_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    lead_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    step_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")

    scheduled_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    dispatched_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    channel_used: Mapped[str | None] = mapped_column(String(32), nullable=True)
    external_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    compliance_check: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    outbox_event_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(256), nullable=False)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        # Idempotency unique constraint (also in migration raw SQL for idempotency)
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_campaign_task_tenant_idem"),
        # Reporting index
        Index("ix_campaign_task_tenant_campaign_status", "tenant_id", "campaign_id", "status"),
        # Lead lookup
        Index("ix_campaign_task_lead", "lead_id"),
        # NOTE: Worker queue partial index ix_campaign_task_worker_queue
        # WHERE status IN ('pending','scheduled') is declared in migration raw SQL only
        # (SQLAlchemy partial index dialect-specific — migration is the SSoT for this).
    )
