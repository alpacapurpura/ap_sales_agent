"""Shared EventBus for cross-module domain event dispatch.

Usage:
    # Subscribe at app startup
    EventBus.subscribe("sale_completed", handle_sale_completed)

    # Publish with deferred dispatch (after DB commit)
    EventBus.publish(event, session=db)

    # Publish with immediate dispatch (no DB context)
    EventBus.publish(event, session=None)
"""

import logging
import sys
import warnings
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog

logger = logging.getLogger(__name__)
_structlog_logger = structlog.get_logger(__name__)


def _is_internal_caller_or_test() -> bool:
    """Return True if caller is inside shared/domain_events/* OR tests/*.

    Used to suppress the deprecation warning during:
    - EventBusAdapter fall-through (adapter calls EventBus.publish when flag=False)
    - Test capability suites (tests/shared/test_event_bus.py, tests/shared/domain_events/*)

    Best-effort: on any error, suppress warning (don't break caller).

    PI-11 PR-1 § 5 D3 (2026-05-04).
    """
    try:
        frame = sys._getframe(2)  # Skip publish() + this helper frame
        depth = 0
        while frame is not None and depth < 10:
            filename = frame.f_code.co_filename
            if (
                "shared/domain_events/" in filename
                or "shared\\domain_events\\" in filename
                or "shared/domain/events.py" in filename
                or "shared\\domain\\events.py" in filename
                or "/tests/" in filename
                or "\\tests\\" in filename
            ):
                return True
            frame = frame.f_back  # type: ignore[assignment]
            depth += 1
    except Exception:  # noqa: BLE001 — best-effort
        return True  # Suppress on error
    return False


@dataclass
class DomainEvent:
    """Base domain event. All cross-module events extend this."""

    event_name: str
    tenant_id: UUID
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any] = field(default_factory=dict)


class EventBus:
    """Simple in-process event bus with after-commit dispatch.

    Singleton pattern: _handlers is class-level, shared across the process.
    Handler exceptions are caught and logged, never propagated to the publisher.
    """

    _handlers: dict[str, list[Callable]] = {}

    @classmethod
    def subscribe(cls, event_name: str, handler: Callable) -> None:
        """Register a handler for a given event name."""
        cls._handlers.setdefault(event_name, []).append(handler)

    @classmethod
    def publish(cls, event: DomainEvent, session: Any | None = None) -> None:  # noqa: ANN401 — SQLAlchemy event listener signature
        """Publish an event.

        If session is provided, dispatch is deferred until after session.commit().
        If session is None, dispatch is immediate.

        DEPRECATED PATH: Since outbox cutover (PR-6 PI-2), production emitters
        route via EventBusAdapter. Direct calls to EventBus.publish outside
        EventBusAdapter fall-through path + test capability suites emit a runtime
        warning when ANY USE_OUTBOX_PATTERN_* flag is True.

        Migration: use EventBusAdapter.publish(event, session=session) or route
        via adapter_bus alias. See CONTRACT.md PR-1 § 5 D3 (PI-11, 2026-05-04).
        Elimination planned post PI-12 capability removal evaluation.
        """
        # Best-effort deprecation warning (try/except: must not break caller).
        # Emits only when outbox flag is ON and caller is outside internal paths.
        try:
            from luana_core_platform.core.config import settings as _settings  # local import avoids circular

            outbox_flags_on = (
                getattr(_settings, "USE_OUTBOX_PATTERN_SALES_AGENT", False)
                or getattr(_settings, "USE_OUTBOX_PATTERN_COPILOT", False)
                or getattr(_settings, "USE_OUTBOX_PATTERN_BRAND", False)
            )
            if outbox_flags_on and not _is_internal_caller_or_test():
                warnings.warn(
                    "EventBus.publish called when outbox cutover active. "
                    "Migrate emitter to EventBusAdapter or wrap with "
                    "magic comment '# arch-bypass: testing legacy capability'.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                _structlog_logger.warning(
                    "legacy_event_bus_called_outside_test_context",
                    event_name=event.event_name,
                    tenant_id=str(event.tenant_id),
                )
        except Exception:  # noqa: BLE001 — best-effort, must not break caller
            pass

        if session is not None:
            from sqlalchemy import event as sa_event

            @sa_event.listens_for(session, "after_commit", once=True)
            def _on_commit(sess: Any) -> None:  # noqa: ANN401 — SQLAlchemy event listener signature
                cls._dispatch(event)
        else:
            cls._dispatch(event)

    @classmethod
    def _dispatch(cls, event: DomainEvent) -> None:
        """Dispatch event to all registered handlers. Exceptions are isolated."""
        for handler in cls._handlers.get(event.event_name, []):
            try:
                handler(event)
            except Exception:
                logger.exception(
                    "Event handler %s failed for event %s",
                    getattr(handler, "__name__", handler),
                    event.event_name,
                )

    @classmethod
    def clear(cls) -> None:
        """Remove all registered handlers. Used for test isolation."""
        cls._handlers.clear()


