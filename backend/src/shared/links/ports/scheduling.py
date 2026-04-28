"""SchedulingPort — cross-module port for scheduling availability checks.

``sales_agent`` uses this to verify calendar connectivity without importing
from ``scheduling`` directly.

Canonical implementation: ``scheduling.application.services.availability_service``
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

# ── Port ABC ──────────────────────────────────────────────────


class SchedulingPort(ABC):
    """Port for scheduling operations across module boundaries."""

    @abstractmethod
    def is_calendar_connected(self) -> bool:
        """Check if the tenant has an active Google Calendar connection."""
        ...


# ── Factory ───────────────────────────────────────────────────


def create_scheduling_port(db: Session, tenant_id: UUID) -> SchedulingPort | None:
    """Create a SchedulingPort instance.

    Lazy-imports the concrete AvailabilityService from scheduling.
    Returns None if the import fails (scheduling module not loaded).
    """
    try:
        from src.modules.scheduling.application.services.availability_service import (
            AvailabilityService,
        )

        return AvailabilityService(db=db, tenant_id=tenant_id)
    except ImportError:
        return None


def get_availability_service(db: Session, tenant_id: UUID) -> object:
    """Create an AvailabilityService instance. Lazy-imports from scheduling."""
    from src.modules.scheduling.application.services.availability_service import (
        AvailabilityService,
    )

    return AvailabilityService(db=db, tenant_id=tenant_id)


def get_booking_base_url(tenant_id: UUID, domain_lookup: object) -> str:
    """Return booking base URL for a tenant. Lazy-imports from scheduling."""
    from src.modules.scheduling.application.booking_url import (
        get_booking_base_url as _impl,
    )

    return _impl(tenant_id, domain_lookup)  # type: ignore[arg-type]


def create_personalized_booking_link(
    db: Session,
    *,
    tenant_id: UUID,
    lead_id: str,
    event_slug: str,
    token: str,
    expires_at: object,
    status: str = "ACTIVE",
) -> dict:
    """Create and persist a BookingLink record. Returns {token, expires_at}.

    Lazy-imports BookingLink from scheduling.
    """
    from src.modules.scheduling.infrastructure.models.booking_link import BookingLink

    _ = tenant_id  # BookingLink table has no tenant_id column; reserved for parity
    link = BookingLink(
        lead_id=lead_id,
        event_slug=event_slug,
        token=token,
        expires_at=expires_at,
        status=status,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return {"token": link.token, "expires_at": link.expires_at}


def lookup_booking_link_by_token(db: Session, token: str) -> object | None:
    """Return ``(status, event_slug, expires_at, lead_id)`` for a token.

    Returns ``None`` when the token is unknown. Sales-agent's
    ``InternalSchedulerProvider`` uses this so it never imports scheduling
    models directly.
    """
    from sqlalchemy import select

    from src.modules.scheduling.infrastructure.models.booking_link import BookingLink

    stmt = select(
        BookingLink.status,
        BookingLink.event_slug,
        BookingLink.expires_at,
        BookingLink.lead_id,
    ).where(BookingLink.token == token)
    row = db.execute(stmt).first()
    return tuple(row) if row else None


def lookup_latest_appointment_for_lead(
    db: Session,
    *,
    tenant_id: UUID,
    lead_id: UUID,
) -> object | None:
    """Return ``(status, start_time, id)`` for the most recent Appointment.

    Returns ``None`` when the lead has no appointment. Used by S8
    ``verify_booking_status`` to derive high-level status without crossing
    DDD boundaries.
    """
    from sqlalchemy import select

    from src.modules.scheduling.infrastructure.models.appointment_model import (
        AppointmentModel,
    )

    stmt = (
        select(
            AppointmentModel.status,
            AppointmentModel.start_time,
            AppointmentModel.id,
        )
        .where(
            AppointmentModel.tenant_id == tenant_id,
            AppointmentModel.lead_id == lead_id,
        )
        .order_by(AppointmentModel.start_time.desc())
        .limit(1)
    )
    row = db.execute(stmt).first()
    return tuple(row) if row else None


def list_event_type_slots(
    db: Session,
    *,
    tenant_id: UUID,
    event_slug: str,
    days_ahead: int = 14,
) -> list[object]:
    """Return upcoming slot start datetimes for an event type slug.

    Empty list when calendar is not connected or the event type doesn't
    exist. Sales-agent's S8 tool ``get_available_slots`` uses this so it
    never imports scheduling services directly.
    """
    import datetime as dt

    from src.modules.scheduling.application.services.availability_service import (
        AvailabilityService,
    )
    from src.modules.scheduling.application.services.event_type_service import (
        EventTypeService,
    )

    et_service = EventTypeService(db, tenant_id)
    event_type = et_service.get_by_slug(event_slug)
    if event_type is None:
        return []

    av_service = AvailabilityService(db, tenant_id)
    if not av_service.is_connected():
        return []

    today = dt.date.today()  # noqa: DTZ011
    starts = av_service.get_event_type_slots(
        event_type,
        today,
        today + dt.timedelta(days=days_ahead),
    )
    return [(s, event_type.duration) for s in starts]
