"""Tests for appointment EventBus bridge.

Covers: appointment_booked -> meeting_booked journey_event,
appointment_no_show -> meeting_no_show journey_event,
and EventBus subscription registration.
"""

import uuid
from unittest.mock import MagicMock, patch, call

import pytest

from src.shared.domain.events import DomainEvent, EventBus

# Pre-import models to register them with SQLAlchemy mapper
# (prevents lazy relationship resolution errors in tests)
import src.modules.iam.infrastructure.models.tenant_model  # noqa: F401
import src.modules.crm.infrastructure.models.customer_model  # noqa: F401
import src.modules.crm.infrastructure.models.lead_model  # noqa: F401
try:
    import src.modules.sales_agent.infrastructure.models.message_model  # noqa: F401
    import src.modules.sales_agent.infrastructure.models.channel_model  # noqa: F401
except ImportError:
    pass
import src.modules.scheduling.infrastructure.models.appointment_model  # noqa: F401
import src.modules.crm.infrastructure.models.lifecycle_transition_model  # noqa: F401
try:
    import src.modules.crm.infrastructure.models.sale_model  # noqa: F401
    import src.modules.offer.infrastructure.models.product_model  # noqa: F401
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_appointment_event(
    tenant_id: uuid.UUID,
    lead_id: uuid.UUID,
    appointment_id: uuid.UUID,
    status: str,
) -> DomainEvent:
    """Create an AppointmentEvent using the domain factory."""
    from src.modules.crm.domain.events import AppointmentEvent

    return AppointmentEvent.create(
        tenant_id=tenant_id,
        lead_id=lead_id,
        appointment_id=appointment_id,
        appointment_status=status,
    )


def _mock_lead(email: str = "lead@example.com"):
    lead = MagicMock()
    lead.email = email
    return lead


def _mock_profile(profile_id: uuid.UUID | None = None):
    profile = MagicMock()
    profile.id = profile_id or uuid.uuid4()
    profile.is_inactive = False
    return profile


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_appointment_event_factory():
    """AppointmentEvent.create maps status to correct event_name."""
    from src.modules.crm.domain.events import AppointmentEvent

    tid = uuid.uuid4()
    lid = uuid.uuid4()
    aid = uuid.uuid4()

    booked = AppointmentEvent.create(tid, lid, aid, "SCHEDULED")
    assert booked.event_name == "appointment_booked"
    assert booked.tenant_id == tid
    assert booked.payload["lead_id"] == str(lid)
    assert booked.payload["appointment_id"] == str(aid)

    completed = AppointmentEvent.create(tid, lid, aid, "COMPLETED")
    assert completed.event_name == "appointment_completed"

    no_show = AppointmentEvent.create(tid, lid, aid, "NO_SHOW")
    assert no_show.event_name == "appointment_no_show"

    cancelled = AppointmentEvent.create(tid, lid, aid, "CANCELLED")
    assert cancelled.event_name == "appointment_cancelled"


def test_appointment_booked_creates_journey_event():
    """handle_appointment_booked creates a JourneyEventModel with event_name='meeting_booked'."""
    tenant_id = uuid.uuid4()
    lead_id = uuid.uuid4()
    appointment_id = uuid.uuid4()
    profile_id = uuid.uuid4()

    event = _make_appointment_event(tenant_id, lead_id, appointment_id, "SCHEDULED")
    lead = _mock_lead()
    profile = _mock_profile(profile_id)

    mock_db = MagicMock()

    # First db.execute: find lead by ID
    # Second db.execute: find profile by email
    mock_db.execute.side_effect = [
        MagicMock(scalar_one_or_none=MagicMock(return_value=lead)),
        MagicMock(scalar_one_or_none=MagicMock(return_value=profile)),
    ]

    with patch(
        "src.core.database.SessionLocal",
        return_value=mock_db,
    ), patch(
        "src.modules.crm.application.services.lifecycle_service.LifecycleService.recalculate_score",
        return_value=None,
    ):
        from src.modules.crm.application.event_handlers import handle_appointment_booked

        handle_appointment_booked(event)

    # Verify JourneyEventModel was added
    mock_db.add.assert_called_once()
    je = mock_db.add.call_args[0][0]
    assert je.event_name == "meeting_booked"
    assert je.event_type == "track"
    assert je.properties["source"] == "scheduling"
    assert je.properties["appointment_id"] == str(appointment_id)
    assert je.properties["lead_id"] == str(lead_id)
    assert je.tenant_id == tenant_id
    assert je.profile_id == profile_id

    mock_db.commit.assert_called_once()


def test_appointment_no_show_creates_journey_event():
    """handle_appointment_no_show creates a JourneyEventModel with event_name='meeting_no_show'."""
    tenant_id = uuid.uuid4()
    lead_id = uuid.uuid4()
    appointment_id = uuid.uuid4()
    profile_id = uuid.uuid4()

    event = _make_appointment_event(tenant_id, lead_id, appointment_id, "NO_SHOW")
    lead = _mock_lead()
    profile = _mock_profile(profile_id)

    mock_db = MagicMock()
    mock_db.execute.side_effect = [
        MagicMock(scalar_one_or_none=MagicMock(return_value=lead)),
        MagicMock(scalar_one_or_none=MagicMock(return_value=profile)),
    ]

    with patch(
        "src.core.database.SessionLocal",
        return_value=mock_db,
    ), patch(
        "src.modules.crm.application.services.lifecycle_service.LifecycleService.recalculate_score",
        return_value=None,
    ):
        from src.modules.crm.application.event_handlers import handle_appointment_no_show

        handle_appointment_no_show(event)

    je = mock_db.add.call_args[0][0]
    assert je.event_name == "meeting_no_show"
    assert je.properties["status"] == "NO_SHOW"


def test_eventbus_subscription_registered():
    """register_event_handlers subscribes all appointment event names."""
    # Clear existing handlers for isolation
    EventBus.clear()

    from src.modules.crm.application.event_handlers import register_event_handlers

    register_event_handlers()

    # Verify that appointment event names are registered
    assert "appointment_booked" in EventBus._handlers
    assert "appointment_completed" in EventBus._handlers
    assert "appointment_no_show" in EventBus._handlers

    # Also verify existing handlers still registered
    assert "sale_completed" in EventBus._handlers
    assert "churn_detected" in EventBus._handlers
    assert "lead_captured" in EventBus._handlers

    # Clean up
    EventBus.clear()
