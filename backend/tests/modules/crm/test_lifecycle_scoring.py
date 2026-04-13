"""
Tests for LifecycleService scoring engine with threshold-based transitions.

CRM-01: Score recalculation, stage transitions (forward/backward/skip),
CUSTOMER exemption, audit trail, and journey_event write hook.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.modules.crm.domain.enums import LifecycleStage
from src.modules.crm.infrastructure.models.customer_model import (
    CustomerProfileModel,
    JourneyEventModel,
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
    tenant_id: uuid.UUID,
    stage: LifecycleStage = LifecycleStage.SUBSCRIBER,
    score: float = 0.0,
    traits: dict | None = None,
    computed_traits: dict | None = None,
    lifetime_value: float = 0.0,
) -> CustomerProfileModel:
    profile = CustomerProfileModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        primary_email=f"{uuid.uuid4().hex[:8]}@test.com",
        full_name="Test User",
        lifecycle_stage=stage,
        lead_score=score,
        lifetime_value=lifetime_value,
        is_inactive=False,
        traits=traits or {},
        computed_traits=computed_traits or {},
    )
    db.add(profile)
    db.flush()
    return profile


def _add_events(
    db: Session,
    profile_id: uuid.UUID,
    tenant_id: uuid.UUID,
    event_names: list[str],
) -> list[JourneyEventModel]:
    events = []
    for name in event_names:
        evt = JourneyEventModel(
            id=uuid.uuid4(),
            profile_id=profile_id,
            tenant_id=tenant_id,
            event_name=name,
            event_type="track",
            properties={},
            occurred_at=datetime.now(timezone.utc),
        )
        db.add(evt)
        events.append(evt)
    db.flush()
    return events


# ---------------------------------------------------------------------------
# Score Recalculation
# ---------------------------------------------------------------------------


class TestRecalculateScore:
    """recalculate_score sums event weights and returns the result."""

    def test_recalculate_score_sums_event_weights(self, db: Session, tenant_id):
        """page_view(1) + email_opened(2) + form_submitted(5) = 8.0"""
        from src.modules.crm.application.services.lifecycle_service import (
            LifecycleService,
        )

        profile = _make_profile(db, tenant_id)
        _add_events(
            db,
            profile.id,
            tenant_id,
            ["page_view", "email_opened", "form_submitted"],
        )

        svc = LifecycleService(db)
        score = svc.recalculate_score(profile.id, tenant_id)

        assert score == 8.0
        db.refresh(profile)
        assert profile.lead_score == 8.0

    def test_customer_stage_exempt(self, db: Session, tenant_id):
        """CUSTOMER profile score not recalculated -- returns current score."""
        from src.modules.crm.application.services.lifecycle_service import (
            LifecycleService,
        )

        profile = _make_profile(
            db,
            tenant_id,
            stage=LifecycleStage.CUSTOMER,
            score=80.0,
        )
        _add_events(db, profile.id, tenant_id, ["page_view", "page_view"])

        svc = LifecycleService(db)
        score = svc.recalculate_score(profile.id, tenant_id)

        assert score == 80.0  # unchanged


# ---------------------------------------------------------------------------
# Threshold Transitions
# ---------------------------------------------------------------------------


class TestThresholdTransitions:
    """Stage transitions driven by score thresholds."""

    def test_threshold_transition_subscriber_to_lead(self, db: Session, tenant_id):
        """Score crosses 10 -> SUBSCRIBER to LEAD."""
        from src.modules.crm.application.services.lifecycle_service import (
            LifecycleService,
        )

        profile = _make_profile(db, tenant_id)
        # meeting_requested=10 + page_view=1 = 11
        _add_events(db, profile.id, tenant_id, ["meeting_requested", "page_view"])

        svc = LifecycleService(db)
        svc.recalculate_score(profile.id, tenant_id)

        db.refresh(profile)
        assert profile.lifecycle_stage == LifecycleStage.LEAD

    def test_threshold_transition_lead_to_mql(self, db: Session, tenant_id):
        """Score crosses 40 -> LEAD to MQL."""
        from src.modules.crm.application.services.lifecycle_service import (
            LifecycleService,
        )

        profile = _make_profile(db, tenant_id, stage=LifecycleStage.LEAD, score=35.0)
        # form_submitted(5)*3 + meeting_requested(10)*2 + email_clicked(3)*2 = 15+20+6 = 41
        _add_events(
            db,
            profile.id,
            tenant_id,
            ["form_submitted"] * 3 + ["meeting_requested"] * 2 + ["email_clicked"] * 2,
        )

        svc = LifecycleService(db)
        svc.recalculate_score(profile.id, tenant_id)

        db.refresh(profile)
        assert profile.lifecycle_stage == LifecycleStage.MQL

    def test_threshold_transition_mql_to_sql(self, db: Session, tenant_id):
        """Score crosses 70 -> MQL to SQL."""
        from src.modules.crm.application.services.lifecycle_service import (
            LifecycleService,
        )

        profile = _make_profile(db, tenant_id, stage=LifecycleStage.MQL, score=65.0)
        # demo_requested(10)*7 + page_view(1)*2 = 72
        _add_events(
            db,
            profile.id,
            tenant_id,
            ["demo_requested"] * 7 + ["page_view"] * 2,
        )

        svc = LifecycleService(db)
        svc.recalculate_score(profile.id, tenant_id)

        db.refresh(profile)
        assert profile.lifecycle_stage == LifecycleStage.SQL

    def test_stage_skipping(self, db: Session, tenant_id):
        """Score jumps from 5 to 75 -> goes directly SUBSCRIBER to SQL."""
        from src.modules.crm.application.services.lifecycle_service import (
            LifecycleService,
        )

        profile = _make_profile(db, tenant_id, score=5.0)
        # demo_requested(10)*7 + form_submitted(5) = 75
        _add_events(
            db,
            profile.id,
            tenant_id,
            ["demo_requested"] * 7 + ["form_submitted"],
        )

        svc = LifecycleService(db)
        svc.recalculate_score(profile.id, tenant_id)

        db.refresh(profile)
        assert profile.lifecycle_stage == LifecycleStage.SQL

    def test_backward_transition(self, db: Session, tenant_id):
        """Score drops below threshold -> stage moves back."""
        from src.modules.crm.application.services.lifecycle_service import (
            LifecycleService,
        )

        # MQL profile but only 2 page_views = 2.0 actual event score -> should go to SUBSCRIBER
        profile = _make_profile(db, tenant_id, stage=LifecycleStage.MQL, score=42.0)
        _add_events(db, profile.id, tenant_id, ["page_view", "page_view"])

        svc = LifecycleService(db)
        svc.recalculate_score(profile.id, tenant_id)

        db.refresh(profile)
        assert profile.lead_score == 2.0
        assert profile.lifecycle_stage == LifecycleStage.SUBSCRIBER


# ---------------------------------------------------------------------------
# Audit Trail
# ---------------------------------------------------------------------------


class TestAuditTrail:
    """Every stage transition is recorded in lifecycle_transitions."""

    def test_transition_creates_audit_record(self, db: Session, tenant_id):
        from src.modules.crm.application.services.lifecycle_service import (
            LifecycleService,
        )

        profile = _make_profile(db, tenant_id)
        _add_events(db, profile.id, tenant_id, ["meeting_requested", "page_view"])

        svc = LifecycleService(db)
        svc.recalculate_score(profile.id, tenant_id)

        transitions = (
            db.query(LifecycleTransitionModel)
            .filter(
                LifecycleTransitionModel.profile_id == profile.id,
                LifecycleTransitionModel.tenant_id == tenant_id,
            )
            .all()
        )
        assert len(transitions) == 1
        t = transitions[0]
        assert t.from_stage == LifecycleStage.SUBSCRIBER
        assert t.to_stage == LifecycleStage.LEAD
        assert t.triggered_by == "scoring_rule"
        assert t.score_at_transition is not None


# ---------------------------------------------------------------------------
# Fit Score
# ---------------------------------------------------------------------------


class TestFitScore:
    """Fit score applied once from profile traits."""

    def test_fit_score_applied_once(self, db: Session, tenant_id):
        from src.modules.crm.application.services.lifecycle_service import (
            LifecycleService,
        )

        profile = _make_profile(
            db,
            tenant_id,
            computed_traits={
                "financial_capacity": "high",
                "sophistication_level": "most_aware",
            },
        )
        _add_events(db, profile.id, tenant_id, ["page_view"])

        svc = LifecycleService(db)
        score1 = svc.recalculate_score(profile.id, tenant_id)

        # financial_capacity_high=8 + sophistication_most_aware=8 + page_view=1 = 17
        assert score1 == 17.0

        # Second call should NOT re-add fit score
        score2 = svc.recalculate_score(profile.id, tenant_id)
        assert score2 == 17.0


# ---------------------------------------------------------------------------
# Journey Event Write Hook
# ---------------------------------------------------------------------------


class TestJourneyEventWriteHook:
    """Writing a journey_event via CustomerService.track_event triggers
    recalculate_score automatically and updates last_activity_at."""

    def test_journey_event_write_triggers_recalculation(self, db: Session, tenant_id):
        from src.modules.crm.application.services.customer_service import (
            CustomerService,
        )

        profile = _make_profile(db, tenant_id)
        svc = CustomerService(db)

        svc.track_event(
            profile_id=profile.id,
            tenant_id=tenant_id,
            event_name="form_submitted",
            event_type="track",
        )

        db.refresh(profile)
        assert profile.lead_score == 5.0  # form_submitted weight

    def test_journey_event_write_updates_last_activity_at(self, db: Session, tenant_id):
        from src.modules.crm.application.services.customer_service import (
            CustomerService,
        )

        profile = _make_profile(db, tenant_id)
        assert profile.last_activity_at is None

        svc = CustomerService(db)
        svc.track_event(
            profile_id=profile.id,
            tenant_id=tenant_id,
            event_name="page_view",
            event_type="track",
        )

        db.refresh(profile)
        assert profile.last_activity_at is not None

    def test_journey_event_write_triggers_stage_transition(
        self,
        db: Session,
        tenant_id,
    ):
        """Write enough high-weight events to cross LEAD threshold (>=10)."""
        from src.modules.crm.application.services.customer_service import (
            CustomerService,
        )

        profile = _make_profile(db, tenant_id)
        svc = CustomerService(db)

        # meeting_requested=10 + page_view=1 = 11 -> LEAD
        svc.track_event(profile.id, tenant_id, "meeting_requested", "track")
        svc.track_event(profile.id, tenant_id, "page_view", "track")

        db.refresh(profile)
        assert profile.lifecycle_stage == LifecycleStage.LEAD
        assert profile.lead_score == 11.0
