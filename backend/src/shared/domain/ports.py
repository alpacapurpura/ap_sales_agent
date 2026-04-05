"""Shared domain ports (ABCs) for cross-module communication.

Consumer defines the port, provider implements it.
Port ABCs live here; implementations live in the provider module.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from pydantic import BaseModel

# ──────────────────────────────────────────────────────────────
# Connection ports (used by analytics, scheduling, sales_agent)
# ──────────────────────────────────────────────────────────────


class ConnectionCredentials(BaseModel):
    """Value object carrying credentials and config for a single connection."""

    channel_type: str
    credentials: dict
    config: dict


class ConnectionPort(ABC):
    """Port for accessing connection credentials across bounded contexts."""

    @abstractmethod
    async def get_credentials(
        self, tenant_id: UUID, channel_type: str
    ) -> ConnectionCredentials:
        """Retrieve credentials for a specific channel type and tenant."""
        ...

    @abstractmethod
    async def list_active_connections(
        self, tenant_id: UUID
    ) -> list[ConnectionCredentials]:
        """List all active connections for a tenant."""
        ...


# ──────────────────────────────────────────────────────────────
# Offer ports (used by analytics, crm, landing)
# ──────────────────────────────────────────────────────────────


class OfferReadDTO(BaseModel):
    """Lightweight read-only projection of Offer for cross-module access."""

    id: UUID
    tenant_id: UUID
    public_name: str
    offer_type: str  # Archetype string (e.g. "producto", "programa")
    value_level: str | None = None  # OfferValueLevel.value string
    pricing_type: str = "one_time"  # "one_time" | "subscription" | "payment_plan"
    currency: str = "USD"


class ProductMappingPort(ABC):
    """Port for resolving external product IDs to internal offer IDs."""

    @abstractmethod
    async def resolve_offer_id(
        self, tenant_id: UUID, source: str, external_product_id: str
    ) -> UUID | None:
        """Resolve a single external product ID to an offer ID."""
        ...

    @abstractmethod
    async def bulk_resolve(
        self, tenant_id: UUID, source: str, external_ids: list[str]
    ) -> dict:
        """Batch resolve: {external_id: offer_id}."""
        ...


class OfferReadPort(ABC):
    """Port for accessing offer data across bounded contexts."""

    @abstractmethod
    async def get_offers_by_tenant(self, tenant_id: UUID) -> list[OfferReadDTO]:
        """All active offers for a tenant (excludes archived, soft-deleted)."""
        ...

    @abstractmethod
    async def get_offer_by_id(
        self, offer_id: UUID, tenant_id: UUID | None = None
    ) -> OfferReadDTO | None:
        """Single offer by ID, scoped to tenant when provided."""
        ...
