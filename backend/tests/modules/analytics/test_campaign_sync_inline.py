"""Tests for campaign sync inline execution (P2 fix).

Verifies that trigger_sync() runs synchronously by default,
falling back to ARQ only when inline execution fails.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.analytics.application.services.campaign_service import CampaignService


@pytest.fixture
def tenant_id():
    return uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def campaign_service():
    db = MagicMock()
    return CampaignService(db)


class TestTriggerSyncInline:
    """trigger_sync should prefer inline execution over ARQ."""

    @pytest.mark.asyncio
    async def test_inline_sync_called_first(self, campaign_service, tenant_id):
        """Inline sync should be attempted before ARQ enqueue."""
        campaign_service._sync_campaigns_inline = AsyncMock(
            return_value={"status": "success", "campaigns_synced": 5}
        )
        campaign_service._enqueue_campaign_sync_arq = AsyncMock()

        result = await campaign_service.trigger_sync(tenant_id)

        campaign_service._sync_campaigns_inline.assert_awaited_once_with(tenant_id)
        campaign_service._enqueue_campaign_sync_arq.assert_not_awaited()
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_falls_back_to_arq_on_failure(self, campaign_service, tenant_id):
        """When inline sync fails, should fall back to ARQ enqueue."""
        campaign_service._sync_campaigns_inline = AsyncMock(
            side_effect=Exception("connection error")
        )
        campaign_service._enqueue_campaign_sync_arq = AsyncMock(
            return_value={"status": "queued", "job_id": "abc123"}
        )

        result = await campaign_service.trigger_sync(tenant_id)

        campaign_service._sync_campaigns_inline.assert_awaited_once()
        campaign_service._enqueue_campaign_sync_arq.assert_awaited_once()
        assert result["status"] == "queued"
