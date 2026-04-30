"""SQLAlchemy model for SegmentSnapshot entity."""

from __future__ import annotations

import datetime as dt
from uuid import UUID

from sqlalchemy import DateTime, Index, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.domain.base_entity import Base


class SegmentSnapshotModel(Base):
    """SQLAlchemy 2.0 model for the segment_snapshot table."""

    __tablename__ = "segment_snapshot"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    segment_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    snapshotted_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    lead_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    lead_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("ix_segment_snapshot_tenant_segment_at", "tenant_id", "segment_id", "snapshotted_at"),)
