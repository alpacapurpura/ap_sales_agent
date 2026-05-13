"""TenantSubscriptionRepository port (ABC) — shared/billing domain.

Every method is tenant-scoped (tenant_id required).

PR-2 / PI-1 S0.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from luana_core_billing.domain.subscription import TenantSubscription


class TenantSubscriptionRepository(ABC):
    """Port for tenant_subscription table access."""

    @abstractmethod
    async def get_by_tenant_id(self, tenant_id: UUID) -> TenantSubscription | None:
        """Return active subscription for tenant, or None.

        Filters: deleted_at IS NULL.
        tenant_id is mandatory (tenant isolation invariant).
        """
        ...

    @abstractmethod
    async def upsert(self, sub: TenantSubscription) -> TenantSubscription:
        """Create or update subscription for tenant.

        ON CONFLICT (tenant_id) DO UPDATE — idempotent.
        """
        ...

    @abstractmethod
    async def soft_delete(self, tenant_id: UUID) -> None:
        """Soft-delete subscription by setting deleted_at = now()."""
        ...
