"""Tests for EnrollmentRepository (Phase 5)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest

from luana_core_sales_agent.domain.enrollment import (
    Enrollment,
    EnrollmentStatus,
    PaymentProvider,
)
from luana_core_sales_agent.infrastructure.repositories.enrollment_repository import (
    EnrollmentRepository,
)
from tests.modules.offer.conftest import create_product_model

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

_TENANT_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_TENANT_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


@pytest.fixture
def tenant_a() -> uuid.UUID:
    return _TENANT_A


@pytest.fixture
def tenant_b() -> uuid.UUID:
    return _TENANT_B


def _make_offer(db: Session, tenant_id: uuid.UUID) -> uuid.UUID:
    model = create_product_model(tenant_id, archetype="programa")
    db.add(model)
    db.flush()
    return model.id


def _base_enrollment(
    tenant_id: uuid.UUID,
    offer_id: uuid.UUID,
    *,
    edition_id: uuid.UUID | None = None,
    status: EnrollmentStatus = EnrollmentStatus.INTENT,
) -> Enrollment:
    return Enrollment(
        tenant_id=tenant_id,
        offer_id=offer_id,
        edition_id=edition_id or uuid.uuid4(),
        contact_id=uuid.uuid4(),
        status=status,
    )


class TestCreateGet:
    def test_roundtrip(self, db: Session, tenant_a: uuid.UUID) -> None:
        offer_id = _make_offer(db, tenant_a)
        repo = EnrollmentRepository(db)

        created = repo.create(_base_enrollment(tenant_a, offer_id))
        assert created.id is not None

        found = repo.get_by_id(created.id, tenant_a)
        assert found is not None
        assert found.offer_id == offer_id
        assert found.status == EnrollmentStatus.INTENT

    def test_tenant_isolation_on_get(
        self,
        db: Session,
        tenant_a: uuid.UUID,
        tenant_b: uuid.UUID,
    ) -> None:
        offer_id = _make_offer(db, tenant_a)
        repo = EnrollmentRepository(db)

        created = repo.create(_base_enrollment(tenant_a, offer_id))
        assert repo.get_by_id(created.id, tenant_b) is None


class TestWaitlistFilter:
    def test_list_waitlist_only_null_edition(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ) -> None:
        offer_id = _make_offer(db, tenant_a)
        repo = EnrollmentRepository(db)

        # Intent row with edition — should NOT appear in waitlist.
        repo.create(_base_enrollment(tenant_a, offer_id))

        # Waitlist row (no edition).
        waitlist = Enrollment(
            tenant_id=tenant_a,
            offer_id=offer_id,
            edition_id=None,
            contact_id=uuid.uuid4(),
            status=EnrollmentStatus.WAITLIST,
        )
        repo.create(waitlist)

        rows = repo.list_waitlist(offer_id, tenant_a)
        assert len(rows) == 1
        assert rows[0].status == EnrollmentStatus.WAITLIST
        assert rows[0].edition_id is None


class TestUpdate:
    def test_mark_paid_persists_payment(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ) -> None:
        from datetime import datetime, timezone

        offer_id = _make_offer(db, tenant_a)
        repo = EnrollmentRepository(db)

        created = repo.create(
            _base_enrollment(tenant_a, offer_id, status=EnrollmentStatus.PAYMENT_PENDING),
        )
        updated = repo.update(
            created.id,
            tenant_a,
            {
                "status": EnrollmentStatus.PAID,
                "payment_provider": PaymentProvider.STRIPE,
                "payment_transaction_id": "tx_test_1",
                "paid_at": datetime(2026, 5, 1, tzinfo=timezone.utc),
            },
        )

        assert updated.status == EnrollmentStatus.PAID
        assert updated.payment_provider == PaymentProvider.STRIPE
        assert updated.payment_transaction_id == "tx_test_1"
        assert updated.paid_at is not None


class TestListByOffer:
    def test_filter_by_edition_and_status(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ) -> None:
        offer_id = _make_offer(db, tenant_a)
        repo = EnrollmentRepository(db)

        edition_a = uuid.uuid4()
        edition_b = uuid.uuid4()

        repo.create(_base_enrollment(tenant_a, offer_id, edition_id=edition_a))
        repo.create(_base_enrollment(tenant_a, offer_id, edition_id=edition_b))

        rows_a = repo.list_by_offer(offer_id, tenant_a, edition_id=edition_a)
        assert len(rows_a) == 1
        assert rows_a[0].edition_id == edition_a