# ──────────────────────────────────────────────────────────────
# Typed domain events — shared across modules
# ──────────────────────────────────────────────────────────────

# Mapping from connections module channel_type to capture channel slugs
# (used by ChatOrchestrator when setting lead_source on new profiles)
CHANNEL_TYPE_TO_CAPTURE_SLUG: dict[str, str] = {
    "instagram": "ig-dm",
    "facebook": "fb-messenger",
    "tiktok": "tiktok-dm",
    "whatsapp": "whatsapp-inbound",
    "telegram": "telegram-dm",
}


@dataclass
class SaleCompletedEvent(DomainEvent):
    """Emitted by SaleService when a sale is completed (CONVERSION or EXPANSION).

    Payload keys:
        sale_id: UUID of the sale record
        customer_id: UUID of the customer profile
        stage: "CONVERSION" or "EXPANSION"
        amount: sale amount (float)
        offer_id: UUID of the related offer
    """

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        sale_id: UUID,
        customer_id: UUID,
        stage: str,
        amount: float,
        offer_id: UUID,
    ) -> "SaleCompletedEvent":
        """Create a sale_completed event from sale details."""
        return cls(
            event_name="sale_completed",
            tenant_id=tenant_id,
            payload={
                "sale_id": str(sale_id),
                "customer_id": str(customer_id),
                "stage": stage,
                "amount": amount,
                "offer_id": str(offer_id),
            },
        )


@dataclass
class ChurnEvent(DomainEvent):
    """Emitted when a subscription cancellation is detected (Shopify/Stripe webhooks).

    Payload keys:
        profile_id: UUID of the customer profile
        source: origin platform ("shopify" or "stripe")
        subscription_id: external subscription identifier
        cancellation_reason: optional reason for cancellation
    """

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        profile_id: UUID,
        source: str,
        subscription_id: str,
        cancellation_reason: str | None = None,
    ) -> "ChurnEvent":
        """Create a churn_detected event from churn details."""
        return cls(
            event_name="churn_detected",
            tenant_id=tenant_id,
            payload={
                "profile_id": str(profile_id),
                "source": source,
                "subscription_id": subscription_id,
                "cancellation_reason": cancellation_reason or "",
            },
        )


@dataclass
class LeadCapturedEvent(DomainEvent):
    """Emitted by Sales Agent when AI extracts email/phone from conversation.

    Payload keys:
        profile_id: UUID of the created customer profile
        channel_slug: capture channel slug (ig-dm, fb-messenger, etc.)
        extracted_field: "email" or "phone"
        source_channel_type: original channel_type from connections module
    """

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        profile_id: UUID,
        channel_slug: str,
        extracted_field: str,
        source_channel_type: str,
    ) -> "LeadCapturedEvent":
        """Create a lead_captured event from capture details."""
        return cls(
            event_name="lead_captured",
            tenant_id=tenant_id,
            payload={
                "profile_id": str(profile_id),
                "channel_slug": channel_slug,
                "extracted_field": extracted_field,
                "source_channel_type": source_channel_type,
            },
        )


