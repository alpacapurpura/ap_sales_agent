"""SQLAlchemy model for CampaignTemplate entity."""

from __future__ import annotations

import datetime as dt
from uuid import UUID

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.domain.base_entity import Base


class CampaignTemplateModel(Base):
    """SQLAlchemy 2.0 model for the campaign_template table.

    Two partial unique indexes are declared in migration raw SQL:
    - uq_campaign_template_global_slug_alive: (slug) WHERE tenant_id IS NULL AND deleted_at IS NULL
    - uq_campaign_template_tenant_slug_alive: (tenant_id, slug) WHERE tenant_id IS NOT NULL AND deleted_at IS NULL
    """

    __tablename__ = "campaign_template"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)  # NULL = global
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=False)
    campaign_type: Mapped[str] = mapped_column(String(32), nullable=False)
    template_body: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    recommended_segment_slugs: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Partial unique indexes declared in migration only (NULL distinct semantics).
