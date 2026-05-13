"""CampaignReadAdapter — implements CampaignReadOnlyPort for cross-module access.

PI-2 copilot subagent and CRM Hub consume via shared/links/ports/campaigns.py.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


class CampaignReadAdapter:
    """Read-only adapter for cross-module campaign access.

    Instantiated lazily via get_campaign_read_port() factory.
    Uses CampaignRepository directly (no service dependency injection needed for read-only).
    """

    async def get_campaign_summary(
        self,
        *,
        tenant_id: UUID,
        campaign_id: UUID,
        session: AsyncSession,
    ) -> dict | None:
        """Return dict shape compatible with CampaignResponse fields.

        Returns None if campaign not found or not owned by tenant.
        """
        from luana_core_campaigns.infrastructure.repositories.campaign_repository_impl import (
            CampaignRepositoryImpl,
        )

        repo = CampaignRepositoryImpl()
        campaign = await repo.get_by_id(campaign_id, tenant_id, session=session)
        if campaign is None:
            return None
        return {
            "id": str(campaign.id),
            "tenant_id": str(campaign.tenant_id),
            "name": campaign.name,
            "description": campaign.description,
            "campaign_type": campaign.campaign_type.value,
            "status": campaign.status.value,
            "segment_id": str(campaign.segment_id) if campaign.segment_id else None,
            "offer_id": str(campaign.offer_id) if campaign.offer_id else None,
            "scheduled_at": campaign.scheduled_at.isoformat() if campaign.scheduled_at else None,
            "launched_at": campaign.launched_at.isoformat() if campaign.launched_at else None,
            "completed_at": campaign.completed_at.isoformat() if campaign.completed_at else None,
            "created_at": campaign.created_at.isoformat(),
            "updated_at": campaign.updated_at.isoformat(),
        }
