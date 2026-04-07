"""Tests for CampaignSyncPipeline — orchestrates full campaign sync."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.analytics.infrastructure.sync.campaign_sync_pipeline import (
    CampaignSyncPipeline,
)


class TestCampaignSyncPipeline:
    @pytest.mark.asyncio
    async def test_run_sync_calls_all_extractors_and_upserts(self):
        mock_provider = MagicMock()
        mock_provider.extract_campaigns = AsyncMock(
            return_value=[
                {"external_id": "c1", "name": "Camp 1"},
            ]
        )
        mock_provider.extract_ad_sets = AsyncMock(
            return_value=(
                [
                    {
                        "external_id": "as1",
                        "campaign_external_id": "c1",
                        "name": "AdSet 1",
                    }
                ],
                [{"source": "ad_set", "recommendation_type": "1942008", "body": "tip"}],
            )
        )
        mock_provider.extract_ads = AsyncMock(
            return_value=(
                [
                    {
                        "external_id": "ad1",
                        "campaign_external_id": "c1",
                        "ad_set_external_id": "as1",
                        "name": "Ad 1",
                    }
                ],
                [],
            )
        )
        mock_provider.extract_account_recommendations = AsyncMock(
            return_value=[
                {
                    "source": "account",
                    "recommendation_type": "CREATIVE_FATIGUE",
                    "body": "Refresh creative",
                },
            ]
        )

        mock_repo = MagicMock()
        mock_repo.upsert_campaigns = AsyncMock(return_value=1)
        mock_repo.upsert_ad_sets = AsyncMock(return_value=1)
        mock_repo.upsert_ads = AsyncMock(return_value=1)
        mock_repo.upsert_recommendations = AsyncMock(return_value=2)
        mock_repo.soft_delete_stale = AsyncMock(return_value=0)

        tenant_id = uuid4()
        creds = {"access_token": "tok", "ad_account_id": "123"}

        pipeline = CampaignSyncPipeline(
            provider=mock_provider,
            repository=mock_repo,
        )
        result = await pipeline.run_sync(tenant_id, creds)

        assert result["campaigns_synced"] == 1
        assert result["ad_sets_synced"] == 1
        assert result["ads_synced"] == 1
        assert result["recommendations_synced"] == 2
        mock_repo.upsert_campaigns.assert_called_once()
        mock_repo.upsert_ad_sets.assert_called_once()
        mock_repo.upsert_ads.assert_called_once()
