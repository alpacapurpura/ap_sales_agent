"""Tests for SQLASubscriptionRepository — infrastructure layer.

RED first. Uses in-memory async SQLite.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.shared.billing.domain.plan import PlanConfig
from src.shared.billing.domain.subscription import TenantSubscription
from src.shared.billing.infrastructure.plan_repository_impl import SQLAPlanRepository
from src.shared.billing.infrastructure.subscription_repository_impl import (
    SQLASubscriptionRepository,
)
from src.shared.domain.base_entity import Base

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def async_session():
    """In-memory async SQLite session for subscription repo tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def plan_in_db(async_session: AsyncSession) -> PlanConfig:
    """Insert a 'free' plan so FK constraint for subscription is satisfied."""
    repo = SQLAPlanRepository(async_session)
    plan = PlanConfig(
        plan_id="free",
        display_name="Free",
        llm_budget_total_usd=Decimal("5.00"),
        is_default=True,
    )
    return await repo.upsert(plan)


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _sub(tenant_id=None, **overrides) -> TenantSubscription:
    now = _now()
    return TenantSubscription(
        tenant_id=tenant_id or uuid4(),
        plan_id="free",
        activated_at=now,
        updated_at=now,
        **overrides,
    )


class TestSQLASubscriptionRepository:
    async def test_get_by_tenant_id_not_found(self, async_session: AsyncSession) -> None:
        repo = SQLASubscriptionRepository(async_session)
        result = await repo.get_by_tenant_id(uuid4())
        assert result is None

    async def test_upsert_and_get(self, async_session: AsyncSession, plan_in_db: PlanConfig) -> None:
        repo = SQLASubscriptionRepository(async_session)
        tid = uuid4()
        sub = _sub(tenant_id=tid)
        stored = await repo.upsert(sub)
        assert stored.tenant_id == tid
        assert stored.plan_id == "free"
        assert stored.custom_overrides == {}

    async def test_upsert_merges_custom_overrides(self, async_session: AsyncSession, plan_in_db: PlanConfig) -> None:
        repo = SQLASubscriptionRepository(async_session)
        tid = uuid4()
        overrides = {"max_outbound_msg_per_day": 5000}
        sub = _sub(tenant_id=tid, custom_overrides=overrides)
        stored = await repo.upsert(sub)
        assert stored.custom_overrides == overrides

    async def test_update_via_upsert(self, async_session: AsyncSession, plan_in_db: PlanConfig) -> None:
        repo = SQLASubscriptionRepository(async_session)
        tid = uuid4()
        await repo.upsert(_sub(tenant_id=tid))
        # Update with new custom_overrides
        now = _now()
        updated = TenantSubscription(
            tenant_id=tid,
            plan_id="free",
            activated_at=now,
            updated_at=now,
            custom_overrides={"llm_budget_total_usd": 50},
        )
        stored2 = await repo.upsert(updated)
        assert stored2.custom_overrides == {"llm_budget_total_usd": 50}

    async def test_soft_delete(self, async_session: AsyncSession, plan_in_db: PlanConfig) -> None:
        repo = SQLASubscriptionRepository(async_session)
        tid = uuid4()
        await repo.upsert(_sub(tenant_id=tid))
        await repo.soft_delete(tid)
        result = await repo.get_by_tenant_id(tid)
        # get_by_tenant_id filters deleted_at IS NULL → should return None
        assert result is None

    async def test_get_by_tenant_id_excludes_deleted(self, async_session: AsyncSession, plan_in_db: PlanConfig) -> None:
        repo = SQLASubscriptionRepository(async_session)
        tid = uuid4()
        await repo.upsert(_sub(tenant_id=tid))
        await repo.soft_delete(tid)
        sub_restored = _sub(tenant_id=tid)
        await repo.upsert(sub_restored)
        result = await repo.get_by_tenant_id(tid)
        assert result is not None
        assert result.deleted_at is None

    async def test_tenant_isolation_cross_tenant(self, async_session: AsyncSession, plan_in_db: PlanConfig) -> None:
        repo = SQLASubscriptionRepository(async_session)
        tid_a = uuid4()
        tid_b = uuid4()
        await repo.upsert(_sub(tenant_id=tid_a))
        # Lookup with tid_b returns None
        result = await repo.get_by_tenant_id(tid_b)
        assert result is None
