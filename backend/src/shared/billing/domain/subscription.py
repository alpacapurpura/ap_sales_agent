"""TenantSubscription entity — 1:1 tenant ↔ plan with per-tenant overrides.

PR-2 / PI-1 S0.
"""

from __future__ import annotations

import datetime as dt
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TenantSubscription(BaseModel):
    """1:1 tenant ↔ plan + per-tenant overrides.

    `cycle_anchor_day`: day-of-month UTC when billing cycle resets.
    Constrained to 1-28 to avoid ambiguity in shorter months (Feb).

    `custom_overrides`: JSONB for per-tenant capacity overrides, e.g.:
        {"llm_budget_total_usd": 50, "max_outbound_msg_per_day": 5000}
    PlanService.get_effective() merges these on top of the base plan.

    Compat: `tenant_billing_config` legacy NOT replaced; PlanService falls
    back when subscription is NULL (S2 migrates existing tenants).
    """

    model_config = ConfigDict(frozen=True, from_attributes=True)

    tenant_id: UUID
    plan_id: str = Field(..., min_length=2, max_length=32)
    cycle_anchor_day: int = Field(default=1, ge=1, le=28)
    custom_overrides: dict[str, Any] = Field(default_factory=dict)
    trial_ends_at: dt.datetime | None = None
    activated_at: dt.datetime
    updated_at: dt.datetime
    deleted_at: dt.datetime | None = None
