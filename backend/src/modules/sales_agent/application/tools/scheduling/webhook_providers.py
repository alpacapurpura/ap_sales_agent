"""Inbound webhook strategy for scheduler providers (S8).

Internal scheduler does NOT route through this — its bookings come via
Nicolify's own ``POST /event-types/.../book`` endpoint and emit
``AppointmentEvent`` directly.

This module exists for **external** scheduler providers. When a tenant
opts into Cal.com / Calendly / Google Calendar push notifications, that
provider sends inbound webhooks to ``POST /api/v1/sales-agent/webhooks/scheduler/{provider}``
(see ``api/scheduler_webhooks.py``).

DRY:

* Each external provider owns a concrete ``WebhookProvider`` impl.
* The endpoint never branches on ``provider_id`` — it looks up the impl
  in ``SCHEDULER_WEBHOOK_PROVIDERS`` and delegates ``verify_signature`` +
  ``parse_payload``.
* Idempotency is enforced **after** parse via natural key
  ``(provider, tracking_id, event_type, occurred_at)`` against the
  ``scheduler_webhook_event`` table.

Anti-pattern (blocked by ``test_no_hardcoded_webhook_provider.py``):

* ``if provider == "calcom": ...`` inside the endpoint or tools.

Today this module exposes the Protocol + dataclasses + registry only —
no concrete impls. When a real tenant requests Cal.com or Calendly,
the impl plugs in via ``register_webhook_provider`` without changing the
endpoint.
"""

# [SALES-AGENT-S8-WEBHOOK]  # noqa: ERA001

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable
from uuid import UUID

# ──────────────────────────────────────────────────────────────
# Output types
# ──────────────────────────────────────────────────────────────


class WebhookEventType(StrEnum):
    """Normalized inbound webhook event types.

    Concrete provider parsers map their native event names into this enum
    so the dispatcher logic is provider-agnostic.
    """

    BOOKING_CONFIRMED = "booking_confirmed"
    BOOKING_CANCELLED = "booking_cancelled"
    BOOKING_RESCHEDULED = "booking_rescheduled"
    BOOKING_COMPLETED = "booking_completed"
    BOOKING_NO_SHOW = "booking_no_show"
    IGNORED = "ignored"  # parser deemed event irrelevant


@dataclass(frozen=True, slots=True)
class ParsedWebhookEvent:
    """Normalized inbound webhook payload.

    ``raw`` carries the original JSON body for audit (persisted on
    ``scheduler_webhook_event.payload_raw``).
    """

    provider_id: str
    event_type: WebhookEventType
    occurred_at: dt.datetime
    tenant_id: UUID | None = None
    lead_id: UUID | None = None
    tracking_id: str | None = None
    external_appointment_id: str | None = None
    scheduled_at: dt.datetime | None = None
    raw: dict[str, Any] = field(default_factory=dict)


# ──────────────────────────────────────────────────────────────
# Strategy Protocol
# ──────────────────────────────────────────────────────────────


@runtime_checkable
class WebhookProvider(Protocol):
    """Inbound webhook contract for a single external scheduler provider.

    Concrete impls (Cal.com / Calendly / GCal push) MUST set
    ``provider_id`` as a class attribute matching the URL path segment
    that will route to them. Arch test enforces.
    """

    provider_id: str

    def verify_signature(self, body: bytes, headers: dict[str, str], secret: str) -> bool:
        """Constant-time HMAC verify of the raw body against ``secret``.

        Provider-specific header layout:

        * Cal.com   — ``X-Cal-Signature-256``
        * Calendly  — ``Calendly-Webhook-Signature`` (t=...,v1=...)
        * GCal push — channel token in ``X-Goog-Channel-Token`` (not HMAC)
        """
        ...

    def parse_payload(self, payload: dict[str, Any]) -> ParsedWebhookEvent:
        """Normalize a verified payload into ``ParsedWebhookEvent``.

        Returning ``WebhookEventType.IGNORED`` is valid — the endpoint
        will short-circuit but still log to the dedup table for audit.
        """
        ...


# ──────────────────────────────────────────────────────────────
# Registry — empty until a real external provider is wired.
# ──────────────────────────────────────────────────────────────


SCHEDULER_WEBHOOK_PROVIDERS: dict[str, type[WebhookProvider]] = {}


def register_webhook_provider(provider_cls: type[WebhookProvider]) -> None:
    """Register a concrete WebhookProvider class by its ``provider_id``."""
    SCHEDULER_WEBHOOK_PROVIDERS[provider_cls.provider_id] = provider_cls


class UnknownWebhookProviderError(LookupError):
    """Raised by ``webhook_provider_for`` when the provider id is unknown."""


def webhook_provider_for(provider_id: str) -> type[WebhookProvider]:
    """Return the WebhookProvider class registered for ``provider_id``."""
    klass = SCHEDULER_WEBHOOK_PROVIDERS.get(provider_id)
    if klass is None:
        msg = f"Unknown scheduler webhook provider: {provider_id!r}"
        raise UnknownWebhookProviderError(msg)
    return klass
