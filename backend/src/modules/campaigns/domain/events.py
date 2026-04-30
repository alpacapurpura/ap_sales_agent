"""Campaign domain events.

14 events declared for campaigns module.
All events are Pydantic v2 models with tenant_id MANDATORY.
Emission via OutboxService.enqueue_* happens in PR-4 service layer / S2 worker.

Note: DomainEvent in shared/domain/events.py is a @dataclass (not Pydantic).
Campaign events use Pydantic v2 for type-safe serialization and follow the
same shape (event_name, tenant_id, occurred_at, payload) without inheriting
the dataclass directly.
"""

from __future__ import annotations

import datetime as dt
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


def _utc_now() -> dt.datetime:
    """Return current UTC datetime."""
    return dt.datetime.now(dt.timezone.utc)


class _CampaignEventBase(BaseModel):
    """Shared base for all campaign events.

    All campaign events carry: tenant_id (mandatory), campaign_id, occurred_at.
    extra='forbid' ensures no extra fields are accepted.
    """

    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    campaign_id: UUID
    occurred_at: dt.datetime = Field(default_factory=_utc_now)


class CampaignCreated(_CampaignEventBase):
    """Emitted when a new campaign is created (PR-4 service)."""

    EVENT_NAME: Literal["campaigns.campaign.created"] = "campaigns.campaign.created"


class CampaignScheduled(_CampaignEventBase):
    """Emitted when a campaign transitions to SCHEDULED state."""

    EVENT_NAME: Literal["campaigns.campaign.scheduled"] = "campaigns.campaign.scheduled"
    scheduled_at: dt.datetime


class CampaignLaunched(_CampaignEventBase):
    """Emitted when a campaign transitions to RUNNING state."""

    EVENT_NAME: Literal["campaigns.campaign.launched"] = "campaigns.campaign.launched"
    launched_at: dt.datetime


class CampaignPaused(_CampaignEventBase):
    """Emitted when a campaign is paused."""

    EVENT_NAME: Literal["campaigns.campaign.paused"] = "campaigns.campaign.paused"


class CampaignCompleted(_CampaignEventBase):
    """Emitted when a campaign reaches COMPLETED terminal state."""

    EVENT_NAME: Literal["campaigns.campaign.completed"] = "campaigns.campaign.completed"
    completed_at: dt.datetime


class CampaignCanceled(_CampaignEventBase):
    """Emitted when a campaign is canceled (terminal state)."""

    EVENT_NAME: Literal["campaigns.campaign.canceled"] = "campaigns.campaign.canceled"
    canceled_at: dt.datetime
    reason: str | None = None


class CampaignStepAdded(_CampaignEventBase):
    """Emitted when a step is added to a campaign."""

    EVENT_NAME: Literal["campaigns.step.added"] = "campaigns.step.added"
    step_id: UUID


class CampaignStepUpdated(_CampaignEventBase):
    """Emitted when a campaign step is updated."""

    EVENT_NAME: Literal["campaigns.step.updated"] = "campaigns.step.updated"
    step_id: UUID


class CampaignTaskQueued(_CampaignEventBase):
    """Emitted when a task is queued for execution.

    Most volume-heavy event: one per (campaign x lead x step) combination.
    Outbox-emit happens in PR-4 service layer / S2 worker.
    """

    EVENT_NAME: Literal["campaigns.task.queued"] = "campaigns.task.queued"
    task_id: UUID
    lead_id: UUID
    scheduled_at: dt.datetime


class CampaignTaskDispatched(_CampaignEventBase):
    """Emitted when a worker claims and dispatches a task."""

    EVENT_NAME: Literal["campaigns.task.dispatched"] = "campaigns.task.dispatched"
    task_id: UUID
    lead_id: UUID
    channel: str


class CampaignTaskSent(_CampaignEventBase):
    """Emitted when a message is successfully handed off to a channel."""

    EVENT_NAME: Literal["campaigns.task.sent"] = "campaigns.task.sent"
    task_id: UUID
    lead_id: UUID
    channel: str
    external_message_id: str | None


class CampaignTaskFailed(_CampaignEventBase):
    """Emitted when a task exhausts retries or encounters a fatal error."""

    EVENT_NAME: Literal["campaigns.task.failed"] = "campaigns.task.failed"
    task_id: UUID
    lead_id: UUID
    error_code: str
    error_message: str


class CampaignTasksGenerated(_CampaignEventBase):
    """Emitted after orchestrator inserts root CampaignTask batch.

    S2 PR-5: new event. audit gate: campaigns.campaign.tasks_generated.
    """

    EVENT_NAME: Literal["campaigns.campaign.tasks_generated"] = "campaigns.campaign.tasks_generated"
    tasks_generated: int
    snapshot_id: UUID | None = None


class SegmentCreated(BaseModel):
    """Emitted when a new segment is created.

    Standalone event (not campaign-scoped — segments exist independently).
    """

    model_config = ConfigDict(extra="forbid")

    EVENT_NAME: Literal["campaigns.segment.created"] = "campaigns.segment.created"
    tenant_id: UUID
    segment_id: UUID
    occurred_at: dt.datetime = Field(default_factory=_utc_now)


class SegmentSnapshotted(BaseModel):
    """Emitted when a segment snapshot is created."""

    model_config = ConfigDict(extra="forbid")

    EVENT_NAME: Literal["campaigns.segment.snapshotted"] = "campaigns.segment.snapshotted"
    tenant_id: UUID
    segment_id: UUID
    snapshot_id: UUID
    lead_count: int
    occurred_at: dt.datetime = Field(default_factory=_utc_now)
