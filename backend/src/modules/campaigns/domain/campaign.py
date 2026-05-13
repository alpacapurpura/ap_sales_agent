"""Campaign aggregate root.

Domain entity — pure Python, no framework dependencies.
FSM transitions enforced via _FSM_TRANSITIONS matrix (arch test inspects this).
"""

from __future__ import annotations

import datetime as dt
from typing import Any
from uuid import UUID

from luana_core_campaigns.domain.enums import CampaignStatus, CampaignType
from pydantic import BaseModel, ConfigDict, Field, model_validator

# FSM transitions matrix — single source of truth for arch test introspection.
# Keys: current status. Values: frozenset of allowed next statuses.
_FSM_TRANSITIONS: dict[CampaignStatus, frozenset[CampaignStatus]] = {
    CampaignStatus.DRAFT: frozenset({CampaignStatus.SCHEDULED, CampaignStatus.CANCELED}),
    CampaignStatus.SCHEDULED: frozenset({CampaignStatus.RUNNING, CampaignStatus.PAUSED, CampaignStatus.CANCELED}),
    CampaignStatus.RUNNING: frozenset({CampaignStatus.PAUSED, CampaignStatus.COMPLETED, CampaignStatus.CANCELED}),
    CampaignStatus.PAUSED: frozenset({CampaignStatus.RUNNING, CampaignStatus.CANCELED}),
    CampaignStatus.COMPLETED: frozenset(),  # terminal
    CampaignStatus.CANCELED: frozenset(),  # terminal
}


class Campaign(BaseModel):
    """Aggregate root for campaign lifecycle.

    Invariants:
    - tenant_id NEVER None
    - deleted_at None unless soft-deleted
    - status DRAFT default; transitions enforced via _FSM_TRANSITIONS
    - scheduled_at NOT NULL when status >= SCHEDULED (model_validator)
    - launched_at NOT NULL when status == RUNNING (set by service PR-4)
    - completed_at NOT NULL when status in (COMPLETED, CANCELED)
    - offer_id required for AGENT_CONVERSATION campaigns from SCHEDULED onward

    config JSONB shape per campaign_type (validated by service PR-4):
      AGENT_CONVERSATION   -> {"agent_instructions": str, "tone_override": str | None}
      EMAIL_DRIP           -> {"mailerlite_group_slug": str}
      EMAIL_BROADCAST      -> {"mailerlite_campaign_id": str}
      EVENT_TRIGGER        -> {"anchor_event_date": iso8601, "timezone": str}
      PUSH_NOTIFICATION    -> {"onesignal_template_id": str}
      RETARGETING_EXPORT   -> {"meta_audience_id": str}
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)

    # Type + state
    campaign_type: CampaignType
    status: CampaignStatus = CampaignStatus.DRAFT

    # Targeting
    segment_id: UUID | None = None
    segment_snapshot_id: UUID | None = None  # set when launched if audience locking enabled (S2)

    # Channel routing — priority list, first available wins (S2 ChannelRouter consumes)
    channel_priority: list[str] = Field(default_factory=list)

    # FK (UUID only — no cross-module SQL JOIN; resolution via shared/links/ports/* in service PR-4)
    offer_id: UUID | None = None
    brand_summary_id: UUID | None = None  # optional pin to specific brand voice version (PI-2)

    # Type-specific config (validated by service layer PR-4 via type-specific Pydantic model)
    config: dict[str, Any] = Field(default_factory=dict)

    # Scheduling — UTC always (regla master-data.md)
    scheduled_at: dt.datetime | None = None
    launched_at: dt.datetime | None = None
    completed_at: dt.datetime | None = None

    # Provenance
    created_by_user_id: UUID | None = None
    created_by_source: str = Field(default="api")

    # Master data
    created_at: dt.datetime
    updated_at: dt.datetime
    deleted_at: dt.datetime | None = None

    @model_validator(mode="after")
    def _validate_status_invariants(self) -> Campaign:
        """Enforce status-dependent field requirements."""
        if (
            self.status in (CampaignStatus.SCHEDULED, CampaignStatus.RUNNING, CampaignStatus.PAUSED)
            and self.scheduled_at is None
        ):
            msg = f"scheduled_at required when status={self.status.value}"
            raise ValueError(msg)
        if self.status == CampaignStatus.RUNNING and self.launched_at is None:
            msg = "launched_at required when status=running"
            raise ValueError(msg)
        if self.status in (CampaignStatus.COMPLETED, CampaignStatus.CANCELED) and self.completed_at is None:
            msg = f"completed_at required when status={self.status.value}"
            raise ValueError(msg)
        if (
            self.status >= CampaignStatus.SCHEDULED
            and self.campaign_type == CampaignType.AGENT_CONVERSATION
            and self.offer_id is None
        ):
            msg = "offer_id required for AGENT_CONVERSATION campaigns from SCHEDULED onward"
            raise ValueError(msg)
        return self

    @classmethod
    def transition_allowed(cls, from_status: CampaignStatus, to_status: CampaignStatus) -> bool:
        """Pure FSM check. Service layer PR-4 calls this before persist."""
        return to_status in _FSM_TRANSITIONS[from_status]

    @classmethod
    def get_fsm_transitions(cls) -> dict[CampaignStatus, frozenset[CampaignStatus]]:
        """Expose FSM matrix for arch test introspection."""
        return _FSM_TRANSITIONS
