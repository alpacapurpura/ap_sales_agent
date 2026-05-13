"""
Tests for LifecycleRepository get_transitions_by_profile.

CRM-05: Transition retrieval — ordered by occurred_at desc, limit, tenant isolation.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from luana_core_crm.domain.enums import LifecycleStage
from luana_core_crm.infrastructure.models.customer_model import CustomerProfileModel
from luana_core_crm.infrastructure.models.lifecycle_transition_model import (
    LifecycleTransitionModel,
)
from luana_core_crm.infrastructure.repositories.lifecycle_repository import (
    LifecycleRepository,
)

SAMPLE_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
OTHER_TENANT_ID = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_profile(db: Session, tenant_id: uuid.UUID) -> CustomerProfileModel:
    profile = CustomerProfileModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        primary_email=f"{uuid.uuid4().hex[:8]}@test.com",
        full_name="Test User",
        lifecycle_stage=LifecycleStage.SUBSCRIBER,
        lead_score=0.0,
        lifetime_value=0.0,
        is_inactive=False,
        traits={},
        computed_traits={},
    )
    db.add(profile)
    db.flush()
    return profile


def _add_transition(
    db: Session,
    profile_id: uuid.UUID,
    tenant_id: uuid.UUID,
    from_stage: LifecycleStage | None,
    to_stage: LifecycleStage,
    occurred_at: datetime,
    reason: str = "test",
) -> LifecycleTransitionModel:
    t = LifecycleTransitionModel(
        id=uuid.uuid4(),
        profile_id=profile_id,
        tenant_id=tenant_id,
        from_stage=from_stage,
        to_stage=to_stage,
        reason=reason,
        triggered_by="test",
        occurred_at=occurred_at,
    )
    db.add(t)
    db.flush()
    return t


# ---------------------------------------------------------------------------
# get_transitions_by_profile
# ---------------------------------------------------------------------------


class TestGetTransitionsByProfile:
    """Returns transitions ordered by occurred_at desc, with limit and tenant isolation."""

    def test_returns_transitions_ordered_desc(self, db: Session, tenant_id):
        """Most recent transition appears first."""
        profile = _make_profile(db, tenant_id)
        now = datetime.now(timezone.utc)
        _add_transition(
            db, profile.id, tenant_id, LifecycleStage.SUBSCRIBER, LifecycleStage.LEAD, now - timedelta(days=2)
        )
        _add_transition(db, profile.id, tenant_id, LifecycleStage.LEAD, LifecycleStage.MQL, now - timedelta(days=1))
        _add_transition(db, profile.id, tenant_id, LifecycleStage.MQL, LifecycleStage.SQL, now)

        repo = LifecycleRepository(db)
        transitions = repo.get_transitions_by_profile(profile.id, tenant_id)

        assert len(transitions) == 3
        assert transitions[0].to_stage == LifecycleStage.SQL
        assert transitions[1].to_stage == LifecycleStage.MQL
        assert transitions[2].to_stage == LifecycleStage.LEAD

    def test_applies_limit(self, db: Session, tenant_id):
        """Limit caps the number of returned transitions."""
        profile = _make_profile(db, tenant_id)
        now = datetime.now(timezone.utc)
        for i in range(5):
            _add_transition(
                db,
                profile.id,
                tenant_id,
                LifecycleStage.SUBSCRIBER,
                LifecycleStage.LEAD,
                now - timedelta(days=i),
                reason=f"transition_{i}",
            )

        repo = LifecycleRepository(db)
        transitions = repo.get_transitions_by_profile(profile.id, tenant_id, limit=2)

        assert len(transitions) == 2
        # Most recent two
        assert transitions[0].reason == "transition_0"
        assert transitions[1].reason == "transition_1"

    def test_tenant_isolation(self, db: Session, tenant_id):
        """Transitions from another tenant are not returned."""
        profile_a = _make_profile(db, tenant_id)
        profile_b = _make_profile(db, OTHER_TENANT_ID)
        now = datetime.now(timezone.utc)

        _add_transition(db, profile_a.id, tenant_id, LifecycleStage.SUBSCRIBER, LifecycleStage.LEAD, now)
        _add_transition(db, profile_b.id, OTHER_TENANT_ID, LifecycleStage.SUBSCRIBER, LifecycleStage.LEAD, now)

        repo = LifecycleRepository(db)
        transitions_a = repo.get_transitions_by_profile(profile_a.id, tenant_id)
        transitions_b = repo.get_transitions_by_profile(profile_b.id, OTHER_TENANT_ID)

        assert len(transitions_a) == 1
        assert transitions_a[0].tenant_id == tenant_id
        assert len(transitions_b) == 1
        assert transitions_b[0].tenant_id == OTHER_TENANT_ID

    def test_returns_empty_for_profile_without_transitions(self, db: Session, tenant_id):
        """Profile with no transitions returns empty list."""
        profile = _make_profile(db, tenant_id)
        repo = LifecycleRepository(db)
        transitions = repo.get_transitions_by_profile(profile.id, tenant_id)
        assert transitions == []

    def test_does_not_return_transitions_from_other_profile_same_tenant(self, db: Session, tenant_id):
        """Transitions for a different profile in the same tenant are excluded."""
        profile_a = _make_profile(db, tenant_id)
        profile_b = _make_profile(db, tenant_id)
        now = datetime.now(timezone.utc)

        _add_transition(db, profile_a.id, tenant_id, LifecycleStage.SUBSCRIBER, LifecycleStage.LEAD, now)
        _add_transition(db, profile_b.id, tenant_id, LifecycleStage.SUBSCRIBER, LifecycleStage.MQL, now)

        repo = LifecycleRepository(db)
        transitions_a = repo.get_transitions_by_profile(profile_a.id, tenant_id)

        assert len(transitions_a) == 1
        assert transitions_a[0].to_stage == LifecycleStage.LEAD
