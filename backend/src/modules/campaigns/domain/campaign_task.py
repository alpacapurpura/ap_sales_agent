"""CampaignTask domain entity.

Atomic execution unit per (campaign, lead, step).
Production-grade worker queue support via partial index and FOR UPDATE SKIP LOCKED.
"""

from __future__ import annotations

import datetime as dt
from uuid import UUID

from luana_core_campaigns.domain.enums import TaskStatus
from pydantic import BaseModel, ConfigDict, Field


class CampaignTask(BaseModel):
    """Atomic execution unit per (campaign, lead, step).

    Production-grade for 1000+ tenants. Worker queue performance critical:
    - Index partial WHERE status IN ('pending','scheduled') on (tenant_id, status, scheduled_at)
    - Index (tenant_id, campaign_id, status) for reporting
    - claim_pending_for_worker uses FOR UPDATE SKIP LOCKED (same pattern as outbox)

    Invariants:
    - tenant_id MANDATORY
    - lead_id MANDATORY (the recipient)
    - step_id MANDATORY for AGENT_CONVERSATION + EVENT_TRIGGER multi-step;
      can be None for single-step EMAIL_DRIP/RETARGETING (whole campaign = single step)
    - scheduled_at MANDATORY (worker polls by it)
    - status PENDING default
    - attempt_count >= 0
    - outbox_event_id NULL until DISPATCHED (then FK link to domain_event_outbox.id)
    - idempotency_key MANDATORY (natural key: f"task:{campaign_id}:{lead_id}:{step_id or 'single'}")
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    campaign_id: UUID
    lead_id: UUID
    step_id: UUID | None = None  # None for single-step campaigns

    status: TaskStatus = TaskStatus.PENDING

    # Scheduling
    scheduled_at: dt.datetime  # MANDATORY — worker polls by this
    dispatched_at: dt.datetime | None = None
    sent_at: dt.datetime | None = None
    executed_at: dt.datetime | None = None  # final state timestamp (sent/failed/skipped/bounced)

    # Channel resolution at execution time (S2 ChannelRouter sets)
    channel_used: str | None = Field(default=None, max_length=32)
    external_message_id: str | None = Field(default=None, max_length=255)

    # Retry + error tracking
    attempt_count: int = Field(default=0, ge=0)
    last_error: str | None = Field(default=None, max_length=2000)

    # Compliance check evidence (S2 ComplianceService.check result)
    compliance_check: dict | None = None  # {"failed_policy": "waba_24h", "reason": "...", "evidence": {...}}

    # Link to outbox (S2 wiring — for now schema accepts, NULL default)
    outbox_event_id: UUID | None = None

    # Idempotency natural key — service layer PR-4 generates as f"task:{campaign_id}:{lead_id}:{step_id or 'single'}"
    idempotency_key: str = Field(..., min_length=1, max_length=256)

    # Master data
    created_at: dt.datetime
    updated_at: dt.datetime
    deleted_at: dt.datetime | None = None  # soft delete (regla backend-ddd.md)
