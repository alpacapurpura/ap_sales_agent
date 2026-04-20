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
