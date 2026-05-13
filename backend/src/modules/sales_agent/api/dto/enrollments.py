"""Pydantic DTOs for the Enrollments API (Phase 5).

Matching the domain entity one-to-one — the API layer does not derive or
aggregate, just serialises. PII (email, phone) is not returned here; the
frontend joins against the CRM contact by id.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from luana_core_sales_agent.domain.enrollment import EnrollmentStatus, PaymentProvider
from pydantic import BaseModel, ConfigDict, Field


class EnrollmentDTO(BaseModel):
    """Enrollment response — contains no PII (contact id is opaque)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    offer_id: UUID
    edition_id: UUID | None
    contact_id: UUID
    conversation_id: UUID | None
    status: EnrollmentStatus
    pricing_tier_label: str | None
    pricing_amount: float | None
    currency: str | None
    payment_provider: PaymentProvider | None
    payment_transaction_id: str | None
    payment_link_url: str | None
    paid_at: datetime | None
    source_channel: str | None
    notes: str | None
    extra: dict[str, Any]
    created_at: datetime | None
    updated_at: datetime | None


class EnrollmentCreateRequest(BaseModel):
    """Body for ``POST /enrollments``."""

    offer_id: UUID
    contact_id: UUID
    edition_id: UUID | None = None
    conversation_id: UUID | None = None
    status: EnrollmentStatus = EnrollmentStatus.INTENT
    pricing_tier_label: str | None = None
    pricing_amount: float | None = None
    currency: str | None = None
    source_channel: str | None = None
    notes: str | None = None
    extra: dict[str, Any] | None = None


class EnrollmentListResponse(BaseModel):
    """Envelope for list responses."""

    items: list[EnrollmentDTO]
    total: int


class StatusTransitionRequest(BaseModel):
    """Body for ``PATCH /enrollments/{id}/status``."""

    status: EnrollmentStatus


class MarkPaidRequest(BaseModel):
    """Body for ``POST /enrollments/{id}/mark-paid``."""

    provider: PaymentProvider = PaymentProvider.MANUAL
    transaction_id: str | None = None


class PromoteWaitlistRequest(BaseModel):
    """Body for ``POST /enrollments/promote-waitlist``."""

    enrollment_ids: list[UUID] = Field(..., min_length=1)
    target_edition_id: UUID


class PromoteWaitlistResponse(BaseModel):
    """Response for the promote-waitlist bulk action."""

    promoted: int
    skipped: int
    items: list[EnrollmentDTO]
