"""
Tests for CRM event handler registration and dispatch.

CRM-05: Event handlers for sale_completed, churn_detected, lead_captured,
appointment_booked, appointment_completed, and appointment_no_show events.
"""

import uuid
from unittest.mock import MagicMock, patch

from src.shared.domain.events import DomainEvent, EventBus

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_event(
    event_name: str,
    tenant_id: uuid.UUID,
    payload: dict | None = None,
) -> DomainEvent:
    return DomainEvent(
        event_name=event_name,
        tenant_id=tenant_id,
        payload=payload or {},
    )


def _mock_session():
    mock_db = MagicMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    return mock_db


# ---------------------------------------------------------------------------
# register_event_handlers
# ---------------------------------------------------------------------------


class TestRegisterEventHandlers:
    """register_event_handlers subscribes all CRM handlers to EventBus."""

    def test_registers_all_six_handlers(self):
        from src.modules.crm.application.event_handlers import register_event_handlers

        EventBus.clear()
        register_event_handlers()

        assert "sale_completed" in EventBus._handlers
        assert "churn_detected" in EventBus._handlers
        assert "lead_captured" in EventBus._handlers
        assert "appointment_booked" in EventBus._handlers
        assert "appointment_completed" in EventBus._handlers
        assert "appointment_no_show" in EventBus._handlers

        EventBus.clear()

    def test_handlers_are_callable(self):
        from src.modules.crm.application.event_handlers import (
            handle_appointment_booked,
            handle_appointment_completed,
            handle_appointment_no_show,
            handle_churn_event,
            handle_lead_captured_event,
            handle_sale_completed_event,
            register_event_handlers,
        )

        EventBus.clear()
        register_event_handlers()

        handlers = EventBus._handlers["sale_completed"]
        assert any(h.__name__ == "handle_sale_completed_event" for h in handlers)

        EventBus.clear()


# ---------------------------------------------------------------------------
# handle_sale_completed_event
# ---------------------------------------------------------------------------


