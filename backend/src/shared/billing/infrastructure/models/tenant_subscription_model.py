"""SQLAlchemy 2.0 model for tenant_subscription (1:1 tenant ↔ plan).

PR-2 / PI-1 S0.
"""

from __future__ import annotations

import datetime as dt
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class TenantSubscriptionModel(Base):
    """tenant_subscription table — 1:1 tenant ↔ plan with overrides.

    Soft-deleted via deleted_at (never hard-deleted per DDD rules).
    ForeignKey to plan_config.plan_id — plan must exist before subscription.
    """

    __tablename__ = "tenant_subscription"

    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    plan_id: Mapped[str] = mapped_column(String(32), ForeignKey("plan_config.plan_id"), nullable=False)
    cycle_anchor_day: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    custom_overrides: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    trial_ends_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    activated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "cycle_anchor_day BETWEEN 1 AND 28",
            name="ck_tenant_subscription_anchor_range",
        ),
        Index("ix_tenant_subscription_plan_id", "plan_id"),
        Index(
            "ix_tenant_subscription_active",
            "tenant_id",
            postgresql_where="deleted_at IS NULL",
        ),
    )
