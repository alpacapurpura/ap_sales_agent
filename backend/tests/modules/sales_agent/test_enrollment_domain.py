"""Domain invariants for the Enrollment entity (Phase 5)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.modules.sales_agent.domain.enrollment import (
    Enrollment,
    EnrollmentStatus,
    PaymentProvider,
)

_TENANT = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_OFFER = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_EDITION = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_CONTACT = uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")


def _base_kwargs(**overrides) -> dict:
    defaults = {
        "tenant_id": _TENANT,
        "offer_id": _OFFER,
        "edition_id": _EDITION,
        "contact_id": _CONTACT,
        "status": EnrollmentStatus.INTENT,
    }
    defaults.update(overrides)
    return defaults


class TestWaitlistInvariant:
    """``status == WAITLIST`` ⇔ ``edition_id IS NULL``."""

    def test_waitlist_without_edition_ok(self) -> None:
        enrollment = Enrollment(
            **_base_kwargs(edition_id=None, status=EnrollmentStatus.WAITLIST),
        )
        assert enrollment.status == EnrollmentStatus.WAITLIST
        assert enrollment.edition_id is None

    def test_waitlist_with_edition_rejected(self) -> None:
        with pytest.raises(ValidationError, match="waitlist"):
            Enrollment(**_base_kwargs(status=EnrollmentStatus.WAITLIST))

    def test_non_waitlist_without_edition_rejected(self) -> None:
        with pytest.raises(ValidationError, match="edition_id"):
            Enrollment(**_base_kwargs(edition_id=None, status=EnrollmentStatus.INTENT))


class TestPaidInvariants:
    """``PAID`` and ``ATTENDED`` require ``paid_at``."""

    def test_paid_requires_paid_at(self) -> None:
        with pytest.raises(ValidationError, match="paid_at"):
            Enrollment(**_base_kwargs(status=EnrollmentStatus.PAID))

    def test_attended_requires_paid_at(self) -> None:
        with pytest.raises(ValidationError, match="paid_at"):
            Enrollment(**_base_kwargs(status=EnrollmentStatus.ATTENDED))

    def test_paid_with_paid_at_ok(self) -> None:
        enrollment = Enrollment(
            **_base_kwargs(
                status=EnrollmentStatus.PAID,
                paid_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
                payment_provider=PaymentProvider.STRIPE,
            ),
        )
        assert enrollment.paid_at is not None


class TestTransitions:
    """Mutation helper ``with_status`` respects invariants."""

    def test_mark_paid_sets_paid_at(self) -> None:
        enrollment = Enrollment(**_base_kwargs(status=EnrollmentStatus.PAYMENT_PENDING))
        updated = enrollment.mark_paid(
            provider=PaymentProvider.STRIPE,
            transaction_id="tx_123",
            now=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )
        assert updated.status == EnrollmentStatus.PAID
        assert updated.paid_at == datetime(2026, 5, 1, tzinfo=timezone.utc)
        assert updated.payment_provider == PaymentProvider.STRIPE
        assert updated.payment_transaction_id == "tx_123"

    def test_promote_waitlist_attaches_edition(self) -> None:
        enrollment = Enrollment(
            **_base_kwargs(edition_id=None, status=EnrollmentStatus.WAITLIST),
        )
        promoted = enrollment.promote_to_edition(_EDITION)
        assert promoted.status == EnrollmentStatus.PAYMENT_PENDING
        assert promoted.edition_id == _EDITION
