"""CampaignStepRepository SQLAlchemy implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

import structlog
from sqlalchemy import func, select, update

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.campaigns.domain.campaign_step import CampaignStep
from src.modules.campaigns.domain.repositories import CampaignStepRepository
from src.modules.campaigns.infrastructure.models.campaign_step_model import CampaignStepModel

logger = structlog.get_logger()


class CampaignStepRepositoryImpl(CampaignStepRepository):
    """Async SQLAlchemy 2.0 implementation of CampaignStepRepository."""

    async def append(self, step: CampaignStep, *, session: AsyncSession) -> None:
        """Persist a new CampaignStep."""
        row = CampaignStepModel(
            id=step.id,
            tenant_id=step.tenant_id,
            campaign_id=step.campaign_id,
            step_type=step.step_type.value,
            step_index=step.step_index,
            label=step.label,
            next_step_ids=[str(uid) for uid in step.next_step_ids],
            step_config=step.step_config,
            created_at=step.created_at,
            updated_at=step.updated_at,
            deleted_at=step.deleted_at,
        )
        session.add(row)
        logger.info(
            "campaign_step_repository_append",
            tenant_id=str(step.tenant_id),
            step_id=str(step.id),
            campaign_id=str(step.campaign_id),
            step_type=step.step_type.value,
        )

    async def update(self, step: CampaignStep, *, session: AsyncSession) -> None:
        """Update an existing CampaignStep."""
        stmt = (
            update(CampaignStepModel)
            .where(
                CampaignStepModel.id == step.id,
                CampaignStepModel.tenant_id == step.tenant_id,
            )
            .values(
                step_type=step.step_type.value,
                step_index=step.step_index,
                label=step.label,
                next_step_ids=[str(uid) for uid in step.next_step_ids],
                step_config=step.step_config,
                updated_at=step.updated_at,
                deleted_at=step.deleted_at,
            )
        )
        await session.execute(stmt)
        logger.info(
            "campaign_step_repository_update",
            tenant_id=str(step.tenant_id),
            step_id=str(step.id),
        )

    async def get_by_id(self, step_id: UUID, tenant_id: UUID, *, session: AsyncSession) -> CampaignStep | None:
        """Fetch by primary key, scoped to tenant. Excludes soft-deleted."""
        stmt = select(CampaignStepModel).where(
            CampaignStepModel.id == step_id,
            CampaignStepModel.tenant_id == tenant_id,
            CampaignStepModel.deleted_at.is_(None),
        )
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_domain(row)

    async def list_by_campaign(
        self, campaign_id: UUID, tenant_id: UUID, *, session: AsyncSession
    ) -> Sequence[CampaignStep]:
        """List all steps for a campaign, ordered by step_index. Excludes soft-deleted."""
        stmt = (
            select(CampaignStepModel)
            .where(
                CampaignStepModel.campaign_id == campaign_id,
                CampaignStepModel.tenant_id == tenant_id,
                CampaignStepModel.deleted_at.is_(None),
            )
            .order_by(CampaignStepModel.step_index.asc())
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()
        return [self._to_domain(row) for row in rows]

    async def soft_delete(self, step_id: UUID, tenant_id: UUID, *, session: AsyncSession) -> None:
        """Set deleted_at = now(). No hard deletes."""
        stmt = (
            update(CampaignStepModel)
            .where(
                CampaignStepModel.id == step_id,
                CampaignStepModel.tenant_id == tenant_id,
                CampaignStepModel.deleted_at.is_(None),
            )
            .values(deleted_at=func.now())
        )
        await session.execute(stmt)
        logger.info(
            "campaign_step_repository_soft_delete",
            tenant_id=str(tenant_id),
            step_id=str(step_id),
        )

    @staticmethod
    def _to_domain(row: CampaignStepModel) -> CampaignStep:
        """Map JSONB list[str] to list[UUID] for next_step_ids."""
        data = {
            "id": row.id,
            "tenant_id": row.tenant_id,
            "campaign_id": row.campaign_id,
            "step_type": row.step_type,
            "step_index": row.step_index,
            "label": row.label,
            "next_step_ids": [UUID(s) for s in (row.next_step_ids or [])],
            "step_config": row.step_config or {},
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "deleted_at": row.deleted_at,
        }
        return CampaignStep.model_validate(data)
