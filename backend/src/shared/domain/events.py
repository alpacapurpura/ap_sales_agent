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
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


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
        """
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
