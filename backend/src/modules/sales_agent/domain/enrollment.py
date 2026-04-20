"""Enrollment domain entity — lead inscribed in an offer edition (Phase 5).

One ``Enrollment`` represents an intent-to-buy or completed purchase of an
offer by a contact. Enrollments are offer/edition-scoped so reporting,
waitlist conversion, and attendance tracking all pivot on the same row.

Lifecycle (``EnrollmentStatus``)::

    INTENT ──► PAYMENT_PENDING ──► PAID ──► ATTENDED
       │               │              │        │
       │               ▼              ▼        ▼
       └──► WAITLIST ─┴─► CANCELLED / REFUNDED (terminal)

Invariants enforced here:

- ``WAITLIST`` iff ``edition_id IS NULL`` (waitlist = no edition yet).
- Any non-``WAITLIST`` status requires ``edition_id``.
- ``PAID`` / ``ATTENDED`` require a ``paid_at`` timestamp.

Mutation helpers return a new instance (domain is immutable at the entity
boundary; the repository writes the delta).
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from src.shared.domain.base_entity import BaseEntity
from src.shared.domain.datetime_utils import utc_now


class EnrollmentStatus(StrEnum):
    """Lifecycle state of an enrollment."""

    INTENT = "intent"  # agent captured purchase intent, no payment link yet
    WAITLIST = "waitlist"  # no edition assigned; waiting for one to open
    PAYMENT_PENDING = "payment_pending"  # payment link sent, not paid
    PAID = "paid"  # payment confirmed
    ATTENDED = "attended"  # attended / consumed the edition
    REFUNDED = "refunded"  # paid then refunded (terminal)
    CANCELLED = "cancelled"  # cancelled before/after payment (terminal)


class PaymentProvider(StrEnum):
    """External payment gateway that captured the transaction."""

    STRIPE = "stripe"
    MERCADOPAGO = "mercadopago"
    CULQI = "culqi"
    MANUAL = "manual"  # marked-paid by human operator (no automated webhook)


_STATUSES_REQUIRING_PAID_AT: frozenset[EnrollmentStatus] = frozenset(
    {EnrollmentStatus.PAID, EnrollmentStatus.ATTENDED},
)


class Enrollment(BaseEntity):
    """One contact's enrollment in one offer (and, when known, one edition)."""

    id: UUID | None = None
    tenant_id: UUID
    offer_id: UUID
    edition_id: UUID | None = None
    contact_id: UUID
    conversation_id: UUID | None = None

    status: EnrollmentStatus = EnrollmentStatus.INTENT

    pricing_tier_label: str | None = None
    pricing_amount: float | None = None
    currency: str | None = None

    payment_provider: PaymentProvider | None = None
    payment_transaction_id: str | None = None
    payment_link_url: str | None = None
    paid_at: datetime | None = None

    source_channel: str | None = None  # ig_dm, landing, manychat, email...
    notes: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

    created_at: datetime | None = None
    updated_at: datetime | None = None

    @model_validator(mode="after")
    def validate_invariants(self) -> Enrollment:
        """Enforce waitlist ⇔ null-edition and paid ⇒ paid_at."""
        if self.status == EnrollmentStatus.WAITLIST and self.edition_id is not None:
            msg = "waitlist enrollments cannot have an edition_id"
            raise ValueError(msg)

        if self.status != EnrollmentStatus.WAITLIST and self.edition_id is None:
            msg = "non-waitlist enrollments require an edition_id"
            raise ValueError(msg)

        if self.status in _STATUSES_REQUIRING_PAID_AT and self.paid_at is None:
            msg = f"{self.status.value} enrollments require paid_at"
            raise ValueError(msg)

        return self

    def mark_paid(
        self,
        *,
        provider: PaymentProvider,
        transaction_id: str | None,
        now: datetime | None = None,
    ) -> Enrollment:
        """Return a copy transitioned to ``PAID`` with payment metadata set."""
        return self.model_copy(
            update={
                "status": EnrollmentStatus.PAID,
                "payment_provider": provider,
                "payment_transaction_id": transaction_id,
                "paid_at": now or utc_now(),
            },
        )

    def promote_to_edition(self, edition_id: UUID) -> Enrollment:
        """Return a copy moved from WAITLIST to PAYMENT_PENDING on a target edition."""
        return self.model_copy(
            update={
                "edition_id": edition_id,
                "status": EnrollmentStatus.PAYMENT_PENDING,
            },
        )


class EnrollmentCreate(BaseEntity):
    """DTO for creating a new enrollment."""

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


class EnrollmentUpdate(BaseEntity):
    """DTO for patching an enrollment (all fields optional)."""

    status: EnrollmentStatus | None = None
    edition_id: UUID | None = None
    pricing_tier_label: str | None = None
    pricing_amount: float | None = None
    currency: str | None = None
    payment_provider: PaymentProvider | None = None
    payment_transaction_id: str | None = None
    payment_link_url: str | None = None
    paid_at: datetime | None = None
    notes: str | None = None
    extra: dict[str, Any] | None = None


__all__ = [
    "Enrollment",
    "EnrollmentCreate",
    "EnrollmentStatus",
    "EnrollmentUpdate",
    "PaymentProvider",
]
