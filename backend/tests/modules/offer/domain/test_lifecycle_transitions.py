"""Tests for the offer lifecycle state machine (pure domain)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from src.modules.offer.domain.lifecycle import (
    LIFECYCLE_TRANSITIONS,
    InvalidLifecycleTransitionError,
    OfferLifecycleStatus,
    OfferLifecycleTransition,
    is_transition_allowed,
)


class TestLifecycleTransitions:
    @pytest.mark.parametrize(
        "from_status,to_status,expected",
        [
            # Allowed
            (OfferLifecycleStatus.DRAFT, OfferLifecycleStatus.ACTIVE, True),
            (OfferLifecycleStatus.DRAFT, OfferLifecycleStatus.ARCHIVED, True),
            (OfferLifecycleStatus.ACTIVE, OfferLifecycleStatus.PAUSED, True),
            (OfferLifecycleStatus.ACTIVE, OfferLifecycleStatus.DRAFT, True),
            (OfferLifecycleStatus.ACTIVE, OfferLifecycleStatus.ARCHIVED, True),
            (OfferLifecycleStatus.PAUSED, OfferLifecycleStatus.ACTIVE, True),
            (OfferLifecycleStatus.PAUSED, OfferLifecycleStatus.DRAFT, True),
            (OfferLifecycleStatus.PAUSED, OfferLifecycleStatus.ARCHIVED, True),
            # Forbidden
            (OfferLifecycleStatus.DRAFT, OfferLifecycleStatus.PAUSED, False),
            (OfferLifecycleStatus.ARCHIVED, OfferLifecycleStatus.ACTIVE, False),
            (OfferLifecycleStatus.ARCHIVED, OfferLifecycleStatus.DRAFT, False),
            (OfferLifecycleStatus.ARCHIVED, OfferLifecycleStatus.PAUSED, False),
        ],
    )
    def test_is_transition_allowed(
        self,
        from_status: OfferLifecycleStatus,
        to_status: OfferLifecycleStatus,
        expected: bool,
    ) -> None:
        assert is_transition_allowed(from_status, to_status) is expected

    def test_same_status_is_allowed_noop(self) -> None:
        for status in OfferLifecycleStatus:
            assert is_transition_allowed(status, status) is True

    def test_archived_is_terminal(self) -> None:
        assert LIFECYCLE_TRANSITIONS[OfferLifecycleStatus.ARCHIVED] == set()

    def test_invalid_transition_error_message(self) -> None:
        err = InvalidLifecycleTransitionError(
            OfferLifecycleStatus.DRAFT, OfferLifecycleStatus.PAUSED
        )
        assert "draft" in str(err)
        assert "paused" in str(err)
        assert err.from_status is OfferLifecycleStatus.DRAFT
        assert err.to_status is OfferLifecycleStatus.PAUSED


class TestOfferLifecycleTransitionValueObject:
    def test_is_archival_true_for_archived_target(self) -> None:
        transition = OfferLifecycleTransition(
            offer_id=uuid4(),
            tenant_id=uuid4(),
            from_status=OfferLifecycleStatus.ACTIVE,
            to_status=OfferLifecycleStatus.ARCHIVED,
            occurred_at=datetime.now(timezone.utc),
        )
        assert transition.is_archival() is True

    def test_is_archival_false_for_non_archived(self) -> None:
        transition = OfferLifecycleTransition(
            offer_id=uuid4(),
            tenant_id=uuid4(),
            from_status=OfferLifecycleStatus.DRAFT,
            to_status=OfferLifecycleStatus.ACTIVE,
            occurred_at=datetime.now(timezone.utc),
        )
        assert transition.is_archival() is False
