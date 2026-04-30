"""CampaignStep domain entity.

Polymorphic step within a Campaign DAG.
DAG structure: each step has next_step_ids (list[UUID]) for branching.
"""

from __future__ import annotations

import datetime as dt
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.modules.campaigns.domain.enums import StepType


class CampaignStep(BaseModel):
    """Polymorphic step within a Campaign DAG.

    DAG structure: each step has next_step_ids (list[UUID]) for branching.
    PR-3 stores list[UUID] in JSONB. service PR-4 / orchestrator S2 walks the DAG.

    step_config JSONB shape per step_type (validated by service layer PR-4):
      SEND_MESSAGE        -> {"template_slug": str, "agent_instructions": str | None,
                              "channel_override": str | None}
      WAIT_DELAY          -> {"delay_seconds": int}
      BRANCH_ON_CONDITION -> {"condition": str, "true_next_step_id": UUID,
                              "false_next_step_id": UUID}
      CALL_SUBAGENT_BRIEF -> {"agent_kind": "sales_agent", "brief": str}
      MARK_COMPLETE       -> {}

    Invariants:
    - next_step_ids cannot contain self.id (no self-loop)
    - step_index >= 0 (display ordering hint, not topology)
    - tenant_id required; redundant with campaign.tenant_id but enforces row-level isolation
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    campaign_id: UUID

    step_type: StepType
    step_index: int = Field(..., ge=0)
    label: str | None = Field(default=None, max_length=128)

    # DAG topology — branching support
    next_step_ids: list[UUID] = Field(default_factory=list)

    # Polymorphic per step_type (validated by service layer PR-4)
    step_config: dict[str, Any] = Field(default_factory=dict)

    created_at: dt.datetime
    updated_at: dt.datetime
    deleted_at: dt.datetime | None = None

    @model_validator(mode="after")
    def _no_self_loop(self) -> CampaignStep:
        """A step cannot reference itself in next_step_ids (no self-loop in DAG)."""
        if self.id in self.next_step_ids:
            msg = "CampaignStep cannot reference itself in next_step_ids"
            raise ValueError(msg)
        return self
