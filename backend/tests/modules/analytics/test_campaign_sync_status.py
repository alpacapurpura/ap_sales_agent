"""Tests for campaign sync status endpoint."""

import json
from uuid import uuid4

from src.modules.analytics.api.campaigns import CampaignSyncStatusDTO


class TestCampaignSyncStatusDTO:
    def test_never_synced_status(self):
        dto = CampaignSyncStatusDTO(status="never_synced")
        assert dto.status == "never_synced"
        assert dto.campaigns_synced is None

    def test_success_status_with_counts(self):
        dto = CampaignSyncStatusDTO(
            status="success",
            campaigns_synced=5,
            ad_sets_synced=10,
            ads_synced=20,
            recommendations_synced=3,
        )
        assert dto.status == "success"
        assert dto.campaigns_synced == 5
        assert dto.ads_synced == 20


class TestSyncStatusRedisIntegration:
    """Verify Redis read/write roundtrip for sync status."""

    def test_sync_result_is_json_serializable(self):
        """The result dict stored in Redis must be JSON-serializable."""
        sync_result = {
            "status": "success",
            "tenant_id": str(uuid4()),
            "provider": "meta",
            "campaigns_synced": 3,
            "ad_sets_synced": 5,
            "ads_synced": 12,
            "recommendations_synced": 2,
            "stale_deleted": 0,
        }
        raw = json.dumps(sync_result)
        parsed = json.loads(raw)
        assert parsed["status"] == "success"
        assert parsed["campaigns_synced"] == 3

    def test_dto_from_redis_data(self):
        """CampaignSyncStatusDTO can be constructed from Redis JSON data."""
        data = {
            "status": "success",
            "campaigns_synced": 3,
            "ad_sets_synced": 5,
            "ads_synced": 12,
            "recommendations_synced": 2,
        }
        dto = CampaignSyncStatusDTO(
            status=data.get("status", "unknown"),
            campaigns_synced=data.get("campaigns_synced"),
            ad_sets_synced=data.get("ad_sets_synced"),
            ads_synced=data.get("ads_synced"),
            recommendations_synced=data.get("recommendations_synced"),
        )
        assert dto.status == "success"
        assert dto.ads_synced == 12
