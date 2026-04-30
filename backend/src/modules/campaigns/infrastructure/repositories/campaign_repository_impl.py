"""CampaignRepository SQLAlchemy implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from sqlalchemy import func, select, update

if TYPE_CHECKING:
    from collections.abc import Sequence
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from src.modules.campaigns.domain.enums import CampaignStatus

from src.modules.campaigns.domain.campaign import Campaign
from src.modules.campaigns.domain.repositories import CampaignRepository
from src.modules.campaigns.infrastructure.models.campaign_model import CampaignModel

logger = structlog.get_logger()


class CampaignRepositoryImpl(CampaignRepository):
    """Async SQLAlchemy 2.0 implementation of CampaignRepository."""

    async def append(self, campaign: Campaign, *, session: AsyncSession) -> None:
        """Persist a new Campaign."""
        row = CampaignModel(
            id=campaign.id,
            tenant_id=campaign.tenant_id,
            name=campaign.name,
            description=campaign.description,
            campaign_type=campaign.campaign_type.value,
            status=campaign.status.value,
            segment_id=campaign.segment_id,
            segment_snapshot_id=campaign.segment_snapshot_id,
            channel_priority=campaign.channel_priority,
            offer_id=campaign.offer_id,
            brand_summary_id=campaign.brand_summary_id,
            config=campaign.config,
            scheduled_at=campaign.scheduled_at,
            launched_at=campaign.launched_at,
            completed_at=campaign.completed_at,
            created_by_user_id=campaign.created_by_user_id,
            created_by_source=campaign.created_by_source,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at,
            deleted_at=campaign.deleted_at,
        )
        session.add(row)
        logger.info(
            "campaign_repository_append",
            tenant_id=str(campaign.tenant_id),
            campaign_id=str(campaign.id),
            status=campaign.status.value,
            campaign_type=campaign.campaign_type.value,
        )

    async def update(self, campaign: Campaign, *, session: AsyncSession) -> None:
        """Update all mutable fields of an existing Campaign."""
        stmt = (
            update(CampaignModel)
            .where(
                CampaignModel.id == campaign.id,
                CampaignModel.tenant_id == campaign.tenant_id,
            )
            .values(
                name=campaign.name,
                description=campaign.description,
                campaign_type=campaign.campaign_type.value,
                status=campaign.status.value,
                segment_id=campaign.segment_id,
                segment_snapshot_id=campaign.segment_snapshot_id,
                channel_priority=campaign.channel_priority,
                offer_id=campaign.offer_id,
                brand_summary_id=campaign.brand_summary_id,
                config=campaign.config,
                scheduled_at=campaign.scheduled_at,
                launched_at=campaign.launched_at,
                completed_at=campaign.completed_at,
                created_by_source=campaign.created_by_source,
                updated_at=campaign.updated_at,
                deleted_at=campaign.deleted_at,
            )
        )
        await session.execute(stmt)
        logger.info(
            "campaign_repository_update",
            tenant_id=str(campaign.tenant_id),
            campaign_id=str(campaign.id),
            status=campaign.status.value,
        )

    async def get_by_id(self, campaign_id: UUID, tenant_id: UUID, *, session: AsyncSession) -> Campaign | None:
        """Fetch by primary key, scoped to tenant. Excludes soft-deleted."""
        stmt = select(CampaignModel).where(
            CampaignModel.id == campaign_id,
            CampaignModel.tenant_id == tenant_id,
            CampaignModel.deleted_at.is_(None),
        )
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return Campaign.model_validate(row)

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        *,
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
        status_filter: Sequence[CampaignStatus] | None = None,
    ) -> Sequence[Campaign]:
        """List campaigns for a tenant. Excludes soft-deleted."""
        stmt = select(CampaignModel).where(
            CampaignModel.tenant_id == tenant_id,
            CampaignModel.deleted_at.is_(None),
        )
        if status_filter:
            stmt = stmt.where(CampaignModel.status.in_([s.value for s in status_filter]))
        stmt = stmt.order_by(CampaignModel.created_at.desc()).limit(limit).offset(offset)
        result = await session.execute(stmt)
        rows = result.scalars().all()
        return [Campaign.model_validate(row) for row in rows]

    async def soft_delete(self, campaign_id: UUID, tenant_id: UUID, *, session: AsyncSession) -> None:
        """Set deleted_at = now(). No hard deletes."""
        stmt = (
            update(CampaignModel)
            .where(
                CampaignModel.id == campaign_id,
                CampaignModel.tenant_id == tenant_id,
                CampaignModel.deleted_at.is_(None),
            )
            .values(deleted_at=func.now())
        )
        await session.execute(stmt)
        logger.info(
            "campaign_repository_soft_delete",
            tenant_id=str(tenant_id),
            campaign_id=str(campaign_id),
        )
