"""
Tests for churn detection and manual override.

CRM-05: Cancellation events trigger CHURNED stage, inactivity is independent,
manual override API with audit trail.
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.crm.application.services.lifecycle_service import LifecycleService
from src.modules.crm.domain.enums import LifecycleStage
from src.modules.crm.infrastructure.models.customer_model import CustomerProfileModel
from src.modules.crm.infrastructure.models.lifecycle_transition_model import (
    LifecycleTransitionModel,
)
from src.shared.domain.events import DomainEvent

SAMPLE_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_profile(
    db: Session,
    tenant_id: uuid.UUID = SAMPLE_TENANT_ID,
    stage: LifecycleStage = LifecycleStage.CUSTOMER,
    score: float = 80.0,
    is_inactive: bool = False,
) -> CustomerProfileModel:
    profile = CustomerProfileModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        primary_email=f"{uuid.uuid4().hex[:8]}@test.com",
        full_name="Test User",
        lifecycle_stage=stage,
        lead_score=score,
        lifetime_value=99.0,
        is_inactive=is_inactive,
        first_conversion_at=datetime.now(timezone.utc) - timedelta(days=30),
        last_activity_at=datetime.now(timezone.utc) - timedelta(days=5),
        traits={},
        computed_traits={},
    )
    db.add(profile)
    db.flush()
    return profile


def _make_churn_event(
    tenant_id: uuid.UUID,
    profile_id: uuid.UUID,
    source: str = "shopify",
    subscription_id: str = "sub_123",
    cancellation_reason: str = "customer_requested",
) -> DomainEvent:
    return DomainEvent(
        event_name="churn_detected",
        tenant_id=tenant_id,
        payload={
            "profile_id": str(profile_id),
            "source": source,
            "subscription_id": subscription_id,
            "cancellation_reason": cancellation_reason,
        },
    )


# ---------------------------------------------------------------------------
# Tests: Churn Detection
# ---------------------------------------------------------------------------


class TestChurnDetection:
    """Test subscription cancellation -> CHURNED lifecycle stage."""

    def test_churn_event_sets_churned_stage(self, db: Session):
        """CUSTOMER profile + churn event -> CHURNED."""
        profile = _make_profile(db)
        event = _make_churn_event(SAMPLE_TENANT_ID, profile.id)

        svc = LifecycleService(db)
        svc.handle_churn_event(event)
        db.flush()

        db.refresh(profile)
        assert profile.lifecycle_stage == LifecycleStage.CHURNED

    def test_churn_event_creates_audit_record(self, db: Session):
        """Verify lifecycle_transition with triggered_by='churn_event'."""
        profile = _make_profile(db)
        event = _make_churn_event(SAMPLE_TENANT_ID, profile.id)

        svc = LifecycleService(db)
        svc.handle_churn_event(event)
        db.flush()

        transitions = (
            db.execute(
                select(LifecycleTransitionModel).where(
                    LifecycleTransitionModel.profile_id == profile.id,
                    LifecycleTransitionModel.triggered_by == "churn_event",
                )
            )
            .scalars()
            .all()
        )
        assert len(transitions) == 1
        assert transitions[0].from_stage == LifecycleStage.CUSTOMER
        assert transitions[0].to_stage == LifecycleStage.CHURNED
        meta = transitions[0].transition_metadata or {}
        assert meta.get("source") == "shopify"
        assert meta.get("subscription_id") == "sub_123"

    def test_churn_event_idempotent(self, db: Session):
        """Already CHURNED profile + churn event -> no duplicate transition."""
        profile = _make_profile(db, stage=LifecycleStage.CHURNED)
        event = _make_churn_event(SAMPLE_TENANT_ID, profile.id)

        svc = LifecycleService(db)
        svc.handle_churn_event(event)
        db.flush()

        transitions = (
            db.execute(
                select(LifecycleTransitionModel).where(
                    LifecycleTransitionModel.profile_id == profile.id,
                )
            )
            .scalars()
            .all()
        )
        assert len(transitions) == 0

    def test_inactivity_does_not_trigger_churn(self, db: Session):
        """is_inactive=True but lifecycle_stage unchanged (not CHURNED)."""
        profile = _make_profile(db, is_inactive=True, stage=LifecycleStage.CUSTOMER)

        # No churn event fired -- just inactivity flag set
        db.refresh(profile)
        assert profile.is_inactive is True
        assert profile.lifecycle_stage == LifecycleStage.CUSTOMER

    def test_churn_from_any_stage(self, db: Session):
        """SQL profile + churn event -> CHURNED (not just CUSTOMER)."""
        profile = _make_profile(db, stage=LifecycleStage.SQL, score=75.0)
        event = _make_churn_event(SAMPLE_TENANT_ID, profile.id)

        svc = LifecycleService(db)
        svc.handle_churn_event(event)
        db.flush()

        db.refresh(profile)
        assert profile.lifecycle_stage == LifecycleStage.CHURNED


# ---------------------------------------------------------------------------
# Tests: Manual Override
# ---------------------------------------------------------------------------


class TestManualOverride:
    """Test force_stage manual override with audit trail."""

    def test_manual_override_changes_stage(self, db: Session):
        """force_stage from LEAD to MQL, triggered_by='manual'."""
        profile = _make_profile(db, stage=LifecycleStage.LEAD, score=30.0)

        svc = LifecycleService(db)
        svc.force_stage(
            profile_id=profile.id,
            tenant_id=SAMPLE_TENANT_ID,
            new_stage=LifecycleStage.MQL,
            admin_user_id="admin-001",
            note="Manual promotion for testing",
        )
        db.flush()

        db.refresh(profile)
        assert profile.lifecycle_stage == LifecycleStage.MQL

    def test_manual_override_audit_trail(self, db: Session):
        """Verify metadata contains admin_user_id and note."""
        profile = _make_profile(db, stage=LifecycleStage.LEAD, score=30.0)

        svc = LifecycleService(db)
        svc.force_stage(
            profile_id=profile.id,
            tenant_id=SAMPLE_TENANT_ID,
            new_stage=LifecycleStage.MQL,
            admin_user_id="admin-001",
            note="Promoted for VIP event",
        )
        db.flush()

        transitions = (
            db.execute(
                select(LifecycleTransitionModel).where(
                    LifecycleTransitionModel.profile_id == profile.id,
                    LifecycleTransitionModel.triggered_by == "manual",
                )
            )
            .scalars()
            .all()
        )
        assert len(transitions) == 1
        meta = transitions[0].transition_metadata or {}
        assert meta.get("admin_user_id") == "admin-001"
        assert meta.get("note") == "Promoted for VIP event"
