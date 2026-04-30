"""SQLAlchemy model for CampaignStep entity."""

from __future__ import annotations

import datetime as dt
from uuid import UUID

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.domain.base_entity import Base


class CampaignStepModel(Base):
    """SQLAlchemy 2.0 model for the campaign_step table."""

    __tablename__ = "campaign_step"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    campaign_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)

    step_type: Mapped[str] = mapped_column(String(32), nullable=False)
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str | None] = mapped_column(String(128), nullable=True)

    next_step_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    step_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("ix_campaign_step_tenant_campaign", "tenant_id", "campaign_id"),)