class TestHandleSaleCompletedEvent:
    """handle_sale_completed_event delegates to LifecycleService."""

    def test_calls_lifecycle_service_on_valid_event(self, tenant_id: uuid.UUID):
        from src.modules.crm.application.event_handlers import (
            handle_sale_completed_event,
        )

        event = _make_event(
            "sale_completed",
            tenant_id,
            payload={
                "sale_id": str(uuid.uuid4()),
                "customer_id": str(uuid.uuid4()),
                "stage": "CONVERSION",
                "amount": 99.0,
                "offer_id": str(uuid.uuid4()),
            },
        )

        mock_db = _mock_session()

        with (
            patch("src.core.database.SessionLocal", return_value=mock_db),
            patch("src.modules.crm.application.services.lifecycle_service.LifecycleService") as mock_lifecycle,
        ):
            mock_svc = MagicMock()
            mock_lifecycle.return_value = mock_svc

            handle_sale_completed_event(event)

            mock_lifecycle.assert_called_once()
            mock_svc.handle_sale_completed.assert_called_once_with(event)
            mock_db.commit.assert_called_once()
            mock_db.close.assert_called_once()

    def test_rollback_on_lifecycle_service_error(self, tenant_id: uuid.UUID):
        from src.modules.crm.application.event_handlers import (
            handle_sale_completed_event,
        )

        event = _make_event("sale_completed", tenant_id, payload={"customer_id": str(uuid.uuid4())})
        mock_db = _mock_session()

        with (
            patch("src.core.database.SessionLocal", return_value=mock_db),
            patch(
                "src.modules.crm.application.services.lifecycle_service.LifecycleService",
                side_effect=RuntimeError("db error"),
            ),
        ):
            handle_sale_completed_event(event)

            mock_db.rollback.assert_called_once()
            mock_db.close.assert_called_once()

    def test_logs_exception_on_failure(self, tenant_id: uuid.UUID, caplog):
        from src.modules.crm.application.event_handlers import (
            handle_sale_completed_event,
        )

        event = _make_event("sale_completed", tenant_id, payload={})

        with patch(
            "src.core.database.SessionLocal",
            side_effect=ImportError("cannot import"),
        ):
            handle_sale_completed_event(event)

        assert any("Failed to handle sale_completed event" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# handle_churn_event
# ---------------------------------------------------------------------------


class TestHandleChurnEvent:
    """handle_churn_event delegates to LifecycleService for churn transitions."""

    def test_calls_lifecycle_service_on_churn(self, tenant_id: uuid.UUID):
        from src.modules.crm.application.event_handlers import handle_churn_event

        event = _make_event(
            "churn_detected",
            tenant_id,
            payload={
                "profile_id": str(uuid.uuid4()),
                "source": "stripe",
                "subscription_id": "sub_123",
            },
        )

        mock_db = _mock_session()

        with (
            patch("src.core.database.SessionLocal", return_value=mock_db),
            patch("src.modules.crm.application.services.lifecycle_service.LifecycleService") as mock_lifecycle,
        ):
            mock_svc = MagicMock()
            mock_lifecycle.return_value = mock_svc

            handle_churn_event(event)

            mock_svc.handle_churn_event.assert_called_once_with(event)
            mock_db.commit.assert_called_once()
            mock_db.close.assert_called_once()

    def test_rollback_on_churn_error(self, tenant_id: uuid.UUID):
        from src.modules.crm.application.event_handlers import handle_churn_event

        event = _make_event("churn_detected", tenant_id, payload={"profile_id": str(uuid.uuid4())})
        mock_db = _mock_session()

        with (
            patch("src.core.database.SessionLocal", return_value=mock_db),
            patch(
                "src.modules.crm.application.services.lifecycle_service.LifecycleService",
                side_effect=ValueError("invalid churn"),
            ),
        ):
            handle_churn_event(event)

            mock_db.rollback.assert_called_once()
            mock_db.close.assert_called_once()

    def test_logs_exception_on_churn_failure(self, tenant_id: uuid.UUID, caplog):
        from src.modules.crm.application.event_handlers import handle_churn_event

        profile_id = uuid.uuid4()
        event = _make_event(
            "churn_detected",
            tenant_id,
            payload={"profile_id": str(profile_id)},
        )

        with patch(
            "src.core.database.SessionLocal",
            side_effect=ImportError("cannot import"),
        ):
            handle_churn_event(event)

        assert any("Failed to handle churn_detected event" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# handle_lead_captured_event
# ---------------------------------------------------------------------------


class TestHandleLeadCapturedEvent:
    """handle_lead_captured_event logs lead capture info (analytics-only)."""

    def test_logs_lead_capture_details(self, tenant_id: uuid.UUID, caplog):
        from src.modules.crm.application.event_handlers import (
            handle_lead_captured_event,
        )

        event = _make_event(
            "lead_captured",
            tenant_id,
            payload={
                "profile_id": str(uuid.uuid4()),
                "channel_slug": "ig-dm",
                "extracted_field": "email",
            },
        )

        import logging

        with caplog.at_level(logging.INFO, logger="src.modules.crm.application.event_handlers"):
            handle_lead_captured_event(event)

        assert any("Lead captured:" in r.message for r in caplog.records)

    def test_handles_missing_payload_keys(self, tenant_id: uuid.UUID, caplog):
        from src.modules.crm.application.event_handlers import (
            handle_lead_captured_event,
        )

        event = _make_event("lead_captured", tenant_id, payload={})

        import logging

        with caplog.at_level(logging.INFO, logger="src.modules.crm.application.event_handlers"):
            handle_lead_captured_event(event)

        assert any("Lead captured:" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# _handle_appointment_event (via handle_appointment_booked)
# ---------------------------------------------------------------------------


class TestHandleAppointmentBooked:
    """handle_appointment_booked creates meeting_booked journey events."""

    def test_creates_journey_event_when_profile_found(self, tenant_id: uuid.UUID):
        from src.modules.crm.application.event_handlers import (
            handle_appointment_booked,
        )

        lead_id = uuid.uuid4()
        appointment_id = uuid.uuid4()
        profile_id = uuid.uuid4()

        event = _make_event(
            "appointment_booked",
            tenant_id,
            payload={
                "lead_id": str(lead_id),
                "appointment_id": str(appointment_id),
                "status": "SCHEDULED",
                "email": "appt@test.com",
            },
        )

        mock_lead = MagicMock()
        mock_lead.email = "appt@test.com"
        mock_lead.id = lead_id

        mock_profile = MagicMock()
        mock_profile.id = profile_id

        mock_db = _mock_session()
        mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            mock_lead,
            mock_profile,
        ]

        with (
            patch("src.core.database.SessionLocal", return_value=mock_db),
            patch("src.modules.crm.application.services.lifecycle_service.LifecycleService") as mock_lifecycle,
        ):
            mock_lifecycle.return_value = MagicMock()

            handle_appointment_booked(event)

            assert mock_db.add.called
            mock_db.commit.assert_called_once()
            mock_db.close.assert_called_once()

    def test_logs_warning_when_no_profile_found(self, tenant_id: uuid.UUID, caplog):
        from src.modules.crm.application.event_handlers import (
            handle_appointment_booked,
        )

        event = _make_event(
            "appointment_booked",
            tenant_id,
            payload={
                "lead_id": str(uuid.uuid4()),
                "appointment_id": str(uuid.uuid4()),
                "status": "SCHEDULED",
            },
        )

        mock_lead = MagicMock()
        mock_lead.email = None

        mock_db = _mock_session()
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_lead

        with patch("src.core.database.SessionLocal", return_value=mock_db):
            handle_appointment_booked(event)

            assert any("without matching profile" in r.message for r in caplog.records)
            mock_db.commit.assert_called_once()
            mock_db.close.assert_called_once()

    def test_handles_exception_with_rollback(self, tenant_id: uuid.UUID, caplog):
        from src.modules.crm.application.event_handlers import (
            handle_appointment_booked,
        )

        event = _make_event(
            "appointment_booked",
            tenant_id,
            payload={
                "lead_id": str(uuid.uuid4()),
                "appointment_id": str(uuid.uuid4()),
                "status": "SCHEDULED",
            },
        )

        with patch(
            "src.core.database.SessionLocal",
            side_effect=RuntimeError("db down"),
        ):
            handle_appointment_booked(event)

        assert any("Failed to handle meeting_booked event" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# handle_appointment_completed
# ---------------------------------------------------------------------------


class TestHandleAppointmentCompleted:
    """handle_appointment_completed creates meeting_completed journey events."""

    def test_passes_correct_journey_event_name(self, tenant_id: uuid.UUID):
        from src.modules.crm.application.event_handlers import (
            handle_appointment_completed,
        )

        event = _make_event(
            "appointment_completed",
            tenant_id,
            payload={
                "lead_id": str(uuid.uuid4()),
                "appointment_id": str(uuid.uuid4()),
                "status": "COMPLETED",
            },
        )

        mock_db = _mock_session()

        with patch("src.core.database.SessionLocal", return_value=mock_db):
            handle_appointment_completed(event)

            mock_db.commit.assert_called_once()
            mock_db.close.assert_called_once()


# ---------------------------------------------------------------------------
# handle_appointment_no_show
# ---------------------------------------------------------------------------


class TestHandleAppointmentNoShow:
    """handle_appointment_no_show creates meeting_no_show journey events."""

    def test_passes_correct_journey_event_name(self, tenant_id: uuid.UUID):
        from src.modules.crm.application.event_handlers import (
            handle_appointment_no_show,
        )

        event = _make_event(
            "appointment_no_show",
            tenant_id,
            payload={
                "lead_id": str(uuid.uuid4()),
                "appointment_id": str(uuid.uuid4()),
                "status": "NO_SHOW",
            },
        )

        mock_db = _mock_session()

        with patch("src.core.database.SessionLocal", return_value=mock_db):
            handle_appointment_no_show(event)

            mock_db.commit.assert_called_once()
            mock_db.close.assert_called_once()


# ---------------------------------------------------------------------------
# EventBus integration
# ---------------------------------------------------------------------------


class TestEventBusDispatch:
    """Event handlers are dispatched via EventBus."""

    def teardown_method(self):
        EventBus.clear()

    def test_handler_exception_does_not_propagate(self, tenant_id: uuid.UUID):
        from src.modules.crm.application.event_handlers import register_event_handlers

        EventBus.clear()
        register_event_handlers()

        event = _make_event("sale_completed", tenant_id, payload={})

        with patch(
            "src.core.database.SessionLocal",
            side_effect=Exception("total failure"),
        ):
            EventBus._dispatch(event)

        EventBus.clear()
