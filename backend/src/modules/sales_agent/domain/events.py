"""Events domain module."""

from __future__ import annotations

import uuid
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.modules.sales_agent.domain.enrollment import EnrollmentStatus, PaymentProvider
from src.shared.domain.datetime_utils import utc_now


class DomainEvent(BaseModel):
    """Base class for all domain events."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    occurred_on: datetime = Field(default_factory=utc_now)
    version: int = 1


class EnrollmentCreated(DomainEvent):
    """Emitted when a new enrollment is persisted."""

    enrollment_id: UUID
    tenant_id: UUID
    offer_id: UUID
    edition_id: UUID | None
    contact_id: UUID
    status: EnrollmentStatus
    source_channel: str | None = None


class EnrollmentPaid(DomainEvent):
    """Emitted when an enrollment transitions to PAID.

    Consumers:

    - offer module: increments ``launch_editions.enrollment_count``.
    - closer studio widget: updates live state in inbox.
    - analytics: logs revenue event for the period_metrics pipeline.
    """

    enrollment_id: UUID
    tenant_id: UUID
    offer_id: UUID
    edition_id: UUID
    contact_id: UUID
    provider: PaymentProvider
    transaction_id: str | None
    amount: float | None
    currency: str | None


class EnrollmentStatusTransitioned(DomainEvent):
    """Emitted on any explicit status change that is NOT the INTENT → PAID shortcut."""

    enrollment_id: UUID
    tenant_id: UUID
    offer_id: UUID
    from_status: EnrollmentStatus
    to_status: EnrollmentStatus
    actor: str | None = None  # "agent" | "human:<user_id>" | "system:webhook"


# ── S1 sales_agent observability domain events ────────────────────────
#
# Subscribed by ``observability/domain_events/subscribers.py`` and
# persisted to ``sales_agent_trace_event`` (event_type='domain_event').
# Each event carries ``tenant_id`` + ``lead_id`` so the subscriber can
# satisfy the agent-specific row contract without re-resolving identity.


class LeadQualifiedEvent(DomainEvent):
    """Emitted when ``signal_accumulator`` finds the lead qualified.

    Threshold = lead_score + qualification breadth + signals.
    Consumer: observability subscriber persists a domain_event row.
    Future: CRM scoring sync, advertising retargeting feedback loop.
    """

    tenant_id: UUID
    lead_id: UUID
    channel_type: str
    turn_id: UUID
    lead_score: int
    qualification_field_count: int
    buying_signal_count: int
    stage: str


class ObjectionHandledEvent(DomainEvent):
    """Emitted when the closer/product_expert resolves an objection.

    Consumer: observability subscriber. Used by S10 quality eval loop
    to grade objection-resolution coverage per lead.
    """

    tenant_id: UUID
    lead_id: UUID
    channel_type: str
    turn_id: UUID
    objection_type: str
    resolved: bool
    specialist: str  # "qualifier" | "product_expert" | "closer"


class StageTransitionedEvent(DomainEvent):
    """Emitted on a stage transition (rapport / discovery / presentation / closing).

    Consumer: observability subscriber. Powers the S2 stage-funnel
    dashboard.
    """

    tenant_id: UUID
    lead_id: UUID
    channel_type: str
    turn_id: UUID
    from_stage: str
    to_stage: str
    lead_score: int


class ToolLoopDetectedEvent(DomainEvent):
    """Emitted when ``ToolCallDedupTracker`` raises ``ToolCallLoopError``.

    Consumer: observability subscriber writes an ``error`` row to
    sales_agent_trace_event so ops dashboards alert. Distinct from a
    generic exception — captures repeat-call signature for triage.
    """

    tenant_id: UUID
    lead_id: UUID
    channel_type: str
    turn_id: UUID
    tool_name: str
    repeat_count: int
    args_hash: str
