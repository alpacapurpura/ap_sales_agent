"""SQLAlchemy model for Segment entity."""

from __future__ import annotations

import datetime as dt
from uuid import UUID

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.domain.base_entity import Base


class SegmentModel(Base):
    """SQLAlchemy 2.0 model for the segment table.

    Partial unique index (tenant_id, name) WHERE deleted_at IS NULL is
    declared in migration raw SQL — SQLAlchemy partial idx needs raw DDL.
    """

    __tablename__ = "segment"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    segment_type: Mapped[str] = mapped_column(String(16), nullable=False, default="dynamic")
    filter_dsl: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    estimated_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_calculated_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_segment_tenant_created", "tenant_id", "created_at"),
        # Partial unique (tenant_id, name) WHERE deleted_at IS NULL — in migration only.
    )