@dataclass
class ExtractionSectionCompletedEvent(DomainEvent):
    """Emitted per section transition running→completed by extraction workers.

    Consumed by copilot to insert a navigation pill into the conversation.

    Payload keys:
        job_id: str (ARQ job id, used as idempotency key)
        conversation_id: str | None
        module: "brand" | "offer"
        section_slug: str
        section_label: str   (Spanish label resolved by the publisher)
        fields_count: int
    """

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        job_id: str,
        conversation_id: str | None,
        module: str,
        section_slug: str,
        section_label: str,
        fields_count: int,
        entity_id: str | None = None,
        nav_route_template: str | None = None,
    ) -> "ExtractionSectionCompletedEvent":
        """Create an extraction_section_completed event.

        ``entity_id`` is None for brand (singleton-per-tenant) and the
        offer_id for offer. ``nav_route_template`` carries literal
        ``{tenantId}``/``{entityId}``/``{section_slug}`` placeholders;
        the subscriber substitutes ``{section_slug}``+``{entityId}`` and
        the FE substitutes ``{tenantId}`` at click time. None falls back
        to legacy module-slug routing for backwards compat.
        """
        return cls(
            event_name="extraction_section_completed",
            tenant_id=tenant_id,
            payload={
                "job_id": job_id,
                "conversation_id": conversation_id,
                "module": module,
                "section_slug": section_slug,
                "section_label": section_label,
                "fields_count": fields_count,
                "entity_id": entity_id,
                "nav_route_template": nav_route_template,
            },
        )


@dataclass
class ExtractionJobCompletedEvent(DomainEvent):
    """Emitted once per successful extraction job.

    Consumed by copilot to insert an extraction_summary card into the conversation.

    Payload keys:
        job_id: str
        conversation_id: str | None
        module: "brand" | "offer" | "asset" | "persona"
        source_ref: str (url or asset_id)
        duration_seconds: int
        filled_fields: list[str]
        filled_fields_by_section: dict[str, list[str]]
        sections_completed: list[str]
        primary_cta_route: str | None
    """

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        job_id: str,
        conversation_id: str | None,
        module: str,
        source_ref: str,
        duration_seconds: int,
        filled_fields: list[str],
        filled_fields_by_section: dict[str, list[str]],
        sections_completed: list[str],
        primary_cta_route: str | None = None,
        entity_id: str | None = None,
        nav_route_template: str | None = None,
    ) -> "ExtractionJobCompletedEvent":
        """Create an extraction_job_completed event.

        ``primary_cta_route`` is pre-formatted by the owning module (only
        ``{tenantId}`` literal remains). ``entity_id`` mirrors the
        section-completed event semantics. ``nav_route_template`` is used
        by the subscriber's safety-net per-section re-emits.
        """
        return cls(
            event_name="extraction_job_completed",
            tenant_id=tenant_id,
            payload={
                "job_id": job_id,
                "conversation_id": conversation_id,
                "module": module,
                "source_ref": source_ref,
                "duration_seconds": duration_seconds,
                "filled_fields": filled_fields,
                "filled_fields_by_section": filled_fields_by_section,
                "sections_completed": sections_completed,
                "primary_cta_route": primary_cta_route,
                "entity_id": entity_id,
                "nav_route_template": nav_route_template,
            },
        )


@dataclass
class BrandSectionUpdatedEvent(DomainEvent):
    """Emitted by ``BrandRepository`` when brand settings persist successfully.

    Consumed by ``brand_summary`` lighthouse worker (F3) to enqueue a
    debounced regeneration of the per-tenant summary that the copilot
    auto-injects into its system prompt for offer/landing/campaign/sales
    routes.

    Payload keys:
        section: section slug whose change drove the save (best-effort —
            ``BrandRepository.save_settings`` writes the whole document so
            ``"brand"`` is the safe default; callers that know the section
            (admin Streamlit, future per-section endpoints) pass it through.
        changed_fields: tuple of dotted field paths reported by the caller.
            Currently informational; the regen task does not depend on it.
    """

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        section: str = "brand",
        changed_fields: tuple[str, ...] = (),
    ) -> "BrandSectionUpdatedEvent":
        """Create a ``brand_section_updated`` event."""
        return cls(
            event_name="brand_section_updated",
            tenant_id=tenant_id,
            payload={
                "section": section,
                "changed_fields": list(changed_fields),
            },
        )


