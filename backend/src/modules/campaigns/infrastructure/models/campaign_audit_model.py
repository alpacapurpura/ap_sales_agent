"""SQLA model for campaign_audit table.

Append-only audit log. No soft-delete (bounded retention via worker).
Retention 90d: purge_old_campaigns_audit cron 04:30 UTC.

PR-5 PI-1 S2.
"""

from __future__ import annotations

import datetime as dt
from uuid import UUID

from sqlalchemy import DateTime, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.domain.base_entity import Base


class CampaignAuditModel(Base):
    """Audit log row. Append-only. Retention 90d via worker."""

    __tablename__ = "campaign_audit"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    campaign_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    campaign_task_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    actor: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        # Hot path: "todos los eventos de esta campaña" ordered desc
        Index(
            "ix_campaign_audit_tenant_campaign_created",
            "tenant_id",
            "campaign_id",
            "created_at",
            postgresql_where="campaign_id IS NOT NULL",
        ),
        # Retention purge hot path (worker scans globally by created_at)
        Index("ix_campaign_audit_created", "created_at"),
        # Debug: buscar eventos por task específica
        Index(
            "ix_campaign_audit_task",
            "campaign_task_id",
            postgresql_where="campaign_task_id IS NOT NULL",
        ),
    )
