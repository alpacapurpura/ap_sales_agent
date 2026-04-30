"""Tests for SQLAPlanRepository — infrastructure layer.

RED first (TDD-mandatory). Tests use SQLite in-memory via conftest db fixture.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.shared.billing.domain.plan import PlanConfig
from src.shared.billing.infrastructure.models.plan_config_model import PlanConfigModel
from src.shared.billing.infrastructure.plan_repository_impl import SQLAPlanRepository
from src.shared.domain.base_entity import Base

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def async_session():
    """In-memory async SQLite session for billing repo tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session
    await engine.dispose()


def _free_plan(**overrides) -> PlanConfig:
    defaults = {
        "plan_id": "free",
        "display_name": "Free",
        "llm_budget_total_usd": Decimal("5.00"),
        "is_default": True,
    }
    defaults.update(overrides)
    return PlanConfig(**defaults)


class TestSQLAPlanRepository:
    async def test_get_by_id_not_found(self, async_session: AsyncSession) -> None:
        repo = SQLAPlanRepository(async_session)
        result = await repo.get_by_id("nonexistent")
        assert result is None

    async def test_upsert_and_get_by_id(self, async_session: AsyncSession) -> None:
        repo = SQLAPlanRepository(async_session)
        plan = _free_plan()
        stored = await repo.upsert(plan)
        assert stored.plan_id == "free"
        assert stored.llm_budget_total_usd == Decimal("5.00")
        assert stored.is_default is True

    async def test_upsert_idempotent(self, async_session: AsyncSession) -> None:
        repo = SQLAPlanRepository(async_session)
        plan = _free_plan()
        await repo.upsert(plan)
        # Second upsert with different display_name (update)
        updated = PlanConfig(**{**plan.model_dump(), "display_name": "Free Updated"})
        stored = await repo.upsert(updated)
        assert stored.display_name == "Free Updated"

    async def test_list_active_filters_inactive(self, async_session: AsyncSession) -> None:
        repo = SQLAPlanRepository(async_session)
        active = _free_plan()
        inactive = PlanConfig(
            plan_id="inactive_test",
            display_name="Inactive",
            llm_budget_total_usd=Decimal("1.00"),
            is_active=False,
        )
        await repo.upsert(active)
        await repo.upsert(inactive)
        result = await repo.list_active()
        plan_ids = [p.plan_id for p in result]
        assert "free" in plan_ids
        assert "inactive_test" not in plan_ids

    async def test_get_default_returns_is_default_row(self, async_session: AsyncSession) -> None:
        repo = SQLAPlanRepository(async_session)
        await repo.upsert(_free_plan(is_default=True))
        await repo.upsert(_free_plan(plan_id="basic", is_default=False, llm_budget_total_usd=Decimal("15.00")))
        default = await repo.get_default()
        assert default is not None
        assert default.is_default is True
        assert default.plan_id == "free"

    async def test_get_default_none_when_no_default(self, async_session: AsyncSession) -> None:
        repo = SQLAPlanRepository(async_session)
        await repo.upsert(_free_plan(is_default=False))
        default = await repo.get_default()
        assert default is None

    async def test_list_active_ordered_by_budget(self, async_session: AsyncSession) -> None:
        repo = SQLAPlanRepository(async_session)
        for plan_id, budget in [("ultra", Decimal("95.00")), ("free", Decimal("5.00")), ("basic", Decimal("15.00"))]:
            await repo.upsert(
                PlanConfig(
                    plan_id=plan_id,
                    display_name=plan_id.capitalize(),
                    llm_budget_total_usd=budget,
                    is_default=(plan_id == "free"),
                )
            )
        result = await repo.list_active()
        budgets = [p.llm_budget_total_usd for p in result]
        assert budgets == sorted(budgets)
