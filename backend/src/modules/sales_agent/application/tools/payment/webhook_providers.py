"""Payment webhook Strategy pattern — S9.

Mirrors scheduling/webhook_providers.py.
No hardcoded provider names in generic tools — only in this file.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import hmac
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol, runtime_checkable
from uuid import UUID

import structlog

logger = structlog.get_logger()


class PaymentWebhookEventType(StrEnum):
    """Canonical webhook event types from any payment provider."""

    PAID = "payment.paid"
    FAILED = "payment.failed"
    REFUNDED = "payment.refunded"
    PENDING = "payment.pending"
    CANCELLED = "payment.cancelled"
    OTHER = "payment.other"


@dataclass(frozen=True, slots=True)
class ParsedPaymentWebhookEvent:
    """Provider-agnostic parsed webhook event."""

    provider_id: str
    event_type: PaymentWebhookEventType
    occurred_at: dt.datetime
    tenant_id: UUID | None
    lead_id: UUID | None
    external_payment_id: str | None
    payment_status: str
    raw: dict[str, Any]


@runtime_checkable
class PaymentWebhookProvider(Protocol):
    """Strategy Protocol for payment webhook verification + parsing."""

    provider_id: str

    def verify_signature(
        self,
        body: bytes,
        headers: dict[str, str],
        secret: str,
    ) -> bool:
        """Return True if signature is valid. Fail-closed: empty secret → False."""
        ...

    def parse_payload(
        self,
        payload: dict[str, Any],
    ) -> ParsedPaymentWebhookEvent:
        """Parse provider-specific payload into canonical event."""
        ...


# ─────────────────────────────────────────────────────────────
# Concrete webhook providers
# ─────────────────────────────────────────────────────────────


class MercadoPagoWebhookProvider:
    """MP webhook: x-signature = ts=<ts>,v1=<HMAC-SHA256(ts:body)>."""

    provider_id = "mercadopago"

    def verify_signature(
        self,
        body: bytes,
        headers: dict[str, str],
        secret: str,
    ) -> bool:
        """Verify MP x-signature header."""
        if not secret:
            return False
        sig_header = headers.get("x-signature", "")
        parts = dict(p.split("=", 1) for p in sig_header.split(",") if "=" in p)
        ts = parts.get("ts", "")
        v1 = parts.get("v1", "")
        if not ts or not v1:
            return False
        manifest = f"ts:{ts};body:{body.decode('utf-8')}"
        expected = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, v1)

    def parse_payload(self, payload: dict[str, Any]) -> ParsedPaymentWebhookEvent:
        """Parse MP webhook payload.

        MP sends a minimal notification — the real status requires a 2nd
        GET /v1/payments/{data.id} call (done in the webhook handler).
        """
        action = payload.get("action", "")
        event_type_map = {
            "payment.created": PaymentWebhookEventType.PENDING,
            "payment.updated": PaymentWebhookEventType.PAID,
        }
        event_type = event_type_map.get(action, PaymentWebhookEventType.OTHER)

        data = payload.get("data", {})
        external_id = str(data.get("id", ""))

        occurred_str = payload.get("date_created") or payload.get("date_last_updated")
        try:
            occurred_at = dt.datetime.fromisoformat(occurred_str) if occurred_str else dt.datetime.now(dt.UTC)
        except (ValueError, TypeError):
            occurred_at = dt.datetime.now(dt.UTC)

        metadata = payload.get("metadata", {})
        tenant_id: UUID | None = None
        lead_id: UUID | None = None
        try:
            if metadata.get("tenant_id"):
                tenant_id = UUID(metadata["tenant_id"])
            if metadata.get("lead_id"):
                lead_id = UUID(metadata["lead_id"])
        except (ValueError, KeyError):
            pass

        return ParsedPaymentWebhookEvent(
            provider_id=self.provider_id,
            event_type=event_type,
            occurred_at=occurred_at,
            tenant_id=tenant_id,
            lead_id=lead_id,
            external_payment_id=external_id or None,
            payment_status=payload.get("status", "pending"),
            raw=payload,
        )


class StripeWebhookProvider:
    """Stripe webhook: Stripe-Signature header via stripe.Webhook.construct_event."""

    provider_id = "stripe"

    def verify_signature(
        self,
        body: bytes,
        headers: dict[str, str],
        secret: str,
    ) -> bool:
        """Verify Stripe-Signature header."""
        if not secret:
            return False
        sig_header = headers.get("stripe-signature", "")
        if not sig_header:
            return False
        try:
            import stripe  # type: ignore[import]

            stripe.Webhook.construct_event(body, sig_header, secret)
            return True
        except Exception:  # noqa: BLE001
            return False

    def parse_payload(self, payload: dict[str, Any]) -> ParsedPaymentWebhookEvent:
        """Parse Stripe webhook payload."""
        event_type_raw = payload.get("type", "")
        event_type_map = {
            "checkout.session.completed": PaymentWebhookEventType.PAID,
            "payment_intent.payment_failed": PaymentWebhookEventType.FAILED,
            "charge.refunded": PaymentWebhookEventType.REFUNDED,
        }
        event_type = event_type_map.get(event_type_raw, PaymentWebhookEventType.OTHER)

        obj = payload.get("data", {}).get("object", {})
        external_id = obj.get("id", "")
        metadata = obj.get("metadata", {})

        created_ts = payload.get("created")
        occurred_at = dt.datetime.fromtimestamp(created_ts, tz=dt.UTC) if created_ts else dt.datetime.now(dt.UTC)

        tenant_id: UUID | None = None
        lead_id: UUID | None = None
        try:
            if metadata.get("tenant_id"):
                tenant_id = UUID(metadata["tenant_id"])
            if metadata.get("lead_id"):
                lead_id = UUID(metadata["lead_id"])
        except (ValueError, KeyError):
            pass

        return ParsedPaymentWebhookEvent(
            provider_id=self.provider_id,
            event_type=event_type,
            occurred_at=occurred_at,
            tenant_id=tenant_id,
            lead_id=lead_id,
            external_payment_id=external_id or None,
            payment_status="paid" if event_type == PaymentWebhookEventType.PAID else "pending",
            raw=payload,
        )


# ─────────────────────────────────────────────────────────────
# Registry
# ─────────────────────────────────────────────────────────────

PAYMENT_WEBHOOK_PROVIDERS: dict[str, type[PaymentWebhookProvider]] = {
    "mercadopago": MercadoPagoWebhookProvider,  # type: ignore[type-abstract]
    "stripe": StripeWebhookProvider,  # type: ignore[type-abstract]
}


def register_payment_webhook_provider(provider: type[PaymentWebhookProvider]) -> None:
    """Register a provider class in the global registry (test + plugin hook)."""
    PAYMENT_WEBHOOK_PROVIDERS[provider.provider_id] = provider  # type: ignore[arg-type]


def webhook_provider_for(provider_id: str) -> type[PaymentWebhookProvider] | None:
    """Look up webhook provider class by id. Returns None if unknown."""
    return PAYMENT_WEBHOOK_PROVIDERS.get(provider_id)
