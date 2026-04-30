"""MVRefreshLog entity — PM Q4 exact MV freshness signal.

Global table (no tenant_id). Operational infra, not tenant data.
Allowlist exception documented in tenant-isolation arch test (PR-2 §12).

PR-2 / PI-1 S0.
"""

from __future__ import annotations

import datetime as dt
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

RefreshStatus = Literal["ok", "error", "skipped"]


class MVRefreshLog(BaseModel):
    """One row per MATERIALIZED VIEW refresh attempt.

    Cron job inserts row after each CONCURRENTLY refresh. BudgetGuard
    queries `get_last_refresh(mv_name)` to determine staleness.

    Retention: 90 days via ARQ weekly task `mv_refresh_log_retention_task`.
    """

    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: UUID
    mv_name: str = Field(..., min_length=1, max_length=64)
    refreshed_at: dt.datetime
    refresh_duration_ms: int | None = Field(default=None, ge=0)
    rows_affected: int | None = Field(default=None, ge=0)
    status: RefreshStatus = "ok"
