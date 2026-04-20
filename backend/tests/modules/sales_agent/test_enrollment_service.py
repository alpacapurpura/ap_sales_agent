"""Tests for EnrollmentService (Phase 5)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import pytest

from src.modules.sales_agent.application.services.enrollment_service import (
    EnrollmentService,
)
from src.modules.sales_agent.domain.enrollment import (
    Enrollment,
    EnrollmentCreate,
    EnrollmentStatus,
    PaymentProvider,
)
from src.modules.sales_agent.domain.events import (
    EnrollmentCreated,
    EnrollmentPaid,
    EnrollmentStatusTransitioned,
)
from src.modules.sales_agent.infrastructure.repositories.enrollment_repository import (
    EnrollmentRepository,
)
from tests.modules.offer.conftest import create_product_model

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

_TENANT = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


@pytest.fixture
def tenant() -> uuid.UUID:
    return _TENANT


@pytest.fixture
def offer_id(db: Session, tenant: uuid.UUID) -> uuid.UUID:
    model = create_product_model(tenant, archetype="programa")
    db.add(model)
    db.flush()
    return model.id


@pytest.fixture
def service(db: Session) -> EnrollmentService:
    return EnrollmentService(EnrollmentRepository(db))


class TestCreate:
    def test_create_waitlist_when_edition_missing(
        self,
        service: EnrollmentService,
        tenant: uuid.UUID,
        offer_id: uuid.UUID,
    ) -> None:
        payload = EnrollmentCreate(
            offer_id=offer_id,
            contact_id=uuid.uuid4(),
            edition_id=None,
            status=EnrollmentStatus.INTENT,  # will be coerced
        )
        result = service.create(payload, tenant)
        assert result.enrollment.status == EnrollmentStatus.WAITLIST
        assert result.enrollment.edition_id is None
        assert len(result.events) == 1
        assert isinstance(result.events[0], EnrollmentCreated)

    def test_create_intent_with_edition(
        self,
        service: EnrollmentService,
        tenant: uuid.UUID,
        offer_id: uuid.UUID,
    ) -> None:
        edition_id = uuid.uuid4()
        payload = EnrollmentCreate(
            offer_id=offer_id,
            contact_id=uuid.uuid4(),
            edition_id=edition_id,
        )
        result = service.create(payload, tenant)
        assert result.enrollment.status == EnrollmentStatus.INTENT
        assert result.enrollment.edition_id == edition_id


class TestMarkPaid:
    def test_emits_paid_and_transition_events(
        self,
        service: EnrollmentService,
        tenant: uuid.UUID,
        offer_id: uuid.UUID,
    ) -> None:
        created = service.create(
            EnrollmentCreate(
                offer_id=offer_id,
                contact_id=uuid.uuid4(),
                edition_id=uuid.uuid4(),
                pricing_amount=690.0,
                currency="PEN",
            ),
            tenant,
        )
        # Force-advance to PAYMENT_PENDING to mimic agent flow.
        service.update_status(
            created.enrollment.id,
            tenant,
            EnrollmentStatus.PAYMENT_PENDING,
        )

        paid = service.mark_paid(
            created.enrollment.id,
            tenant,
            provider=PaymentProvider.STRIPE,
            transaction_id="tx_test_1",
            now=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )
        assert paid.enrollment.status == EnrollmentStatus.PAID
        assert paid.enrollment.paid_at is not None
        event_types = {type(e) for e in paid.events}
        assert EnrollmentPaid in event_types
        assert EnrollmentStatusTransitioned in event_types

    def test_rejects_waitlist(
        self,
        service: EnrollmentService,
        tenant: uuid.UUID,
        offer_id: uuid.UUID,
    ) -> None:
        created = service.create(
            EnrollmentCreate(
                offer_id=offer_id,
                contact_id=uuid.uuid4(),
                edition_id=None,
            ),
            tenant,
        )
        with pytest.raises(ValueError, match="waitlist"):
            service.mark_paid(
                created.enrollment.id,
                tenant,
                provider=PaymentProvider.STRIPE,
                transaction_id="tx_1",
            )


class TestPromoteWaitlist:
    def test_bulk_promote_skips_non_waitlist(
        self,
        service: EnrollmentService,
        tenant: uuid.UUID,
        offer_id: uuid.UUID,
    ) -> None:
        wait = service.create(
            EnrollmentCreate(offer_id=offer_id, contact_id=uuid.uuid4(), edition_id=None),
            tenant,
        )
        intent = service.create(
            EnrollmentCreate(
                offer_id=offer_id,
                contact_id=uuid.uuid4(),
                edition_id=uuid.uuid4(),
            ),
            tenant,
        )

        target_edition = uuid.uuid4()
        promoted = service.promote_waitlist(
            [wait.enrollment.id, intent.enrollment.id],
            target_edition,
            tenant,
        )
        assert len(promoted) == 1
        assert promoted[0].enrollment.status == EnrollmentStatus.PAYMENT_PENDING
        assert promoted[0].enrollment.edition_id == target_edition
