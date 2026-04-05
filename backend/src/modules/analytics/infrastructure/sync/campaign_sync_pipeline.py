"""Campaign Sync Pipeline — orchestrates extraction and storage of campaign hierarchy.

Separate from ETLPipeline (metrics) to keep concerns isolated.
Runs as an independent job via ARQ.
"""

import logging
from uuid import UUID

import httpx

from src.modules.analytics.infrastructure.providers.meta_campaign_provider import (
    MetaCampaignProvider,
)
from src.modules.analytics.infrastructure.repositories.campaign_repository import (
    CampaignRepository,
)

logger = logging.getLogger(__name__)


class CampaignSyncPipeline:
    """Orchestrates full campaign hierarchy sync."""

    def __init__(
        self,
        provider: MetaCampaignProvider,
        repository: CampaignRepository,
    ):
        self._provider = provider
        self._repo = repository

    async def run_sync(
        self,
        tenant_id: UUID,
        credentials: dict,
    ) -> dict:
        """Extract and upsert full campaign hierarchy + recommendations.

        Returns summary dict with counts.
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            # 1. Campaigns
            campaigns = await self._provider.extract_campaigns(client, credentials)
            campaigns_count = await self._repo.upsert_campaigns(tenant_id, campaigns)

            # 2. Ad Sets + inline recommendations
            ad_sets, adset_recs = await self._provider.extract_ad_sets(
                client, credentials
            )
            adsets_count = await self._repo.upsert_ad_sets(tenant_id, ad_sets)

            # 3. Ads + inline recommendations
            ads, ad_recs = await self._provider.extract_ads(client, credentials)
            ads_count = await self._repo.upsert_ads(tenant_id, ads)

            # 4. Account-level recommendations
            account_recs = await self._provider.extract_account_recommendations(
                client,
                credentials,
            )

            # 5. Merge all recommendations and upsert
            all_recs = adset_recs + ad_recs + account_recs
            recs_count = await self._repo.upsert_recommendations(tenant_id, all_recs)

            # 6. Soft-delete entities that disappeared from the API
            campaign_ids = [c["external_id"] for c in campaigns]
            adset_ids = [a["external_id"] for a in ad_sets]
            ad_ids = [a["external_id"] for a in ads]

            stale_camps = await self._repo.soft_delete_stale(
                tenant_id,
                "meta",
                "ad_campaigns",
                campaign_ids,
            )
            stale_adsets = await self._repo.soft_delete_stale(
                tenant_id,
                "meta",
                "ad_sets",
                adset_ids,
            )
            stale_ads = await self._repo.soft_delete_stale(
                tenant_id,
                "meta",
                "ads",
                ad_ids,
            )

        summary = {
            "campaigns_synced": campaigns_count,
            "ad_sets_synced": adsets_count,
            "ads_synced": ads_count,
            "recommendations_synced": recs_count,
            "stale_deleted": stale_camps + stale_adsets + stale_ads,
        }
        logger.info("campaign_sync_complete tenant=%s summary=%s", tenant_id, summary)
        return summary
