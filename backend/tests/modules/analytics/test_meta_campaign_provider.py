"""Tests for MetaCampaignProvider — campaign hierarchy extraction from Meta API."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.modules.analytics.infrastructure.providers.meta_campaign_provider import (
    MetaCampaignProvider,
)

TENANT_ID = uuid4()
CREDS = {
    "access_token": "test_token",
    "ad_account_id": "111222",
    "currency": "MXN",
}


def _ok_response(json_data: dict) -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


class TestExtractCampaigns:
    @pytest.mark.asyncio
    async def test_extracts_campaigns_with_all_fields(self):
        mock_resp = _ok_response({
            "data": [
                {
                    "id": "camp_001",
                    "name": "Spring Sale",
                    "objective": "OUTCOME_SALES",
                    "status": "ACTIVE",
                    "effective_status": "ACTIVE",
                    "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
                    "daily_budget": "5000",
                    "budget_remaining": "3200",
                    "buying_type": "AUCTION",
                    "special_ad_categories": [],
                    "start_time": "2026-03-01T00:00:00-0500",
                    "created_time": "2026-02-28T10:00:00-0500",
                    "updated_time": "2026-03-15T14:00:00-0500",
                },
            ],
            "paging": {},
        })

        async def mock_get(url, **kwargs):
            return mock_resp

        provider = MetaCampaignProvider()
        client = AsyncMock()
        client.get = AsyncMock(side_effect=mock_get)

        result = await provider.extract_campaigns(client, CREDS)

        assert len(result) == 1
        camp = result[0]
        assert camp["external_id"] == "camp_001"
        assert camp["name"] == "Spring Sale"
        assert camp["objective"] == "OUTCOME_SALES"
        assert camp["daily_budget"] == 5000

    @pytest.mark.asyncio
    async def test_no_ad_account_returns_empty(self):
        provider = MetaCampaignProvider()
        client = AsyncMock()
        result = await provider.extract_campaigns(client, {"access_token": "tok"})
        assert result == []


class TestExtractAdSets:
    @pytest.mark.asyncio
    async def test_extracts_ad_sets_with_targeting(self):
        mock_resp = _ok_response({
            "data": [
                {
                    "id": "adset_001",
                    "campaign_id": "camp_001",
                    "name": "Mujeres 25-34 CDMX",
                    "status": "ACTIVE",
                    "effective_status": "ACTIVE",
                    "optimization_goal": "CONVERSIONS",
                    "billing_event": "IMPRESSIONS",
                    "daily_budget": "2000",
                    "targeting": {
                        "age_min": 25,
                        "age_max": 34,
                        "genders": [2],
                        "geo_locations": {"cities": [{"key": "2673660"}]},
                        "interests": [{"id": "123", "name": "Yoga"}],
                    },
                    "destination_type": "WEBSITE",
                    "learning_stage_info": {"status": "SUCCESS"},
                    "recommendations": [
                        {
                            "title": "Expand Audience",
                            "message": "Your audience is too narrow",
                            "code": 1942008,
                            "importance": "HIGH",
                            "confidence": "HIGH",
                            "blame_field": "targeting",
                        }
                    ],
                },
            ],
            "paging": {},
        })

        async def mock_get(url, **kwargs):
            return mock_resp

        provider = MetaCampaignProvider()
        client = AsyncMock()
        client.get = AsyncMock(side_effect=mock_get)

        ad_sets, inline_recs = await provider.extract_ad_sets(client, CREDS)

        assert len(ad_sets) == 1
        adset = ad_sets[0]
        assert adset["external_id"] == "adset_001"
        assert adset["targeting"]["age_min"] == 25
        assert adset["learning_stage"] == "SUCCESS"

        # Inline recommendation extracted
        assert len(inline_recs) == 1
        assert inline_recs[0]["recommendation_type"] == "1942008"
        assert inline_recs[0]["source"] == "ad_set"


class TestExtractRecommendations:
    @pytest.mark.asyncio
    async def test_extracts_account_recommendations(self):
        mock_resp = _ok_response({
            "data": [
                {
                    "recommendation_data": {
                        "recommendation_signature": "sig_abc123",
                        "type": "CREATIVE_FATIGUE",
                        "object_ids": ["camp_001"],
                        "recommendation_content": {
                            "body": "Your creative has been shown too many times",
                            "lift_estimate": "+15% CTR",
                            "opportunity_score_lift": 8.5,
                        },
                        "url": "https://business.facebook.com/adsmanager/...",
                    },
                },
            ],
            "paging": {},
        })

        async def mock_get(url, **kwargs):
            return mock_resp

        provider = MetaCampaignProvider()
        client = AsyncMock()
        client.get = AsyncMock(side_effect=mock_get)

        recs = await provider.extract_account_recommendations(client, CREDS)

        assert len(recs) == 1
        rec = recs[0]
        assert rec["recommendation_type"] == "CREATIVE_FATIGUE"
        assert rec["source"] == "account"
        assert rec["opportunity_score"] == 8.5
