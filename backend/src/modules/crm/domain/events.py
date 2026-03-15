"""
CRM-specific domain events.

Typed event classes for cross-module communication via the shared EventBus.
Each event has a factory classmethod that sets event_name automatically.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from src.shared.domain.events import DomainEvent


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
        """Factory method. Sets event_name='sale_completed' automatically."""
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
        cancellation_reason: Optional[str] = None,
    ) -> "ChurnEvent":
        """Factory method. Sets event_name='churn_detected' automatically."""
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
