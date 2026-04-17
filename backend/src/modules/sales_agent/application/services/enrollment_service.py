"""Enrollment application service (Phase 5).

Orchestrates the enrollment lifecycle. Emits events through the
``events`` list on each returned object so callers (API layer, webhook
handlers) can dispatch them onto the event bus without the service
needing an async bus reference.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.modules.sales_agent.domain.enrollment import (
    Enrollment,
    EnrollmentCreate,
    EnrollmentStatus,
    EnrollmentUpdate,
    PaymentProvider,
)
from src.modules.sales_agent.domain.events import (
    DomainEvent,
    EnrollmentCreated,
    EnrollmentPaid,
    EnrollmentStatusTransitioned,
)
from src.shared.domain.datetime_utils import utc_now

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from src.modules.sales_agent.infrastructure.repositories.enrollment_repository import (
        EnrollmentRepository,
    )


@dataclass
class ServiceResult:
    """Tuple of the mutated entity and the domain events to publish."""

    enrollment: Enrollment
    events: list[DomainEvent]


class EnrollmentService:
    """Use cases around enrollments: create, mark-paid, promote-waitlist."""

    def __init__(self, repo: EnrollmentRepository) -> None:
        """Initialize with a pre-bound repository."""
        self.repo = repo

    # ------------------------------------------------------------------ create

    def create(self, payload: EnrollmentCreate, tenant_id: UUID) -> ServiceResult:
        """Create a fresh enrollment.

        If ``edition_id`` is missing the status is forced to ``WAITLIST``
        (a non-waitlist row without an edition violates the domain
        invariant). Otherwise ``payload.status`` is respected.
        """
        status = payload.status
        if payload.edition_id is None:
            status = EnrollmentStatus.WAITLIST

        enrollment = Enrollment(
            tenant_id=tenant_id,
            offer_id=payload.offer_id,
            edition_id=payload.edition_id,
            contact_id=payload.contact_id,
            conversation_id=payload.conversation_id,
            status=status,
            pricing_tier_label=payload.pricing_tier_label,
            pricing_amount=payload.pricing_amount,
            currency=payload.currency,
            source_channel=payload.source_channel,
            notes=payload.notes,
            extra=payload.extra or {},
        )
        stored = self.repo.create(enrollment)

        event = EnrollmentCreated(
            enrollment_id=stored.id,
            tenant_id=stored.tenant_id,
            offer_id=stored.offer_id,
            edition_id=stored.edition_id,
            contact_id=stored.contact_id,
            status=stored.status,
            source_channel=stored.source_channel,
        )
        return ServiceResult(enrollment=stored, events=[event])

    # ------------------------------------------------------------------ mark paid

    def mark_paid(
        self,
        enrollment_id: UUID,
        tenant_id: UUID,
        *,
        provider: PaymentProvider,
        transaction_id: str | None,
        now: datetime | None = None,
    ) -> ServiceResult:
        """Transition an enrollment to ``PAID`` and emit ``EnrollmentPaid``."""
        current = self.repo.get_by_id(enrollment_id, tenant_id)
        if current is None:
            msg = f"Enrollment {enrollment_id} not found"
            raise LookupError(msg)
        if current.edition_id is None:
            msg = "cannot mark waitlist enrollment as paid — promote it first"
            raise ValueError(msg)

        updated_domain = current.mark_paid(
            provider=provider,
            transaction_id=transaction_id,
            now=now or utc_now(),
        )
        stored = self.repo.update(
            enrollment_id,
            tenant_id,
            {
                "status": updated_domain.status,
                "payment_provider": updated_domain.payment_provider,
                "payment_transaction_id": updated_domain.payment_transaction_id,
                "paid_at": updated_domain.paid_at,
            },
        )

        events: list[DomainEvent] = [
            EnrollmentPaid(
                enrollment_id=stored.id,
                tenant_id=stored.tenant_id,
                offer_id=stored.offer_id,
                edition_id=stored.edition_id,  # type: ignore[arg-type]
                contact_id=stored.contact_id,
                provider=provider,
                transaction_id=transaction_id,
                amount=stored.pricing_amount,
                currency=stored.currency,
            ),
            EnrollmentStatusTransitioned(
                enrollment_id=stored.id,
                tenant_id=stored.tenant_id,
                offer_id=stored.offer_id,
                from_status=current.status,
                to_status=stored.status,
                actor="system:webhook",
            ),
        ]
        return ServiceResult(enrollment=stored, events=events)

    # ------------------------------------------------------------------ promote waitlist

    def promote_waitlist(
        self,
        enrollment_ids: list[UUID],
        target_edition_id: UUID,
        tenant_id: UUID,
    ) -> list[ServiceResult]:
        """Move a batch of waitlist enrollments to ``PAYMENT_PENDING``.

        Atomic per-row: a failure on enrollment #3 does not roll back
        enrollments #1 and #2. The caller shows a per-row result.
        """
        results: list[ServiceResult] = []
        for eid in enrollment_ids:
            current = self.repo.get_by_id(eid, tenant_id)
            if current is None:
                continue
            if current.status != EnrollmentStatus.WAITLIST:
                continue

            promoted = current.promote_to_edition(target_edition_id)
            stored = self.repo.update(
                eid,
                tenant_id,
                {
                    "status": promoted.status,
                    "edition_id": target_edition_id,
                },
            )
            events: list[DomainEvent] = [
                EnrollmentStatusTransitioned(
                    enrollment_id=stored.id,
                    tenant_id=stored.tenant_id,
                    offer_id=stored.offer_id,
                    from_status=current.status,
                    to_status=stored.status,
                    actor="system:waitlist-promotion",
                ),
            ]
            results.append(ServiceResult(enrollment=stored, events=events))
        return results

    # ------------------------------------------------------------------ update status

    def update_status(
        self,
        enrollment_id: UUID,
        tenant_id: UUID,
        new_status: EnrollmentStatus,
        *,
        actor: str | None = None,
    ) -> ServiceResult:
        """Generic status transition (refund, cancel, attended)."""
        current = self.repo.get_by_id(enrollment_id, tenant_id)
        if current is None:
            msg = f"Enrollment {enrollment_id} not found"
            raise LookupError(msg)

        patch: dict = {"status": new_status}
        if new_status == EnrollmentStatus.ATTENDED and current.paid_at is None:
            msg = "cannot mark unpaid enrollment as attended"
            raise ValueError(msg)

        stored = self.repo.update(enrollment_id, tenant_id, patch)
        event = EnrollmentStatusTransitioned(
            enrollment_id=stored.id,
            tenant_id=stored.tenant_id,
            offer_id=stored.offer_id,
            from_status=current.status,
            to_status=stored.status,
            actor=actor,
        )
        return ServiceResult(enrollment=stored, events=[event])

    # ------------------------------------------------------------------ patch

    def patch(
        self,
        enrollment_id: UUID,
        tenant_id: UUID,
        payload: EnrollmentUpdate,
    ) -> Enrollment:
        """Patch arbitrary fields (no event emission)."""
        data = payload.model_dump(exclude_unset=True)
        return self.repo.update(enrollment_id, tenant_id, data)


__all__ = ["EnrollmentService", "ServiceResult"]
