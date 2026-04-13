"""Tests for ARQ task functions — credential handling and period extraction triggers."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.shared.domain.ports import ConnectionCredentials

# Patch targets match the actual source modules (late imports in tasks.py)
_CONN_PORT = "src.modules.connections.application.services.connection_port_impl.ConnectionPortImpl"
_PIPELINE = "src.modules.analytics.infrastructure.sync.campaign_sync_pipeline.CampaignSyncPipeline"
_PROVIDER = "src.modules.analytics.infrastructure.providers.meta_campaign_provider.MetaCampaignProvider"
_REPO = "src.modules.analytics.infrastructure.repositories.campaign_repository.CampaignRepository"


def _make_ctx():
    mock_db = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.close = MagicMock()
    return {"db_factory": lambda: mock_db}


def _make_pipeline_mock(result=None):
    m = MagicMock()
    m.run_sync = AsyncMock(
        return_value=result
        or {
            "campaigns_synced": 2,
            "ad_sets_synced": 3,
            "ads_synced": 5,
            "recommendations_synced": 1,
            "stale_deleted": 0,
        },
    )
    return m


class TestRunCampaignSyncTask:
    """Verify run_campaign_sync properly flattens ConnectionCredentials to dict."""

    @pytest.mark.asyncio
    async def test_credentials_are_flattened_before_pipeline(self):
        """The task must merge .credentials + .config into a flat dict
        before passing to CampaignSyncPipeline.run_sync().
        """
        tenant_id = uuid4()
        creds_obj = ConnectionCredentials(
            channel_type="meta",
            credentials={"access_token": "tok123"},
            config={"ad_account_id": "act_456"},
        )

        mock_pipeline = _make_pipeline_mock()

        with (
            patch(_CONN_PORT) as MockConnPort,
            patch(_PIPELINE) as MockPipelineCls,
            patch(_PROVIDER),
            patch(_REPO),
        ):
            MockConnPort.return_value.get_credentials = AsyncMock(
                return_value=creds_obj,
            )
            MockPipelineCls.return_value = mock_pipeline

            from src.modules.analytics.workers.tasks import run_campaign_sync

            result = await run_campaign_sync(_make_ctx(), str(tenant_id), "meta")

        # The pipeline must receive a flat dict, NOT a ConnectionCredentials object
        call_args = mock_pipeline.run_sync.call_args
        passed_creds = call_args[0][1]  # second positional arg
        assert isinstance(passed_creds, dict), f"Expected dict, got {type(passed_creds).__name__}"
        assert passed_creds["access_token"] == "tok123"
        assert passed_creds["ad_account_id"] == "act_456"
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_credentials_include_both_credentials_and_config(self):
        """Ensure all keys from both credentials and config dicts are present."""
        tenant_id = uuid4()
        creds_obj = ConnectionCredentials(
            channel_type="meta",
            credentials={
                "access_token": "tok",
                "app_secret": "secret",
            },
            config={
                "ad_account_id": "act_789",
                "page_id": "page_001",
            },
        )

        mock_pipeline = _make_pipeline_mock(
            {
                "campaigns_synced": 0,
                "ad_sets_synced": 0,
                "ads_synced": 0,
                "recommendations_synced": 0,
                "stale_deleted": 0,
            },
        )

        with (
            patch(_CONN_PORT) as MockConnPort,
            patch(_PIPELINE) as MockPipelineCls,
            patch(_PROVIDER),
            patch(_REPO),
        ):
            MockConnPort.return_value.get_credentials = AsyncMock(
                return_value=creds_obj,
            )
            MockPipelineCls.return_value = mock_pipeline

            from src.modules.analytics.workers.tasks import run_campaign_sync

            await run_campaign_sync(_make_ctx(), str(tenant_id), "meta")

        passed_creds = mock_pipeline.run_sync.call_args[0][1]
        assert passed_creds == {
            "access_token": "tok",
            "app_secret": "secret",
            "ad_account_id": "act_789",
            "page_id": "page_001",
        }


class TestMaybeEnqueuePeriodExtraction:
    """Verify _maybe_enqueue_period_extraction triggers when period_metrics is empty."""

    @pytest.mark.asyncio
    async def test_enqueues_when_period_metrics_empty(self):
        """When period_metrics count is 0, should enqueue monthly extraction."""
        tenant_id = str(uuid4())
        mock_redis = AsyncMock()
        mock_db = MagicMock()
        # Simulate count query returning 0
        mock_db.execute.return_value.scalar.return_value = 0

        ctx = {"redis": mock_redis}

        with patch(
            "src.modules.analytics.infrastructure.models.period_metrics_model.PeriodMetricModel",
        ):
            from src.modules.analytics.workers.tasks import (
                _maybe_enqueue_period_extraction,
            )

            await _maybe_enqueue_period_extraction(ctx, mock_db, tenant_id)

        # Should enqueue at least the monthly period extraction
        job_names = [c[0][0] for c in mock_redis.enqueue_job.call_args_list]
        assert "run_period_extraction" in job_names

    @pytest.mark.asyncio
    async def test_skips_when_period_metrics_exist(self):
        """When period_metrics has data, should not enqueue anything."""
        tenant_id = str(uuid4())
        mock_redis = AsyncMock()
        mock_db = MagicMock()
        # Simulate count query returning > 0
        mock_db.execute.return_value.scalar.return_value = 42

        ctx = {"redis": mock_redis}

        with patch(
            "src.modules.analytics.infrastructure.models.period_metrics_model.PeriodMetricModel",
        ):
            from src.modules.analytics.workers.tasks import (
                _maybe_enqueue_period_extraction,
            )

            await _maybe_enqueue_period_extraction(ctx, mock_db, tenant_id)

        mock_redis.enqueue_job.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_when_no_redis(self):
        """When redis is not in context, should return silently."""
        from src.modules.analytics.workers.tasks import (
            _maybe_enqueue_period_extraction,
        )

        mock_db = MagicMock()
        ctx = {}  # No redis

        await _maybe_enqueue_period_extraction(ctx, mock_db, str(uuid4()))

        mock_db.execute.assert_not_called()
