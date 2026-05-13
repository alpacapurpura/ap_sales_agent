"""SQLAlchemy 2.0 async implementation of TenantSubscriptionRepository.

PR-2 / PI-1 S0.
"""

from __future__ import annotations

from uuid import UUID

import structlog
from luana_core_billing.domain.subscription import TenantSubscription
from luana_core_billing.domain.subscription_repository import TenantSubscriptionRepository
from luana_core_billing.infrastructure.models.tenant_subscription_model import (
    TenantSubscriptionModel,
)
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

logger = structlog.get_logger(__name__)


def _model_to_vo(m: TenantSubscriptionModel) -> TenantSubscription:
    """Map ORM row to immutable VO."""
    return TenantSubscription(
        tenant_id=m.tenant_id,
        plan_id=m.plan_id,
        cycle_anchor_day=m.cycle_anchor_day,
        custom_overrides=m.custom_overrides or {},
        trial_ends_at=m.trial_ends_at,
        activated_at=m.activated_at,
        updated_at=m.updated_at,
        deleted_at=m.deleted_at,
    )


class SQLASubscriptionRepository(TenantSubscriptionRepository):
    """SQLAlchemy 2.0 async implementation of TenantSubscriptionRepository."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind repository to async session."""
        self._session = session

    async def get_by_tenant_id(self, tenant_id: UUID) -> TenantSubscription | None:
        """Return active subscription for tenant. tenant_id mandatory."""
        stmt = select(TenantSubscriptionModel).where(
            TenantSubscriptionModel.tenant_id == tenant_id,
            TenantSubscriptionModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _model_to_vo(row) if row else None

    async def upsert(self, sub: TenantSubscription) -> TenantSubscription:
        """Create or update subscription for tenant."""
        existing_result = await self._session.execute(
            select(TenantSubscriptionModel).where(TenantSubscriptionModel.tenant_id == sub.tenant_id)
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            await self._session.execute(
                update(TenantSubscriptionModel)
                .where(TenantSubscriptionModel.tenant_id == sub.tenant_id)
                .values(
                    plan_id=sub.plan_id,
                    cycle_anchor_day=sub.cycle_anchor_day,
                    custom_overrides=sub.custom_overrides,
                    trial_ends_at=sub.trial_ends_at,
                    updated_at=func.now(),
                    deleted_at=None,
                )
            )
        else:
            model = TenantSubscriptionModel(
                tenant_id=sub.tenant_id,
                plan_id=sub.plan_id,
                cycle_anchor_day=sub.cycle_anchor_day,
                custom_overrides=sub.custom_overrides,
                trial_ends_at=sub.trial_ends_at,
                activated_at=sub.activated_at,
                updated_at=sub.updated_at,
            )
            self._session.add(model)
        await self._session.flush()
        refreshed = await self.get_by_tenant_id(sub.tenant_id)
        assert refreshed is not None  # noqa: S101 — post-upsert invariant
        return refreshed

    async def soft_delete(self, tenant_id: UUID) -> None:
        """Soft-delete subscription (set deleted_at = now())."""
        await self._session.execute(
            update(TenantSubscriptionModel)
            .where(
                TenantSubscriptionModel.tenant_id == tenant_id,
                TenantSubscriptionModel.deleted_at.is_(None),
            )
            .values(deleted_at=func.now())
        )
        await self._session.flush()
