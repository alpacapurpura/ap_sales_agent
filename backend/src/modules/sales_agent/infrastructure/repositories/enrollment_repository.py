"""Repository for Enrollment CRUD (Phase 5).

Mirrors the pattern of ``LaunchEditionRepository``: sync ``Session``,
tenant-scoped reads, ``_to_domain`` converter on every row. Every query
filters by ``tenant_id`` — no exceptions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from luana_core_sales_agent.domain.enrollment import (
    Enrollment,
    EnrollmentStatus,
    PaymentProvider,
)
from luana_core_sales_agent.infrastructure.models.enrollment_model import (
    EnrollmentModel,
)
from sqlalchemy import select

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session


class EnrollmentRepository:
    """Repository for enrollment persistence."""

    def __init__(self, db: Session) -> None:
        """Initialize repository with database session."""
        self.db = db

    # ------------------------------------------------------------------ mapping

    def _to_domain(self, model: EnrollmentModel) -> Enrollment:
        return Enrollment(
            id=model.id,
            tenant_id=model.tenant_id,
            offer_id=model.offer_id,
            edition_id=model.edition_id,
            contact_id=model.contact_id,
            conversation_id=model.conversation_id,
            status=EnrollmentStatus(model.status),
            pricing_tier_label=model.pricing_tier_label,
            pricing_amount=model.pricing_amount,
            currency=model.currency,
            payment_provider=(PaymentProvider(model.payment_provider) if model.payment_provider else None),
            payment_transaction_id=model.payment_transaction_id,
            payment_link_url=model.payment_link_url,
            paid_at=model.paid_at,
            source_channel=model.source_channel,
            notes=model.notes,
            extra=model.extra or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    # ------------------------------------------------------------------ writes

    def create(self, enrollment: Enrollment) -> Enrollment:
        """Persist a fresh enrollment.

        Domain invariants were validated by ``Enrollment`` — the repo
        trusts the caller.
        """
        model = EnrollmentModel(
            tenant_id=enrollment.tenant_id,
            offer_id=enrollment.offer_id,
            edition_id=enrollment.edition_id,
            contact_id=enrollment.contact_id,
            conversation_id=enrollment.conversation_id,
            status=enrollment.status.value,
            pricing_tier_label=enrollment.pricing_tier_label,
            pricing_amount=enrollment.pricing_amount,
            currency=enrollment.currency,
            payment_provider=(enrollment.payment_provider.value if enrollment.payment_provider else None),
            payment_transaction_id=enrollment.payment_transaction_id,
            payment_link_url=enrollment.payment_link_url,
            paid_at=enrollment.paid_at,
            source_channel=enrollment.source_channel,
            notes=enrollment.notes,
            extra=enrollment.extra or None,
        )
        self.db.add(model)
        self.db.flush()
        self.db.refresh(model)
        return self._to_domain(model)

    def update(
        self,
        enrollment_id: UUID,
        tenant_id: UUID,
        data: dict[str, Any],
    ) -> Enrollment:
        """Patch an enrollment with a dict of attributes."""
        stmt = select(EnrollmentModel).where(
            EnrollmentModel.id == enrollment_id,
            EnrollmentModel.tenant_id == tenant_id,
        )
        model = self.db.execute(stmt).scalar_one_or_none()
        if model is None:
            msg = f"Enrollment {enrollment_id} not found"
            raise ValueError(msg)

        for key, raw_value in data.items():
            if raw_value is None and key in {
                "edition_id",
                "paid_at",
                "payment_provider",
                "payment_transaction_id",
            }:
                # Allow explicit null writes for these columns.
                setattr(model, key, None)
                continue
            if raw_value is None:
                continue
            resolved = raw_value.value if hasattr(raw_value, "value") else raw_value
            if hasattr(model, key):
                setattr(model, key, resolved)

        self.db.flush()
        self.db.refresh(model)
        return self._to_domain(model)

    # ------------------------------------------------------------------ reads

    def get_by_id(self, enrollment_id: UUID, tenant_id: UUID) -> Enrollment | None:
        """Retrieve by id, tenant-scoped."""
        stmt = select(EnrollmentModel).where(
            EnrollmentModel.id == enrollment_id,
            EnrollmentModel.tenant_id == tenant_id,
        )
        model = self.db.execute(stmt).scalar_one_or_none()
        return self._to_domain(model) if model else None

    def list_by_offer(
        self,
        offer_id: UUID,
        tenant_id: UUID,
        *,
        edition_id: UUID | None = None,
        status: EnrollmentStatus | None = None,
    ) -> list[Enrollment]:
        """List enrollments for an offer, optionally filtered by edition/status."""
        stmt = select(EnrollmentModel).where(
            EnrollmentModel.tenant_id == tenant_id,
            EnrollmentModel.offer_id == offer_id,
        )
        if edition_id is not None:
            stmt = stmt.where(EnrollmentModel.edition_id == edition_id)
        if status is not None:
            stmt = stmt.where(EnrollmentModel.status == status.value)
        stmt = stmt.order_by(EnrollmentModel.created_at.desc())
        models = self.db.execute(stmt).scalars().all()
        return [self._to_domain(m) for m in models]

    def list_waitlist(self, offer_id: UUID, tenant_id: UUID) -> list[Enrollment]:
        """List waitlist enrollments for an offer (no edition yet)."""
        stmt = (
            select(EnrollmentModel)
            .where(
                EnrollmentModel.tenant_id == tenant_id,
                EnrollmentModel.offer_id == offer_id,
                EnrollmentModel.status == EnrollmentStatus.WAITLIST.value,
                EnrollmentModel.edition_id.is_(None),
            )
            .order_by(EnrollmentModel.created_at.asc())
        )
        models = self.db.execute(stmt).scalars().all()
        return [self._to_domain(m) for m in models]

    def list_all(
        self,
        tenant_id: UUID,
        *,
        offer_id: UUID | None = None,
        edition_id: UUID | None = None,
        status: EnrollmentStatus | None = None,
        contact_id: UUID | None = None,
    ) -> list[Enrollment]:
        """List with any combination of filters — for global Closer page."""
        stmt = select(EnrollmentModel).where(EnrollmentModel.tenant_id == tenant_id)
        if offer_id is not None:
            stmt = stmt.where(EnrollmentModel.offer_id == offer_id)
        if edition_id is not None:
            stmt = stmt.where(EnrollmentModel.edition_id == edition_id)
        if status is not None:
            stmt = stmt.where(EnrollmentModel.status == status.value)
        if contact_id is not None:
            stmt = stmt.where(EnrollmentModel.contact_id == contact_id)
        stmt = stmt.order_by(EnrollmentModel.created_at.desc())
        models = self.db.execute(stmt).scalars().all()
        return [self._to_domain(m) for m in models]

    def get_by_conversation(
        self,
        conversation_id: UUID,
        tenant_id: UUID,
    ) -> Enrollment | None:
        """Return the most recent enrollment linked to a conversation, if any.

        Used by the inbox widget in Closer Studio.
        """
        stmt = (
            select(EnrollmentModel)
            .where(
                EnrollmentModel.tenant_id == tenant_id,
                EnrollmentModel.conversation_id == conversation_id,
            )
            .order_by(EnrollmentModel.created_at.desc())
            .limit(1)
        )
        model = self.db.execute(stmt).scalar_one_or_none()
        return self._to_domain(model) if model else None
