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

    link = BookingLink(
        tenant_id=tenant_id,
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