@dataclass
class PersonalityProfileUpdatedEvent(DomainEvent):
    """Emitted by ``PersonalityService`` when a tenant's voice profile changes.

    Triggers cache invalidation in the sales_agent so the next turn picks up
    the recompiled ``system_instruction`` (BRAND_VOICE slot 5). Best-effort —
    a missing subscriber must NEVER crash the publishing service.

    Payload keys:
        profile_id: UUID of the affected ``PersonalityProfile``.
        action: one of ``"selected"``, ``"updated"``, ``"cloned"``,
            ``"activated"``, ``"deleted"``. Informational; subscribers
            invalidate by ``tenant_id`` regardless of action.
    """

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        profile_id: UUID,
        action: str,
    ) -> "PersonalityProfileUpdatedEvent":
        """Create a ``personality_profile_updated`` event."""
        return cls(
            event_name="personality_profile_updated",
            tenant_id=tenant_id,
            payload={
                "profile_id": str(profile_id),
                "action": action,
            },
        )


@dataclass
class AppointmentEvent(DomainEvent):
    """Emitted by scheduling module when appointment status changes.

    Payload keys:
        lead_id: UUID of the lead (legacy leads table)
        appointment_id: UUID of the appointment
        status: AppointmentStatus value (SCHEDULED, COMPLETED, NO_SHOW, CANCELLED)
        email: optional email for profile resolution
    """

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        lead_id: UUID,
        appointment_id: UUID,
        appointment_status: str,
        email: str | None = None,
    ) -> "AppointmentEvent":
        """Create an appointment event, mapping status to event_name."""
        event_names = {
            "SCHEDULED": "appointment_booked",
            "COMPLETED": "appointment_completed",
            "NO_SHOW": "appointment_no_show",
            "CANCELLED": "appointment_cancelled",
        }
        return cls(
            event_name=event_names.get(
                appointment_status,
                f"appointment_{appointment_status.lower()}",
            ),
            tenant_id=tenant_id,
            payload={
                "lead_id": str(lead_id),
                "appointment_id": str(appointment_id),
                "status": appointment_status,
                "email": email,
            },
        )


# ──────────────────────────────────────────────────────────────
# S8 — sales_agent scheduler events
# ──────────────────────────────────────────────────────────────


@dataclass
class BookingLinkCreatedEvent(DomainEvent):
    """Emitted when sales_agent issues a single-use booking link to a lead.

    Subscriber ``schedule_booking_link_followup`` (sales_agent) appends an
    entry to ``agent_state_checkpoints.scheduled_meetings`` so the verify
    cron and reminder engine pick it up. Best-effort.

    Payload keys:
        lead_id: UUID of the lead.
        tracking_id: provider-issued tracking id (Internal = BookingLink.token).
        event_slug: scheduling event_type slug used by the link.
        expires_at: ISO 8601 — link expiration.
        provider_id: ``"internal"`` / ``"calcom"`` / ``"calendly"`` / etc.
    """

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        tracking_id: str,
        event_slug: str,
        expires_at: datetime,
        provider_id: str = "internal",
    ) -> "BookingLinkCreatedEvent":
        """Create a ``booking_link_created`` event."""
        return cls(
            event_name="booking_link_created",
            tenant_id=tenant_id,
            payload={
                "lead_id": str(lead_id),
                "tracking_id": tracking_id,
                "event_slug": event_slug,
                "expires_at": expires_at.isoformat(),
                "provider_id": provider_id,
            },
        )


@dataclass
class BookingMissedEvent(DomainEvent):
    """Emit when an appointment past ``start_time + grace`` is still SCHEDULED.

    Inferred no-show by the ``verify_pending_bookings`` cron when no
    external transition arrives. Distinct from ``appointment_no_show``
    (explicit user-set status from admin agenda UI).

    Subscriber drives recovery cadence: postcheck nudge or escalation.
    Distinct from ``appointment_no_show`` (explicit user-set status from
    admin agenda UI) — this one is *inferred* by the cron.

    Payload keys:
        lead_id: UUID.
        appointment_id: UUID — local AppointmentModel.
        scheduled_at: ISO 8601 — original scheduled start_time.
        grace_minutes: int — grace window applied before flagging missed.
    """

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        appointment_id: UUID,
        scheduled_at: datetime,
        grace_minutes: int = 30,
    ) -> "BookingMissedEvent":
        """Create a ``booking_missed`` event."""
        return cls(
            event_name="booking_missed",
            tenant_id=tenant_id,
            payload={
                "lead_id": str(lead_id),
                "appointment_id": str(appointment_id),
                "scheduled_at": scheduled_at.isoformat(),
                "grace_minutes": grace_minutes,
            },
        )


