"""Payment gateway Strategy pattern — S9.

Mirrors scheduling/providers.py exactly.
No hardcoded provider names outside this file + webhook_providers.py.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

import structlog

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

logger = structlog.get_logger()


class PaymentStatusEnum(StrEnum):
    """Canonical payment status values."""

    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class PaymentLinkOutput:
    """Result of create_payment_link — provider-agnostic."""

    external_id: str
    url: str
    provider_id: str
    amount: float | None = None
    currency: str | None = None
    expires_at: Any | None = None
    metadata: dict[str, Any] | None = None


@runtime_checkable
class PaymentGatewayProvider(Protocol):
    """Strategy Protocol for payment gateways.

    Concrete impls: MercadoPagoPaymentProvider, StripePaymentProvider.
    Registry key = provider_id class attribute.
    """

    provider_id: str

    def create_payment_link(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        offer_id: UUID,
        amount: float,
        currency: str,
        metadata: dict[str, Any],
    ) -> PaymentLinkOutput:
        """Create a payment link and return provider-issued URL + external_id."""
        ...

    def verify_payment(self, external_id: str) -> PaymentStatusEnum:
        """Query provider for current payment status."""
        ...


# ─────────────────────────────────────────────────────────────
# Concrete providers
# ─────────────────────────────────────────────────────────────


class MercadoPagoPaymentProvider:
    """Mercado Pago Checkout Preferences — covers AR/BR/MX/CO/PE."""

    provider_id = "mercadopago"

    def create_payment_link(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        offer_id: UUID,
        amount: float,
        currency: str,
        metadata: dict[str, Any],
    ) -> PaymentLinkOutput:
        """Create MP checkout preference via POST /checkout/preferences."""
        import httpx

        access_token = os.environ.get("MERCADOPAGO_ACCESS_TOKEN", "")
        payload = {
            "items": [
                {
                    "title": metadata.get("offer_title", "Producto"),
                    "quantity": 1,
                    "currency_id": currency,
                    "unit_price": amount,
                }
            ],
            "external_reference": f"{tenant_id}:{lead_id}:{offer_id}",
            "metadata": {
                "tenant_id": str(tenant_id),
                "lead_id": str(lead_id),
                "offer_id": str(offer_id),
            },
        }
        resp = httpx.post(
            "https://api.mercadopago.com/checkout/preferences",
            json=payload,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return PaymentLinkOutput(
            external_id=data["id"],
            url=data["init_point"],
            provider_id=self.provider_id,
        )

    def verify_payment(self, external_id: str) -> PaymentStatusEnum:
        """Query MP payment status via GET /v1/payments/{id}.

        MP webhooks contain only the payment *id*, not the full status,
        so a second API call is always required for authoritative status.
        """
        import httpx

        access_token = os.environ.get("MERCADOPAGO_ACCESS_TOKEN", "")
        resp = httpx.get(
            f"https://api.mercadopago.com/v1/payments/{external_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        status_map = {
            "approved": PaymentStatusEnum.PAID,
            "pending": PaymentStatusEnum.PENDING,
            "in_process": PaymentStatusEnum.PENDING,
            "rejected": PaymentStatusEnum.FAILED,
            "cancelled": PaymentStatusEnum.CANCELLED,
            "refunded": PaymentStatusEnum.REFUNDED,
            "charged_back": PaymentStatusEnum.REFUNDED,
        }
        return status_map.get(data.get("status", ""), PaymentStatusEnum.PENDING)


class StripePaymentProvider:
    """Stripe Payment Links — international-ready."""

    provider_id = "stripe"

    def create_payment_link(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        offer_id: UUID,
        amount: float,
        currency: str,
        metadata: dict[str, Any],
    ) -> PaymentLinkOutput:
        """Create Stripe checkout session."""
        import stripe  # type: ignore[import]

        stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": currency.lower(),
                        "product_data": {"name": metadata.get("offer_title", "Producto")},
                        "unit_amount": int(amount * 100),
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=metadata.get("success_url", "https://app.nicolify.com/payment/success"),
            cancel_url=metadata.get("cancel_url", "https://app.nicolify.com/payment/cancel"),
            metadata={
                "tenant_id": str(tenant_id),
                "lead_id": str(lead_id),
                "offer_id": str(offer_id),
            },
        )
        return PaymentLinkOutput(
            external_id=session["id"],
            url=session["url"],
            provider_id=self.provider_id,
        )

    def verify_payment(self, external_id: str) -> PaymentStatusEnum:
        """Query Stripe checkout session status."""
        import stripe  # type: ignore[import]

        stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
        session = stripe.checkout.Session.retrieve(external_id)
        status_map = {
            "complete": PaymentStatusEnum.PAID,
            "open": PaymentStatusEnum.PENDING,
            "expired": PaymentStatusEnum.EXPIRED,
        }
        return status_map.get(session.get("status", ""), PaymentStatusEnum.PENDING)


# ─────────────────────────────────────────────────────────────
# Registry + resolver
# ─────────────────────────────────────────────────────────────

# Re-export alias so tests can import PaymentWebhookEvent from this module.
# Canonical definition lives in webhook_providers.py.
from src.modules.sales_agent.application.tools.payment.webhook_providers import (
    ParsedPaymentWebhookEvent as PaymentWebhookEvent,  # noqa: F401
)

PAYMENT_PROVIDERS: dict[str, type[PaymentGatewayProvider]] = {
    "mercadopago": MercadoPagoPaymentProvider,  # type: ignore[type-abstract]
    "stripe": StripePaymentProvider,  # type: ignore[type-abstract]
}


def payment_provider_for_tenant(
    db: Session,
    tenant_id: UUID,
    *,
    preferred_provider_id: str | None = None,
) -> PaymentGatewayProvider:
    """Resolve the active PaymentGatewayProvider for a tenant.

    Resolution order:
    1. ``preferred_provider_id`` arg (tool-level override).
    2. connections.ChannelConnectionModel with channel_type="payment" (per-tenant config).
    3. Env-var ``DEFAULT_PAYMENT_PROVIDER`` fallback.
    4. First registered provider (last resort).
    """
    if preferred_provider_id and preferred_provider_id in PAYMENT_PROVIDERS:
        return PAYMENT_PROVIDERS[preferred_provider_id]()

    try:
        from src.shared.links.ports.payment_connection import (
            get_payment_connection_provider,
        )

        provider_id = get_payment_connection_provider(db, tenant_id)
        if provider_id and provider_id in PAYMENT_PROVIDERS:
            return PAYMENT_PROVIDERS[provider_id]()
    except Exception:  # noqa: BLE001
        logger.warning("payment_provider_lookup_failed", exc_info=True)

    env_default = os.environ.get("DEFAULT_PAYMENT_PROVIDER", "")
    if env_default in PAYMENT_PROVIDERS:
        return PAYMENT_PROVIDERS[env_default]()

    return next(iter(PAYMENT_PROVIDERS.values()))()
