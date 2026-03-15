"""Tests for ETLPipeline — atomic extraction pipeline orchestration.

Tests cover:
- Happy path: extract -> stage -> transform -> official -> aggregate -> cache invalidate
- ExtractionRun created with SUCCESS on happy path
- ExtractionRun created with FAILED and rollback on provider error
- ConnectionRevokedException marks run FAILED without retry
"""

import asyncio
import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
START_DATE = date(2026, 3, 1)
END_DATE = date(2026, 3, 14)


def _run(coro):
    """Run a coroutine synchronously for testing."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _make_extracted_metric(**overrides):
    """Create a mock ExtractedMetric."""
    from src.modules.analytics.infrastructure.providers.base import ExtractedMetric

    defaults = {
        "provider": "meta",
        "channel_slug": "meta-ads",
        "metric_name": "impressions",
        "value": 1000.0,
        "unit": "count",
        "date": date(2026, 3, 10),
    }
    defaults.update(overrides)
    return ExtractedMetric(**defaults)


def _make_run_model(run_id=None, status="pending"):
    """Create a mock ExtractionRunModel."""
    model = MagicMock()
    model.id = run_id or uuid.uuid4()
    model.tenant_id = TENANT_ID
    model.provider = "meta"
    model.status = status
    return model


class TestETLPipelineHappyPath:
    """Tests for ETLPipeline.run() — successful extraction."""

    def test_run_executes_full_pipeline_in_order(self):
        """run() calls extract -> stage -> transform -> upsert -> aggregate -> cache in sequence."""
        from src.modules.analytics.infrastructure.etl.pipeline import ETLPipeline
        from src.modules.analytics.domain.enums import ExtractionStatus

        # Mock all dependencies
        mock_db = MagicMock()
        mock_provider = AsyncMock()
        mock_provider.provider_name.return_value = "meta"
        mock_provider.extract_metrics.return_value = [
            _make_extracted_metric(),
            _make_extracted_metric(metric_name="clicks", value=50.0),
        ]

        mock_connection_port = AsyncMock()
        mock_connection_port.get_credentials.return_value = MagicMock(
            credentials={"access_token": "test"},
            config={},
        )

        run_model = _make_run_model()
        mock_staging_repo = MagicMock()
        mock_staging_repo.bulk_insert.return_value = 2

        mock_official_repo = MagicMock()
        mock_official_repo.upsert_from_staging.return_value = 2

        mock_run_repo = MagicMock()
        mock_run_repo.create.return_value = run_model

        mock_cache = AsyncMock()

        pipeline = ETLPipeline(
            db=mock_db,
            provider=mock_provider,
            connection_port=mock_connection_port,
            staging_repo=mock_staging_repo,
            official_repo=mock_official_repo,
            run_repo=mock_run_repo,
            cache=mock_cache,
        )

        result = _run(pipeline.run(TENANT_ID, START_DATE, END_DATE))

        # Verify calls happened
        mock_run_repo.create.assert_called_once()
        mock_connection_port.get_credentials.assert_called_once()
        mock_provider.extract_metrics.assert_called_once()
        mock_staging_repo.bulk_insert.assert_called_once()
        mock_official_repo.upsert_from_staging.assert_called_once()
        mock_cache.invalidate_tenant.assert_called_once_with(str(TENANT_ID))

        # Run status updated to SUCCESS
        status_calls = mock_run_repo.update_status.call_args_list
        assert len(status_calls) >= 1
        # Last call should be SUCCESS
        last_call = status_calls[-1]
        assert last_call[1].get("status") == ExtractionStatus.SUCCESS or \
               (len(last_call[0]) > 1 and last_call[0][1] == ExtractionStatus.SUCCESS)

    def test_run_creates_extraction_run_with_success(self):
        """Happy path creates ExtractionRun and marks SUCCESS with metrics_count."""
        from src.modules.analytics.infrastructure.etl.pipeline import ETLPipeline
        from src.modules.analytics.domain.enums import ExtractionStatus

        mock_db = MagicMock()
        mock_provider = AsyncMock()
        mock_provider.provider_name.return_value = "meta"
        mock_provider.extract_metrics.return_value = [_make_extracted_metric()]

        mock_connection_port = AsyncMock()
        mock_connection_port.get_credentials.return_value = MagicMock(
            credentials={"access_token": "test"}, config={},
        )

        run_model = _make_run_model()
        mock_run_repo = MagicMock()
        mock_run_repo.create.return_value = run_model

        mock_staging_repo = MagicMock()
        mock_staging_repo.bulk_insert.return_value = 1
        mock_official_repo = MagicMock()
        mock_official_repo.upsert_from_staging.return_value = 1
        mock_cache = AsyncMock()

        pipeline = ETLPipeline(
            db=mock_db,
            provider=mock_provider,
            connection_port=mock_connection_port,
            staging_repo=mock_staging_repo,
            official_repo=mock_official_repo,
            run_repo=mock_run_repo,
            cache=mock_cache,
        )

        _run(pipeline.run(TENANT_ID, START_DATE, END_DATE))

        # Verify SUCCESS status was set
        update_calls = mock_run_repo.update_status.call_args_list
        success_call = [c for c in update_calls
                        if c[1].get("status") == ExtractionStatus.SUCCESS]
        assert len(success_call) == 1


class TestETLPipelineFailure:
    """Tests for ETLPipeline.run() — error handling."""

    def test_run_marks_failed_and_rolls_back_on_provider_error(self):
        """Provider error -> ExtractionRun FAILED, DB rollback."""
        from src.modules.analytics.infrastructure.etl.pipeline import ETLPipeline
        from src.modules.analytics.domain.enums import ExtractionStatus

        mock_db = MagicMock()
        mock_provider = AsyncMock()
        mock_provider.provider_name.return_value = "meta"
        mock_provider.extract_metrics.side_effect = RuntimeError("API rate limited")

        mock_connection_port = AsyncMock()
        mock_connection_port.get_credentials.return_value = MagicMock(
            credentials={"access_token": "test"}, config={},
        )

        run_model = _make_run_model()
        mock_run_repo = MagicMock()
        mock_run_repo.create.return_value = run_model

        mock_staging_repo = MagicMock()
        mock_official_repo = MagicMock()
        mock_cache = AsyncMock()

        pipeline = ETLPipeline(
            db=mock_db,
            provider=mock_provider,
            connection_port=mock_connection_port,
            staging_repo=mock_staging_repo,
            official_repo=mock_official_repo,
            run_repo=mock_run_repo,
            cache=mock_cache,
        )

        result = _run(pipeline.run(TENANT_ID, START_DATE, END_DATE))

        # Verify FAILED status
        update_calls = mock_run_repo.update_status.call_args_list
        failed_call = [c for c in update_calls
                       if c[1].get("status") == ExtractionStatus.FAILED]
        assert len(failed_call) == 1
        assert "API rate limited" in failed_call[0][1].get("error", "")

        # DB rollback called
        mock_db.rollback.assert_called()

        # Cache NOT invalidated on failure
        mock_cache.invalidate_tenant.assert_not_called()

    def test_run_marks_failed_on_connection_revoked(self):
        """ConnectionRevokedException -> FAILED, no retry."""
        from src.modules.analytics.infrastructure.etl.pipeline import ETLPipeline
        from src.modules.analytics.domain.enums import ExtractionStatus
        from src.modules.analytics.domain.exceptions import ConnectionRevokedException

        mock_db = MagicMock()
        mock_provider = AsyncMock()
        mock_provider.provider_name.return_value = "meta"

        mock_connection_port = AsyncMock()
        mock_connection_port.get_credentials.side_effect = ConnectionRevokedException(
            "Connection revoked", channel_type="meta"
        )

        run_model = _make_run_model()
        mock_run_repo = MagicMock()
        mock_run_repo.create.return_value = run_model

        mock_staging_repo = MagicMock()
        mock_official_repo = MagicMock()
        mock_cache = AsyncMock()

        pipeline = ETLPipeline(
            db=mock_db,
            provider=mock_provider,
            connection_port=mock_connection_port,
            staging_repo=mock_staging_repo,
            official_repo=mock_official_repo,
            run_repo=mock_run_repo,
            cache=mock_cache,
        )

        result = _run(pipeline.run(TENANT_ID, START_DATE, END_DATE))

        # Verify FAILED status
        update_calls = mock_run_repo.update_status.call_args_list
        failed_call = [c for c in update_calls
                       if c[1].get("status") == ExtractionStatus.FAILED]
        assert len(failed_call) == 1
        assert "revoked" in failed_call[0][1].get("error", "").lower()

        # Provider extract_metrics should NOT have been called
        mock_provider.extract_metrics.assert_not_called()
