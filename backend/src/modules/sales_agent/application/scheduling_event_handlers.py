"""Sales-agent subscribers to scheduling-related shared events (S8).

Bridges the shared ``AppointmentEvent`` (emitted by ``scheduling`` admin
agenda + future external webhook providers) into the local
``scheduled_meetings`` JSONB so the reminder engine + Closer Studio UI
see live status without reading the appointments table directly.

Coupling discipline:

* Reads/writes only via ``MeetingStateService`` — no direct SQL on the
  JSONB column.
* Each handler opens a short-lived ``SessionLocal()`` (best-effort) so
  failures NEVER propagate back to ``scheduling.api.agenda``.
* Idempotent: re-receiving the same event mutates the entry to the same
  terminal state (no spurious StageTransition or duplicate notification).
"""

# [SALES-AGENT-S8-WEBHOOK]  # noqa: ERA001

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

import structlog
from luana_core_events.outbox.application.event_bus_adapter import (
    adapter_bus as EventBus,  # noqa: N812
)
from luana_core_platform.domain.events import (
    AppointmentEvent,
    BookingMissedEvent,
    DomainEvent,
)
from luana_core_sales_agent.application.services.meeting_state_service import (
    MeetingEntryStatus,
    MeetingStateService,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = structlog.get_logger()


_STATUS_TO_ENTRY = {
    "SCHEDULED": MeetingEntryStatus.CONFIRMED,
    "COMPLETED": MeetingEntryStatus.COMPLETED,
    "NO_SHOW": MeetingEntryStatus.NO_SHOW,
    "CANCELLED": MeetingEntryStatus.CANCELLED,
}


def handle_appointment_event(event: DomainEvent) -> None:
    """Reflect an AppointmentEvent into ``scheduled_meetings``.

    We do NOT receive the tracking_id from the event payload (the
    appointment record doesn't carry it back through admin/agenda).
    Strategy: match the most recent non-terminal entry for the lead and
    transition it. If no entry exists (booking happened outside the
    sales_agent flow), this is a no-op.
    """
    if not isinstance(event, AppointmentEvent):
        return

    payload = event.payload or {}
    raw_lead = payload.get("lead_id")
    raw_appt = payload.get("appointment_id")
    status = payload.get("status")
    if not raw_lead or not raw_appt or not status:
        return

    new_status = _STATUS_TO_ENTRY.get(status.upper())
    if new_status is None:
        return

    try:
        lead_id = UUID(str(raw_lead))
        appointment_id = UUID(str(raw_appt))
    except ValueError:
        logger.warning("appointment_event_invalid_uuids", payload=payload)
        return

    db = _open_session()
    if db is None:
        return
    try:
        service = MeetingStateService(db)
        entries = service.list_for_lead(event.tenant_id, lead_id)
        target = _pick_entry_to_update(entries)
        if target is None:
            return
        service.update_status_by_tracking(
            event.tenant_id,
            lead_id,
            tracking_id=target.tracking_id,
            status=new_status,
            appointment_id=appointment_id,
        )
        db.commit()
    except Exception as exc:  # noqa: BLE001 — best-effort
        logger.warning("appointment_event_persist_failed", error=str(exc))
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            logger.warning("appointment_event_rollback_failed")
    finally:
        try:
            db.close()
        except Exception:  # noqa: BLE001
            logger.warning("appointment_event_close_failed")


def handle_booking_missed(event: DomainEvent) -> None:
    """Idempotent — sets entry to MISSED. Reminder engine fires postcheck."""
    if not isinstance(event, BookingMissedEvent):
        return
    payload = event.payload or {}
    raw_lead = payload.get("lead_id")
    if not raw_lead:
        return
    try:
        lead_id = UUID(str(raw_lead))
    except ValueError:
        return

    db = _open_session()
    if db is None:
        return
    try:
        service = MeetingStateService(db)
        entries = service.list_for_lead(event.tenant_id, lead_id)
        target = _pick_entry_to_update(entries)
        if target is None:
            return
        service.update_status_by_tracking(
            event.tenant_id,
            lead_id,
            tracking_id=target.tracking_id,
            status=MeetingEntryStatus.MISSED,
        )
        db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("booking_missed_persist_failed", error=str(exc))
        try:
            db.rollback()
        except Exception:  # noqa: BLE001
            logger.warning("booking_missed_rollback_failed")
    finally:
        try:
            db.close()
        except Exception:  # noqa: BLE001
            logger.warning("booking_missed_close_failed")


def _pick_entry_to_update(
    entries: list,
) -> object:
    """Return the most recent non-terminal entry, else None."""
    terminal = {
        MeetingEntryStatus.COMPLETED,
        MeetingEntryStatus.NO_SHOW,
        MeetingEntryStatus.CANCELLED,
        MeetingEntryStatus.EXPIRED,
        MeetingEntryStatus.MISSED,
    }
    candidates = [e for e in entries if e.status not in terminal]
    return max(candidates, key=lambda e: e.created_at) if candidates else None


def _open_session() -> Session | None:
    """Open a fresh sales_agent session for handler-local writes."""
    try:
        from luana_core_sales_agent.infrastructure.db.database import SessionLocal

        return SessionLocal()
    except Exception as exc:  # noqa: BLE001
        logger.warning("appointment_event_session_failed", error=str(exc))
        return None


def register_scheduling_event_handlers() -> None:
    """Subscribe handlers. Idempotent: safe to call multiple times."""
    EventBus.subscribe("appointment_booked", handle_appointment_event)
    EventBus.subscribe("appointment_completed", handle_appointment_event)
    EventBus.subscribe("appointment_no_show", handle_appointment_event)
    EventBus.subscribe("appointment_cancelled", handle_appointment_event)
    EventBus.subscribe("booking_missed", handle_booking_missed)
    logger.info(
        "Sales-agent scheduling handlers registered: appointment_{booked,completed,no_show,cancelled} + booking_missed",
    )
