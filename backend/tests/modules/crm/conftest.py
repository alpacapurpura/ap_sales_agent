"""
CRM test fixtures.

Provides sample CustomerProfileModel, JourneyEventModel, and LifecycleTransitionModel
instances for use across CRM test modules (plans 02 and 03).
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from luana_core_crm.domain.enums import LifecycleStage
from luana_core_crm.infrastructure.models.customer_model import (
    CustomerProfileModel,
    JourneyEventModel,
)
from luana_core_crm.infrastructure.models.lifecycle_transition_model import (
    LifecycleTransitionModel,
)

SAMPLE_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def tenant_id() -> uuid.UUID:
    return SAMPLE_TENANT_ID


@pytest.fixture
def sample_profile(db: Session, tenant_id: uuid.UUID) -> CustomerProfileModel:
    """A basic SUBSCRIBER profile with default scoring fields."""
    profile = CustomerProfileModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        primary_email="test@example.com",
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


@pytest.fixture
def sample_mql_profile(db: Session, tenant_id: uuid.UUID) -> CustomerProfileModel:
    """A profile at MQL stage with score above MQL threshold."""
    profile = CustomerProfileModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        primary_email="mql@example.com",
        full_name="MQL User",
        lifecycle_stage=LifecycleStage.MQL,
        lead_score=45.0,
        lifetime_value=0.0,
        is_inactive=False,
        last_activity_at=datetime.now(timezone.utc),
        traits={},
        computed_traits={},
    )
    db.add(profile)
    db.flush()
    return profile


@pytest.fixture
def sample_customer_profile(db: Session, tenant_id: uuid.UUID) -> CustomerProfileModel:
    """A profile at CUSTOMER stage (sale-driven, decay paused)."""
    profile = CustomerProfileModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        primary_email="customer@example.com",
        full_name="Customer User",
        lifecycle_stage=LifecycleStage.CUSTOMER,
        lead_score=80.0,
        lifetime_value=99.0,
        is_inactive=False,
        first_conversion_at=datetime.now(timezone.utc) - timedelta(days=30),
        last_activity_at=datetime.now(timezone.utc) - timedelta(days=5),
        traits={},
        computed_traits={},
    )
    db.add(profile)
    db.flush()
    return profile


@pytest.fixture
def sample_journey_events(
    db: Session,
    sample_profile: CustomerProfileModel,
    tenant_id: uuid.UUID,
) -> list:
    """A set of journey events for the sample_profile."""
    events = [
        JourneyEventModel(
            id=uuid.uuid4(),
            profile_id=sample_profile.id,
            tenant_id=tenant_id,
            event_name="page_view",
            event_type="track",
            properties={"page": "/landing"},
            occurred_at=datetime.now(timezone.utc) - timedelta(days=3),
        ),
        JourneyEventModel(
            id=uuid.uuid4(),
            profile_id=sample_profile.id,
            tenant_id=tenant_id,
            event_name="email_opened",
            event_type="track",
            properties={"campaign": "welcome"},
            occurred_at=datetime.now(timezone.utc) - timedelta(days=2),
        ),
        JourneyEventModel(
            id=uuid.uuid4(),
            profile_id=sample_profile.id,
            tenant_id=tenant_id,
            event_name="form_submitted",
            event_type="track",
            properties={"form": "contact"},
            occurred_at=datetime.now(timezone.utc) - timedelta(days=1),
        ),
    ]
    db.add_all(events)
    db.flush()
    return events


@pytest.fixture
def sample_transition(
    db: Session,
    sample_profile: CustomerProfileModel,
    tenant_id: uuid.UUID,
) -> LifecycleTransitionModel:
    """A sample lifecycle transition record."""
    transition = LifecycleTransitionModel(
        id=uuid.uuid4(),
        profile_id=sample_profile.id,
        tenant_id=tenant_id,
        from_stage=LifecycleStage.SUBSCRIBER,
        to_stage=LifecycleStage.LEAD,
        reason="Score crossed LEAD threshold (12.0 >= 10)",
        triggered_by="scoring_rule",
        score_at_transition=12.0,
        transition_metadata={
            "score": 12.0,
            "threshold": 10.0,
            "threshold_name": "lead",
        },
    )
    db.add(transition)
    db.flush()
    return transition
