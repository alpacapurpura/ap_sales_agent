"""SQLAlchemy 2.0 model for lead_opt_ins — PM Q2 production-grade consent tracking.

PR-2 / PI-1 S0.
"""

from __future__ import annotations

import datetime as dt
import uuid as uuid_mod
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class LeadOptInModel(Base):
    """lead_opt_ins table — per-channel consent audit trail.

    GDPR/LGPD-ready: explicit opted_in_at timestamp + source + evidence.
    Unique constraint (tenant_id, lead_id, channel) for idempotent upsert.
    """

    __tablename__ = "lead_opt_ins"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid_mod.uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    lead_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("leads.id"), nullable=False)
    channel: Mapped[str] = mapped_column(String(32), nullable=False)
    opted_in_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    opted_out_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source: Mapped[str] = mapped_column(String(24), nullable=False)  # webhook | manual | imported | inferred_message
    evidence: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "lead_id",
            "channel",
            name="uq_lead_opt_ins_tenant_lead_channel",
        ),
        CheckConstraint(
            "source IN ('webhook', 'manual', 'imported', 'inferred_message')",
            name="ck_lead_opt_ins_source_enum",
        ),
        Index(
            "ix_lead_opt_ins_lookup",
            "tenant_id",
            "lead_id",
            "channel",
            "opted_in_at",
            "opted_out_at",
        ),
    )