# ──────────────────────────────────────────────────────────────
# S9 — Payment lifecycle events
# ──────────────────────────────────────────────────────────────


@dataclass
class PaymentLinkCreatedEvent(DomainEvent):
    """Emitted when sales_agent creates a payment link for a lead.

    Payload keys:
        lead_id: UUID.
        external_id: provider-issued payment preference / session id.
        provider_id: ``"mercadopago"`` / ``"stripe"`` / etc.
        url: payment URL shared with lead.
        amount: float.
        currency: ISO 4217 (from offer SSoT).
    """

    @property
    def lead_id(self) -> UUID:
        """Lead UUID."""
        return UUID(self.payload["lead_id"])

    @property
    def external_id(self) -> str:
        """Provider-issued payment preference / session id."""
        return self.payload["external_id"]  # type: ignore[return-value]

    @property
    def provider_id(self) -> str:
        """Payment provider identifier."""
        return self.payload["provider_id"]  # type: ignore[return-value]

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        external_id: str,
        provider_id: str,
        url: str,
        amount: float,
        currency: str,
    ) -> "PaymentLinkCreatedEvent":
        """Create a ``payment_link_created`` event."""
        return cls(
            event_name="payment_link_created",
            tenant_id=tenant_id,
            payload={
                "lead_id": str(lead_id),
                "external_id": external_id,
                "provider_id": provider_id,
                "url": url,
                "amount": amount,
                "currency": currency,
            },
        )


@dataclass
class PaymentReceivedEvent(DomainEvent):
    """Emitted when a payment transitions to PAID.

    Sources: webhook handler OR verify_pending_payments cron.

    Payload keys:
        lead_id, offer_id, payment_id: UUIDs.
        auto_grant: bool — if True, auto_grant_on_paid subscriber fires grant_access.
    """

    @property
    def lead_id(self) -> UUID:
        """Lead UUID."""
        return UUID(self.payload["lead_id"])

    @property
    def offer_id(self) -> UUID:
        """Offer UUID."""
        return UUID(self.payload["offer_id"])

    @property
    def payment_id(self) -> UUID:
        """Payment UUID (PaymentLinkModel PK)."""
        return UUID(self.payload["payment_id"])

    @property
    def auto_grant(self) -> bool:
        """If True, auto_grant_on_paid fires grant_access."""
        return bool(self.payload["auto_grant"])

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        offer_id: UUID,
        payment_id: UUID,
        auto_grant: bool = True,
    ) -> "PaymentReceivedEvent":
        """Create a ``payment_received`` event."""
        return cls(
            event_name="payment_received",
            tenant_id=tenant_id,
            payload={
                "lead_id": str(lead_id),
                "offer_id": str(offer_id),
                "payment_id": str(payment_id),
                "auto_grant": auto_grant,
            },
        )


@dataclass
class AccessGrantedEvent(DomainEvent):
    """Emitted when digital access is delivered to a lead after payment.

    Payload keys:
        lead_id, offer_id, payment_id: UUIDs.
        channels: list[str] — channels through which access was delivered.
        audit_id: UUID of the payment_grant_audit row.
    """

    @property
    def lead_id(self) -> UUID:
        """Lead UUID."""
        return UUID(self.payload["lead_id"])

    @property
    def offer_id(self) -> UUID:
        """Offer UUID."""
        return UUID(self.payload["offer_id"])

    @property
    def payment_id(self) -> UUID:
        """Payment UUID."""
        return UUID(self.payload["payment_id"])

    @property
    def channels(self) -> list[str]:
        """Delivery channels."""
        return self.payload["channels"]  # type: ignore[return-value]

    @classmethod
    def create(
        cls,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        offer_id: UUID,
        payment_id: UUID,
        channels: list[str],
        audit_id: UUID | None = None,
    ) -> "AccessGrantedEvent":
        """Create an ``access_granted`` event."""
        return cls(
            event_name="access_granted",
            tenant_id=tenant_id,
            payload={
                "lead_id": str(lead_id),
                "offer_id": str(offer_id),
                "payment_id": str(payment_id),
                "channels": channels,
                "audit_id": str(audit_id) if audit_id else None,
            },
        )
