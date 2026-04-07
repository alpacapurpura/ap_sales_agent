"""Tests for CampaignRepository — upsert and query operations."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.analytics.infrastructure.repositories.campaign_repository import (
    CampaignRepository,
)


class TestCampaignRepositoryUpsert:
    """Test upsert methods call session.execute with correct params."""

    @pytest.mark.asyncio
    async def test_upsert_campaigns_executes_sql(self):
        session = AsyncMock()
        repo = CampaignRepository(session)
        tenant_id = uuid4()
        campaigns = [
            {
                "external_id": "camp_001",
                "name": "Spring Sale",
                "objective": "OUTCOME_SALES",
                "status": "ACTIVE",
                "effective_status": "ACTIVE",
                "daily_budget": 5000,
            }
        ]
        count = await repo.upsert_campaigns(tenant_id, campaigns)
        assert count == 1
        session.execute.assert_called_once()
        call_args = session.execute.call_args
        params = call_args[0][1]
        assert params["external_id"] == "camp_001"
        assert params["tenant_id"] == str(tenant_id)

    @pytest.mark.asyncio
    async def test_upsert_ad_sets_executes_sql(self):
        session = AsyncMock()
        repo = CampaignRepository(session)
        tenant_id = uuid4()
        ad_sets = [
            {
                "external_id": "adset_001",
                "campaign_external_id": "camp_001",
                "name": "Women 25-34",
                "targeting": {"age_min": 25, "age_max": 34},
            }
        ]
        count = await repo.upsert_ad_sets(tenant_id, ad_sets)
        assert count == 1
        session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_ads_executes_sql(self):
        session = AsyncMock()
        repo = CampaignRepository(session)
        tenant_id = uuid4()
        ads = [
            {
                "external_id": "ad_001",
                "campaign_external_id": "camp_001",
                "ad_set_external_id": "adset_001",
                "name": "Ad Creative 1",
            }
        ]
        count = await repo.upsert_ads(tenant_id, ads)
        assert count == 1
        session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_recommendations_executes_sql(self):
        session = AsyncMock()
        repo = CampaignRepository(session)
        tenant_id = uuid4()
        recs = [
            {
                "recommendation_type": "CREATIVE_FATIGUE",
                "source": "account",
                "body": "Refresh your creative",
            }
        ]
        count = await repo.upsert_recommendations(tenant_id, recs)
        assert count == 1
        session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_upsert_multiple_campaigns(self):
        session = AsyncMock()
        repo = CampaignRepository(session)
        tenant_id = uuid4()
        campaigns = [
            {"external_id": "c1", "name": "Camp 1"},
            {"external_id": "c2", "name": "Camp 2"},
            {"external_id": "c3", "name": "Camp 3"},
        ]
        count = await repo.upsert_campaigns(tenant_id, campaigns)
        assert count == 3
        assert session.execute.call_count == 3


class TestCampaignRepositoryQueries:
    """Test query methods."""

    @pytest.mark.asyncio
    async def test_get_campaigns_filters_by_tenant(self):
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        session = AsyncMock()
        session.execute.return_value = mock_result
        repo = CampaignRepository(session)
        tenant_id = uuid4()
        result = await repo.get_campaigns(tenant_id)
        assert result == []
        call_args = session.execute.call_args
        params = call_args[0][1]
        assert params["tenant_id"] == str(tenant_id)

    @pytest.mark.asyncio
    async def test_soft_delete_stale_with_empty_ids_returns_zero(self):
        session = AsyncMock()
        repo = CampaignRepository(session)
        tenant_id = uuid4()
        result = await repo.soft_delete_stale(tenant_id, "meta", "ad_campaigns", [])
        assert result == 0
        session.execute.assert_not_called()
