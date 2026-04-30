"""SQLAlchemy 2.0 model for mv_refresh_log — PM Q4.

Global infra table (NO tenant_id). Allowlist exception documented in
tenant-isolation arch test (global catalog / operational infra).

PR-2 / PI-1 S0.
"""

from __future__ import annotations

import datetime as dt
import uuid as uuid_mod
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class MVRefreshLogModel(Base):
    """mv_refresh_log table — exact MV freshness signal.

    One row per MATERIALIZED VIEW refresh attempt. 90-day retention via
    weekly ARQ task `mv_refresh_log_retention_task`.

    Global infra table (NO tenant_id) — operational data, not tenant-scoped.
    Allowlist exception documented in architectural fitness tests.
    """

    __tablename__ = "mv_refresh_log"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid_mod.uuid4)
    mv_name: Mapped[str] = mapped_column(String(64), nullable=False)
    refreshed_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    refresh_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rows_affected: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ok")

    __table_args__ = (
        CheckConstraint(
            "status IN ('ok', 'error', 'skipped')",
            name="ck_mv_refresh_log_status_enum",
        ),
        Index(
            "ix_mv_refresh_log_mv_name_recent",
            "mv_name",
            "refreshed_at",
        ),
    )
