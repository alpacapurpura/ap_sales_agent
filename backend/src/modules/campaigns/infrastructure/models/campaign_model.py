"""SQLAlchemy model for Campaign entity."""

from __future__ import annotations

import datetime as dt
from uuid import UUID

from sqlalchemy import DateTime, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.domain.base_entity import Base


class CampaignModel(Base):
    """SQLAlchemy 2.0 model for the campaign table."""

    __tablename__ = "campaign"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    campaign_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")

    segment_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    segment_snapshot_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    channel_priority: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    offer_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    brand_summary_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)

    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    scheduled_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    launched_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by_user_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    created_by_source: Mapped[str] = mapped_column(String(32), nullable=False, default="api")

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_campaign_tenant_status", "tenant_id", "status"),
        Index("ix_campaign_tenant_scheduled", "tenant_id", "scheduled_at"),
        Index("ix_campaign_tenant_created", "tenant_id", "created_at"),
        Index("ix_campaign_segment", "segment_id"),
    )
