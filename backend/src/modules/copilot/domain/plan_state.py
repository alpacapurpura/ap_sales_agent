"""PlanState — stored in copilot_conversations.plan_state (JSONB)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PlanStep(BaseModel):
    """One step in a proposed execution plan."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    description: str
    tool: str
    args: dict[str, object]
    estimated_cost_usd: float


class PlanState(BaseModel):
    """Plan proposed by the orchestrator, awaiting user approval."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    plan_id: UUID
    message_id: UUID
    steps: list[PlanStep]
    total_cost_estimate: float
    proposed_at: datetime
    expires_at: datetime
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
