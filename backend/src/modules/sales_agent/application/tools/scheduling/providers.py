"""SchedulerProvider strategy pattern (S8).

Outbound Strategy: how the sales agent generates booking links, verifies
booking status, and lists available slots — abstracted across multiple
scheduler back-ends.

Today only ``InternalSchedulerProvider`` is wired (uses Nicolify's own
``BookingLink`` + ``AvailabilityService``). Cal.com / Calendly / Google
Calendar push will register concrete impls via ``SCHEDULER_PROVIDERS``
without touching tool code.

DRY contract:

* All providers expose the **same Protocol surface** (`SchedulerProvider`).
* Resolution is registry-based (``scheduler_provider_for_tenant``) — tools
  must never branch on ``provider_id``. New providers add an entry, not
  a conditional.
* Output types (``BookingLinkOutput``, ``BookingStatus``, ``SchedulerSlot``)
  are frozen dataclasses → tools serialize them mechanically into the
  ``dict`` shape the LLM consumes.

Coupling discipline:

* Concrete impls may import from `scheduling`, `connections`, `iam` (read
  models). Tools must import only the Protocol + dataclasses + resolver.
* No I/O in dataclasses. ``InternalSchedulerProvider`` owns DB session,
  not the Protocol.
"""

# [SALES-AGENT-S8-PROVIDER]  # noqa: ERA001

from __future__ import annotations

import datetime as dt
import secrets
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol, runtime_checkable
from uuid import UUID

import structlog
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = structlog.get_logger()


# ──────────────────────────────────────────────────────────────
# Output types — frozen, transport-friendly
# ──────────────────────────────────────────────────────────────


class BookingStatusValue(StrEnum):
    """High-level booking status surfaced to tools / UI / events.

    Maps from underlying scheduler-specific states. Internal mapping:

    * ``pending``    → BookingLink ACTIVE, no Appointment yet.
    * ``confirmed``  → Appointment SCHEDULED.
    * ``completed``  → Appointment COMPLETED.
    * ``no_show``    → Appointment NO_SHOW (admin set or webhook).
    * ``missed``     → cron-inferred (start_time + grace passed, still SCHEDULED).
    * ``cancelled``  → Appointment CANCELLED OR BookingLink consumed but
                       reservation cancelled by lead/host.
    * ``expired``    → BookingLink past expires_at without USED transition.
    * ``unknown``    → tracking_id not found locally.
    """

    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    MISSED = "missed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class BookingLinkOutput:
    """Single-use booking URL + tracking metadata."""

    tracking_id: str
    url: str
    event_slug: str
    expires_at: dt.datetime
    provider_id: str = "internal"

    def as_tool_response(self) -> dict[str, str]:
        """Serialize for LLM-readable tool result."""
        return {
            "url": self.url,
            "tracking_id": self.tracking_id,
            "event_slug": self.event_slug,
            "expires_at": self.expires_at.isoformat(),
            "provider": self.provider_id,
        }


@dataclass(frozen=True, slots=True)
class BookingStatus:
    """Status of a booking by tracking_id."""

    tracking_id: str
    status: BookingStatusValue
    scheduled_at: dt.datetime | None = None
    appointment_id: UUID | None = None
    provider_id: str = "internal"
    extra: dict[str, str] = field(default_factory=dict)

    def as_tool_response(self) -> dict[str, str | None]:
        """Serialize for LLM-readable tool result."""
        return {
            "tracking_id": self.tracking_id,
            "status": self.status.value,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "appointment_id": str(self.appointment_id) if self.appointment_id else None,
            "provider": self.provider_id,
            **self.extra,
        }


@dataclass(frozen=True, slots=True)
class SchedulerSlot:
    """Available slot offering."""

    start_time: dt.datetime
    duration_minutes: int

    def as_tool_response(self) -> dict[str, str | int]:
        """Serialize for LLM-readable tool result."""
        return {
            "start_time": self.start_time.isoformat(),
            "duration_minutes": self.duration_minutes,
        }


# ──────────────────────────────────────────────────────────────
# Strategy Protocol
# ──────────────────────────────────────────────────────────────


