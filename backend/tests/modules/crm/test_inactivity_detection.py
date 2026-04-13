"""
Tests for InactivityService: batch inactivity detection and score decay.

CRM-04: Profiles inactive 14+ days flagged, 5%/day score decay,
CUSTOMER decay paused, backward transitions on threshold crossing.
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.crm.application.services.inactivity_service import InactivityService
from src.modules.crm.domain.enums import LifecycleStage
from src.modules.crm.domain.scoring import DECAY_CONFIG, INACTIVITY_CONFIG
from src.modules.crm.infrastructure.models.customer_model import (
    CustomerProfileModel,
)
from src.modules.crm.infrastructure.models.lifecycle_transition_model import (
    LifecycleTransitionModel,
)

SAMPLE_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_profile(
    db: Session,
    tenant_id: uuid.UUID = SAMPLE_TENANT_ID,
    stage: LifecycleStage = LifecycleStage.SUBSCRIBER,
    score: float = 0.0,
    last_activity_at: datetime | None = None,
    is_inactive: bool = False,
) -> CustomerProfileModel:
    profile = CustomerProfileModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        primary_email=f"{uuid.uuid4().hex[:8]}@test.com",
        full_name="Test User",
        lifecycle_stage=stage,
        lead_score=score,
        lifetime_value=0.0,
        is_inactive=is_inactive,
        last_activity_at=last_activity_at,
        traits={},
        computed_traits={},
    )
    db.add(profile)
    db.flush()
    return profile


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestInactivityDetection:
    """Test is_inactive flag setting based on last_activity_at threshold."""

    def test_flags_inactive_after_threshold(self, db: Session):
        """Profile with last_activity 15 days ago -> is_inactive=True."""
        profile = _make_profile(
            db,
            last_activity_at=datetime.now(timezone.utc) - timedelta(days=15),
        )
        svc = InactivityService(db)
        result = svc.run_batch(tenant_id=SAMPLE_TENANT_ID)

        db.refresh(profile)
        assert profile.is_inactive is True
        assert result["profiles_flagged_inactive"] >= 1

    def test_does_not_flag_active_profile(self, db: Session):
        """Profile with last_activity 5 days ago -> is_inactive=False."""
        profile = _make_profile(
            db,
            last_activity_at=datetime.now(timezone.utc) - timedelta(days=5),
        )
        svc = InactivityService(db)
        svc.run_batch(tenant_id=SAMPLE_TENANT_ID)

        db.refresh(profile)
        assert profile.is_inactive is False

    def test_recovers_previously_inactive(self, db: Session):
        """Inactive profile with new activity -> is_inactive=False."""
        profile = _make_profile(
            db,
            is_inactive=True,
            last_activity_at=datetime.now(timezone.utc) - timedelta(days=2),
        )
        svc = InactivityService(db)
        result = svc.run_batch(tenant_id=SAMPLE_TENANT_ID)

        db.refresh(profile)
        assert profile.is_inactive is False
        assert result["profiles_recovered"] >= 1

    def test_null_last_activity_treated_as_inactive(self, db: Session):
        """Profile with last_activity_at=NULL -> is_inactive=True."""
        profile = _make_profile(db, last_activity_at=None)
        svc = InactivityService(db)
        svc.run_batch(tenant_id=SAMPLE_TENANT_ID)

        db.refresh(profile)
        assert profile.is_inactive is True


class TestScoreDecay:
    """Test lead_score decay for inactive profiles."""

    def test_score_decay_applied(self, db: Session):
        """Inactive 7 days, score 40 -> ~27.8 (40 * 0.95^7)."""
        profile = _make_profile(
            db,
            stage=LifecycleStage.MQL,
            score=40.0,
            last_activity_at=datetime.now(timezone.utc)
            - timedelta(days=7 + INACTIVITY_CONFIG.inactive_days),
        )
        svc = InactivityService(db)
        svc.run_batch(tenant_id=SAMPLE_TENANT_ID)

        db.refresh(profile)
        # 40 * (1-0.05)^(7+14) = 40 * 0.95^21 ~ 13.6
        # Actually the days_inactive = total days since last activity
        # days_inactive = 21, so score = 40 * 0.95^21
        expected = 40.0 * (1 - DECAY_CONFIG.daily_decay_rate) ** (
            7 + INACTIVITY_CONFIG.inactive_days
        )
        assert abs(profile.lead_score - expected) < 0.1

    def test_decay_clamps_to_floor(self, db: Session):
        """Very old inactive profile -> score = 0.0."""
        profile = _make_profile(
            db,
            score=10.0,
            last_activity_at=datetime.now(timezone.utc) - timedelta(days=365),
        )
        svc = InactivityService(db)
        svc.run_batch(tenant_id=SAMPLE_TENANT_ID)

        db.refresh(profile)
        assert profile.lead_score == DECAY_CONFIG.min_score

    def test_customer_decay_paused(self, db: Session):
        """CUSTOMER profile inactive but score unchanged."""
        original_score = 80.0
        profile = _make_profile(
            db,
            stage=LifecycleStage.CUSTOMER,
            score=original_score,
            last_activity_at=datetime.now(timezone.utc) - timedelta(days=30),
        )
        svc = InactivityService(db)
        svc.run_batch(tenant_id=SAMPLE_TENANT_ID)

        db.refresh(profile)
        assert profile.lead_score == original_score

    def test_customer_still_flagged_inactive(self, db: Session):
        """CUSTOMER profile gets is_inactive=True despite no decay."""
        profile = _make_profile(
            db,
            stage=LifecycleStage.CUSTOMER,
            score=80.0,
            last_activity_at=datetime.now(timezone.utc) - timedelta(days=30),
        )
        svc = InactivityService(db)
        svc.run_batch(tenant_id=SAMPLE_TENANT_ID)

        db.refresh(profile)
        assert profile.is_inactive is True


class TestDecayTransitions:
    """Test backward stage transitions triggered by score decay."""

    def test_decay_triggers_backward_transition(self, db: Session):
        """MQL(42) decays below MQL threshold (40) -> LEAD, audit record created."""
        # days_inactive such that 42 * 0.95^days < 40
        # 42 * 0.95^1 = 39.9 < 40  => 1 day past threshold sufficient
        days_past_threshold = INACTIVITY_CONFIG.inactive_days + 1
        profile = _make_profile(
            db,
            stage=LifecycleStage.MQL,
            score=42.0,
            last_activity_at=datetime.now(timezone.utc)
            - timedelta(days=days_past_threshold),
        )
        svc = InactivityService(db)
        result = svc.run_batch(tenant_id=SAMPLE_TENANT_ID)

        db.refresh(profile)
        # Score should be decayed: 42 * 0.95^(days_past_threshold)
        # Stage should be LEAD now (decayed below 40)
        assert profile.lifecycle_stage == LifecycleStage.LEAD
        assert result["transitions"] >= 1

        # Check audit record
        transitions = (
            db.execute(
                select(LifecycleTransitionModel).where(
                    LifecycleTransitionModel.profile_id == profile.id,
                    LifecycleTransitionModel.triggered_by == "decay",
                ),
            )
            .scalars()
            .all()
        )
        assert len(transitions) >= 1
        assert transitions[0].from_stage == LifecycleStage.MQL
        assert transitions[0].to_stage == LifecycleStage.LEAD


class TestBatchProcessing:
    """Test batch processing behavior."""

    def test_batch_processes_in_chunks(self, db: Session):
        """Verify batch processing works with multiple profiles."""
        # Create 10 profiles (not 500+ to keep test fast)
        profiles = []
        for _ in range(10):
            p = _make_profile(
                db,
                last_activity_at=datetime.now(timezone.utc) - timedelta(days=20),
            )
            profiles.append(p)

        svc = InactivityService(db)
        result = svc.run_batch(tenant_id=SAMPLE_TENANT_ID)

        assert result["profiles_flagged_inactive"] >= 10

    def test_run_batch_all_tenants(self, db: Session):
        """run_batch(tenant_id=None) processes all tenants."""
        tenant_a = uuid.UUID("00000000-0000-0000-0000-00000000000a")
        tenant_b = uuid.UUID("00000000-0000-0000-0000-00000000000b")

        p_a = _make_profile(
            db,
            tenant_id=tenant_a,
            last_activity_at=datetime.now(timezone.utc) - timedelta(days=20),
        )
        p_b = _make_profile(
            db,
            tenant_id=tenant_b,
            last_activity_at=datetime.now(timezone.utc) - timedelta(days=20),
        )

        svc = InactivityService(db)
        svc.run_batch(tenant_id=None)

        db.refresh(p_a)
        db.refresh(p_b)
        assert p_a.is_inactive is True
        assert p_b.is_inactive is True
