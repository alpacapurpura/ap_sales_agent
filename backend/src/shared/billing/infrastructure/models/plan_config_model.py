"""SQLAlchemy 2.0 model for plan_config global catalog.

Global table — no tenant_id (allowed exception, documented in migration comment).

PR-2 / PI-1 S0.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class PlanConfigModel(Base):
    """plan_config table — global billing plan catalog.

    Five rows seeded in migration 110 (Free/Básico/Intermedio/Avanzado/Ultra).
    Editable via Streamlit admin `/planes-billing` (no migration needed for
    price/cap changes — 1 UPDATE row).

    PM Q6: is_default partial unique index ensures exactly one default row.
    Index: `uq_plan_config_one_default ON plan_config (is_default) WHERE is_default = TRUE`.
    """

    __tablename__ = "plan_config"

    plan_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(64), nullable=False)
    llm_budget_total_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    sales_agent_reserved_pct: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False, default=Decimal("0.50"))
    max_outbound_msg_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_campaigns_active: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_segment_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_contacts_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    features: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # PM Q6
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("llm_budget_total_usd > 0", name="ck_plan_config_budget_positive"),
        CheckConstraint(
            "sales_agent_reserved_pct >= 0 AND sales_agent_reserved_pct <= 1",
            name="ck_plan_config_sa_pct_range",
        ),
        CheckConstraint(
            "max_outbound_msg_per_day IS NULL OR max_outbound_msg_per_day >= 0",
            name="ck_plan_config_outbound_nonneg",
        ),
        # NOTE: partial unique index `uq_plan_config_one_default`
        # (is_default WHERE is_default=TRUE) created via raw SQL in migration
        # (SQLA 2.0 doesn't surface partial UNIQUE cleanly in __table_args__).
    )