@runtime_checkable
class SchedulerProvider(Protocol):
    """Outbound scheduler operations contract.

    All concrete impls MUST be ``runtime_checkable`` compliant — arch test
    ``test_scheduler_provider_strategy.py`` enforces.
    """

    provider_id: str

    def create_booking_link(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        event_slug: str,
        expires_in_hours: int = 72,
    ) -> BookingLinkOutput:
        """Issue a single-use, lead-scoped booking URL."""
        ...

    def verify_booking_status(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        tracking_id: str,
    ) -> BookingStatus:
        """Resolve current high-level status of a tracking_id."""
        ...

    def get_available_slots(
        self,
        *,
        tenant_id: UUID,
        event_slug: str,
        days_ahead: int = 14,
    ) -> list[SchedulerSlot]:
        """Return upcoming slots for ``event_slug``."""
        ...


# ──────────────────────────────────────────────────────────────
# Internal impl — uses Nicolify's own scheduling module
# ──────────────────────────────────────────────────────────────


class InternalSchedulerProvider:
    """Default impl backed by ``BookingLink`` + ``AvailabilityService``.

    Each call delegates to ``shared/links/ports/scheduling.py`` helpers so
    sales_agent never imports ``scheduling`` directly (tenant isolation +
    DDD boundary).
    """

    provider_id: str = "internal"

    def __init__(self, db: Session) -> None:
        """Initialize InternalSchedulerProvider."""
        self.db = db

    # ── outbound ─────────────────────────────────────────────

    def create_booking_link(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        event_slug: str,
        expires_in_hours: int = 72,
    ) -> BookingLinkOutput:
        """Persist a BookingLink + return URL composed against tenant domain."""
        from src.shared.links.ports.scheduling import (
            create_personalized_booking_link,
            get_booking_base_url,
        )

        token = secrets.token_urlsafe(16)
        expires_at = dt.datetime.now(dt.UTC) + dt.timedelta(hours=expires_in_hours)

        create_personalized_booking_link(
            self.db,
            tenant_id=tenant_id,
            lead_id=str(lead_id),
            event_slug=event_slug,
            token=token,
            expires_at=expires_at,
        )

        from src.shared.links.ports.domain_lookup import create_domain_lookup

        base_url = get_booking_base_url(tenant_id, create_domain_lookup(self.db))
        tenant_slug = self._resolve_tenant_slug(tenant_id)
        url = f"{base_url}/book/{tenant_slug}/{event_slug}?token={token}"

        logger.info(
            "internal_scheduler_link_created",
            tenant_id=str(tenant_id),
            lead_id=str(lead_id),
            event_slug=event_slug,
        )

        return BookingLinkOutput(
            tracking_id=token,
            url=url,
            event_slug=event_slug,
            expires_at=expires_at,
            provider_id=self.provider_id,
        )

    def verify_booking_status(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        tracking_id: str,
    ) -> BookingStatus:
        """Resolve status by joining BookingLink + Appointment."""
        link_state = self._lookup_link(tracking_id)
        if link_state is None:
            return BookingStatus(
                tracking_id=tracking_id,
                status=BookingStatusValue.UNKNOWN,
                provider_id=self.provider_id,
            )

        link_status, link_event_slug, link_expires_at, link_lead_id = link_state

        # Tenant + lead boundary check (defense in depth — repo also filters).
        if link_lead_id is not None and str(link_lead_id) != str(lead_id):
            return BookingStatus(
                tracking_id=tracking_id,
                status=BookingStatusValue.UNKNOWN,
                provider_id=self.provider_id,
                extra={"reason": "lead_mismatch"},
            )

        appt = self._lookup_appointment(tenant_id, lead_id, link_event_slug)
        status = self._derive_status(
            link_status=link_status,
            link_expires_at=link_expires_at,
            appointment_status=appt[0] if appt else None,
            appointment_start=appt[1] if appt else None,
        )

        return BookingStatus(
            tracking_id=tracking_id,
            status=status,
            scheduled_at=appt[1] if appt else None,
            appointment_id=appt[2] if appt else None,
            provider_id=self.provider_id,
        )

    def get_available_slots(
        self,
        *,
        tenant_id: UUID,
        event_slug: str,
        days_ahead: int = 14,
    ) -> list[SchedulerSlot]:
        """Pull slots from AvailabilityService via shared port."""
        from src.shared.links.ports.scheduling import list_event_type_slots

        rows = list_event_type_slots(
            self.db,
            tenant_id=tenant_id,
            event_slug=event_slug,
            days_ahead=days_ahead,
        )
        return [SchedulerSlot(start_time=start_time, duration_minutes=duration) for (start_time, duration) in rows]

    # ── helpers ──────────────────────────────────────────────

    def _resolve_tenant_slug(self, tenant_id: UUID) -> str:
        from src.modules.iam.infrastructure.models.tenant_model import TenantModel

        stmt = select(TenantModel.slug).where(TenantModel.id == tenant_id)
        slug = self.db.execute(stmt).scalar_one_or_none()
        return slug or "tenant"

    def _lookup_link(
        self,
        tracking_id: str,
    ) -> tuple[str, str | None, dt.datetime, UUID | None] | None:
        """Return (status, event_slug, expires_at, lead_id) for a token, or None."""
        from src.shared.links.ports.scheduling import lookup_booking_link_by_token

        return lookup_booking_link_by_token(self.db, tracking_id)

    def _lookup_appointment(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        event_slug: str | None,
    ) -> tuple[str, dt.datetime, UUID] | None:
        """Most recent appointment for this lead.

        Returns ``(status, start_time, id)`` via shared port — never
        imports scheduling models directly. ``event_slug`` reserved for
        future per-slug filtering when AppointmentModel grows the FK.
        """
        from src.shared.links.ports.scheduling import (
            lookup_latest_appointment_for_lead,
        )

        _ = event_slug  # reserved for future per-slug filtering
        return lookup_latest_appointment_for_lead(
            self.db,
            tenant_id=tenant_id,
            lead_id=lead_id,
        )

    @staticmethod
    def _derive_status(
        *,
        link_status: str,
        link_expires_at: dt.datetime,
        appointment_status: str | None,
        appointment_start: dt.datetime | None,
    ) -> BookingStatusValue:
        """Combine link + appointment state into the high-level enum.

        Appointment trumps link (the booking happened). If no appointment,
        we fall back to link status, including expiration math.
        """
        now = dt.datetime.now(dt.UTC)

        if appointment_status:
            mapping = {
                "SCHEDULED": BookingStatusValue.CONFIRMED,
                "COMPLETED": BookingStatusValue.COMPLETED,
                "NO_SHOW": BookingStatusValue.NO_SHOW,
                "CANCELLED": BookingStatusValue.CANCELLED,
            }
            mapped = mapping.get(appointment_status.upper())
            if mapped == BookingStatusValue.CONFIRMED and appointment_start is not None:
                # Auto-promote to MISSED if start passed by ≥30min and still SCHEDULED.
                aware_start = (
                    appointment_start if appointment_start.tzinfo else appointment_start.replace(tzinfo=dt.UTC)
                )
                grace = aware_start + dt.timedelta(minutes=30)
                if now > grace:
                    return BookingStatusValue.MISSED
            if mapped is not None:
                return mapped

        # No appointment yet — examine link.
        normalized = (link_status or "").upper()
        if normalized == "USED":
            # Used means lead consumed the link but appointment not persisted yet —
            # transient race. Surface as PENDING; cron + webhook reconcile.
            return BookingStatusValue.PENDING
        if normalized == "EXPIRED":
            return BookingStatusValue.EXPIRED

        # ACTIVE branch — check expiration vs wall clock.
        expires_aware = link_expires_at if link_expires_at.tzinfo else link_expires_at.replace(tzinfo=dt.UTC)
        if expires_aware < now:
            return BookingStatusValue.EXPIRED
        return BookingStatusValue.PENDING


# ──────────────────────────────────────────────────────────────
# Registry + resolver
# ──────────────────────────────────────────────────────────────


SCHEDULER_PROVIDERS: dict[str, type[SchedulerProvider]] = {
    "internal": InternalSchedulerProvider,
}


def register_scheduler_provider(provider: type[SchedulerProvider]) -> None:
    """Register a concrete SchedulerProvider impl by its ``provider_id``.

    Used by future Cal.com / Calendly / GCal-push impls. Idempotent
    (overwrite same key is allowed for test wiring).
    """
    SCHEDULER_PROVIDERS[provider.provider_id] = provider


def scheduler_provider_for_tenant(db: Session, tenant_id: UUID) -> SchedulerProvider:
    """Return the SchedulerProvider configured for ``tenant_id``.

    Resolution today: every tenant uses ``InternalSchedulerProvider``.
    When tenant config grows a ``scheduler_provider`` column (or
    ``connections`` exposes a per-tenant scheduler choice), branch here
    via lookup — never inside tools.
    """
    _ = tenant_id  # reserved for future per-tenant routing
    klass = SCHEDULER_PROVIDERS["internal"]
    return klass(db=db)
