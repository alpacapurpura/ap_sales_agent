"""SQLAlchemy 2.0 async implementation of PlanRepository.

PR-2 / PI-1 S0.
"""

from __future__ import annotations

from decimal import Decimal

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.billing.domain.plan import PlanConfig
from src.shared.billing.domain.plan_repository import PlanRepository
from src.shared.billing.infrastructure.models.plan_config_model import PlanConfigModel

logger = structlog.get_logger(__name__)


def _model_to_vo(m: PlanConfigModel) -> PlanConfig:
    """Map ORM row to immutable VO."""
    return PlanConfig(
        plan_id=m.plan_id,
        display_name=m.display_name,
        llm_budget_total_usd=Decimal(str(m.llm_budget_total_usd)),
        sales_agent_reserved_pct=Decimal(str(m.sales_agent_reserved_pct)),
        max_outbound_msg_per_day=m.max_outbound_msg_per_day,
        max_campaigns_active=m.max_campaigns_active,
        max_segment_size=m.max_segment_size,
        max_contacts_total=m.max_contacts_total,
        features=m.features or {},
        is_active=m.is_active,
        is_default=m.is_default,
    )


class SQLAPlanRepository(PlanRepository):
    """SQLAlchemy 2.0 async implementation of PlanRepository."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind repository to async session."""
        self._session = session

    async def get_by_id(self, plan_id: str) -> PlanConfig | None:
        """Return plan by plan_id or None."""
        stmt = select(PlanConfigModel).where(PlanConfigModel.plan_id == plan_id)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _model_to_vo(row) if row else None

    async def get_default(self) -> PlanConfig | None:
        """Return the plan with is_default=TRUE (partial unique index, LIMIT 1).

        PM Q6: exactly one default row is guaranteed by the partial unique index.
        """
        stmt = select(PlanConfigModel).where(PlanConfigModel.is_default.is_(True)).limit(1)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return _model_to_vo(row) if row else None

    async def list_active(self) -> list[PlanConfig]:
        """Return all active plans ordered by budget ascending."""
        stmt = (
            select(PlanConfigModel)
            .where(PlanConfigModel.is_active.is_(True))
            .order_by(PlanConfigModel.llm_budget_total_usd.asc())
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [_model_to_vo(r) for r in rows]

    async def upsert(self, plan: PlanConfig) -> PlanConfig:
        """Create or update a plan row. Returns stored VO."""
        existing_result = await self._session.execute(
            select(PlanConfigModel).where(PlanConfigModel.plan_id == plan.plan_id)
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            await self._session.execute(
                update(PlanConfigModel)
                .where(PlanConfigModel.plan_id == plan.plan_id)
                .values(
                    display_name=plan.display_name,
                    llm_budget_total_usd=plan.llm_budget_total_usd,
                    sales_agent_reserved_pct=plan.sales_agent_reserved_pct,
                    max_outbound_msg_per_day=plan.max_outbound_msg_per_day,
                    max_campaigns_active=plan.max_campaigns_active,
                    max_segment_size=plan.max_segment_size,
                    max_contacts_total=plan.max_contacts_total,
                    features=plan.features,
                    is_active=plan.is_active,
                    is_default=plan.is_default,
                )
            )
        else:
            model = PlanConfigModel(
                plan_id=plan.plan_id,
                display_name=plan.display_name,
                llm_budget_total_usd=plan.llm_budget_total_usd,
                sales_agent_reserved_pct=plan.sales_agent_reserved_pct,
                max_outbound_msg_per_day=plan.max_outbound_msg_per_day,
                max_campaigns_active=plan.max_campaigns_active,
                max_segment_size=plan.max_segment_size,
                max_contacts_total=plan.max_contacts_total,
                features=plan.features,
                is_active=plan.is_active,
                is_default=plan.is_default,
            )
            self._session.add(model)
        await self._session.flush()
        refreshed = await self.get_by_id(plan.plan_id)
        assert refreshed is not None  # noqa: S101 — post-upsert invariant
        return refreshed
