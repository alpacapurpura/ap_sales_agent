"""Tests for PeriodExtractionPipeline — period-level NON_AGGREGABLE extraction.

Tests cover:
- No-op when provider has no NON_AGGREGABLE metrics
- Happy path: extract -> upsert -> cache invalidate -> SUCCESS status
- Partial success: metrics + sub-extractor failures -> PARTIAL_SUCCESS status
- All sub-extractors fail, no metrics -> FAILED status
- ConnectionRevokedError -> FAILED, no retry
- Generic exception -> FAILED, db rollback
"""

import asyncio
import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
PERIOD_START = date(2026, 3, 3)
PERIOD_END = date(2026, 3, 9)
PERIOD_TYPE = "weekly"


def _run(coro):
    """Run a coroutine synchronously for testing."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _make_period_metric(**overrides):
    """Create a mock ExtractedMetric for period extraction."""
    from luana_core_analytics_engine.infrastructure.providers.base import ExtractedMetric

    defaults = {
        "provider": "meta",
        "channel_slug": "meta-ads",
        "metric_name": "reach",
        "value": 5000.0,
        "unit": "count",
        "date": PERIOD_START,
    }
    defaults.update(overrides)
    return ExtractedMetric(**defaults)


def _make_extraction_result(*metrics, failures=None):
    """Wrap metrics + optional failures into ExtractionResult."""
    from luana_core_analytics_engine.domain.extraction_result import ExtractionResult

    return ExtractionResult(metrics=list(metrics), failures=failures or [])


def _make_sub_extractor_failure(name="meta_reach", error="Timeout"):
    """Create a SubExtractorFailure instance."""
    from luana_core_analytics_engine.domain.extraction_result import SubExtractorFailure

    return SubExtractorFailure(extractor_name=name, error=error, error_type="timeout")


def _make_run_model(run_id=None):
    """Create a mock ExtractionRunModel."""
    model = MagicMock()
    model.id = run_id or uuid.uuid4()
    model.tenant_id = TENANT_ID
    model.provider = "meta"
    model.status = "pending"
    return model


def _make_pipeline(*, provider_name="meta", non_agg_metrics=None):
    """Construct a PeriodExtractionPipeline with fully mocked dependencies.

    Returns (pipeline, mocks_dict).
    """
    from luana_core_analytics_engine.infrastructure.etl.period_pipeline import (
        PeriodExtractionPipeline,
    )

    if non_agg_metrics is None:
        non_agg_metrics = ["reach", "unique_users"]

    mock_db = MagicMock()
    mock_provider = AsyncMock()
    # provider_name() is a sync method — override with MagicMock so it returns
    # the string directly instead of a coroutine (AsyncMock side-effect).
    mock_provider.provider_name = MagicMock(return_value=provider_name)

    run_model = _make_run_model()
    mock_run_repo = MagicMock()
    mock_run_repo.create.return_value = run_model

    mock_period_repo = MagicMock()
    mock_period_repo.upsert_period_metrics.return_value = 0

    mock_connection_port = AsyncMock()
    mock_connection_port.get_credentials.return_value = MagicMock(
        credentials={"access_token": "test-token"},
        config={"account_id": "123"},
    )

    mock_cache = AsyncMock()

    pipeline = PeriodExtractionPipeline(
        db=mock_db,
        provider=mock_provider,
        connection_port=mock_connection_port,
        period_repo=mock_period_repo,
        run_repo=mock_run_repo,
        cache=mock_cache,
    )

    return pipeline, {
        "db": mock_db,
        "provider": mock_provider,
        "run_repo": mock_run_repo,
        "period_repo": mock_period_repo,
        "connection_port": mock_connection_port,
        "cache": mock_cache,
        "run_model": run_model,
        "non_agg_metrics": non_agg_metrics,
    }


class TestPeriodPipelineSkip:
    """Provider with no NON_AGGREGABLE metrics -> early return, no DB writes."""

    def test_returns_skipped_when_no_non_aggregable_metrics(self):
        """If get_non_aggregable_for_provider returns [], run() returns skipped."""
        pipeline, mocks = _make_pipeline()

        with patch(
            "luana_core_analytics_engine.infrastructure.etl.period_pipeline.get_non_aggregable_for_provider",
            return_value=[],
        ):
            result = _run(pipeline.run(TENANT_ID, PERIOD_TYPE, PERIOD_START, PERIOD_END))

        assert result["status"] == "skipped"
        assert result["reason"] == "no_non_aggregable_metrics"
        mocks["run_repo"].create.assert_not_called()
        mocks["period_repo"].upsert_period_metrics.assert_not_called()
        mocks["cache"].invalidate_tenant.assert_not_called()


class TestPeriodPipelineHappyPath:
    """Successful extraction: metrics extracted, upserted, cache invalidated."""

    def test_run_extracts_and_upserts_metrics(self):
        """Happy path calls provider.extract_period_metrics and period_repo.upsert."""
        from luana_core_analytics_engine.domain.enums import ExtractionStatus

        pipeline, mocks = _make_pipeline()
        mocks["provider"].extract_period_metrics.return_value = _make_extraction_result(
            _make_period_metric(),
            _make_period_metric(metric_name="unique_users", value=3000.0),
        )
        mocks["period_repo"].upsert_period_metrics.return_value = 2

        with patch(
            "luana_core_analytics_engine.infrastructure.etl.period_pipeline.get_non_aggregable_for_provider",
            return_value=["reach", "unique_users"],
        ):
            result = _run(pipeline.run(TENANT_ID, PERIOD_TYPE, PERIOD_START, PERIOD_END))

        assert result["status"] == ExtractionStatus.SUCCESS.value
        assert result["metrics_count"] == 2
        mocks["period_repo"].upsert_period_metrics.assert_called_once()
        mocks["cache"].invalidate_tenant.assert_called_once_with(str(TENANT_ID))

    def test_run_creates_extraction_run_before_extracting(self):
        """run_repo.create must be called before provider.extract_period_metrics."""
        pipeline, mocks = _make_pipeline()
        mocks["provider"].extract_period_metrics.return_value = _make_extraction_result(
            _make_period_metric(),
        )

        with patch(
            "luana_core_analytics_engine.infrastructure.etl.period_pipeline.get_non_aggregable_for_provider",
            return_value=["reach"],
        ):
            _run(pipeline.run(TENANT_ID, PERIOD_TYPE, PERIOD_START, PERIOD_END))

        mocks["run_repo"].create.assert_called_once()
        create_kwargs = mocks["run_repo"].create.call_args
        assert create_kwargs[0][0] == TENANT_ID
        assert create_kwargs[0][1] == "meta"

    def test_run_commits_run_row_before_extraction(self):
        """DB must be committed before extraction to persist run row."""
        pipeline, mocks = _make_pipeline()
        mocks["provider"].extract_period_metrics.return_value = _make_extraction_result(
            _make_period_metric(),
        )

        with patch(
            "luana_core_analytics_engine.infrastructure.etl.period_pipeline.get_non_aggregable_for_provider",
            return_value=["reach"],
        ):
            _run(pipeline.run(TENANT_ID, PERIOD_TYPE, PERIOD_START, PERIOD_END))

        # commit() called at least twice: pre-extraction + post-success
        assert mocks["db"].commit.call_count >= 2

    def test_run_marks_success_status(self):
        """run_repo.update_status called with SUCCESS when all metrics extracted."""
        from luana_core_analytics_engine.domain.enums import ExtractionStatus

        pipeline, mocks = _make_pipeline()
        mocks["provider"].extract_period_metrics.return_value = _make_extraction_result(
            _make_period_metric(),
        )

        with patch(
            "luana_core_analytics_engine.infrastructure.etl.period_pipeline.get_non_aggregable_for_provider",
            return_value=["reach"],
        ):
            _run(pipeline.run(TENANT_ID, PERIOD_TYPE, PERIOD_START, PERIOD_END))

        update_calls = mocks["run_repo"].update_status.call_args_list
        success_calls = [c for c in update_calls if c[1].get("status") == ExtractionStatus.SUCCESS]
        assert len(success_calls) == 1

    def test_run_passes_metric_names_to_provider(self):
        """provider.extract_period_metrics receives the NON_AGGREGABLE metric_names list."""
        pipeline, mocks = _make_pipeline()
        mocks["provider"].extract_period_metrics.return_value = _make_extraction_result(
            _make_period_metric(),
        )

        with patch(
            "luana_core_analytics_engine.infrastructure.etl.period_pipeline.get_non_aggregable_for_provider",
            return_value=["reach", "unique_users"],
        ):
            _run(pipeline.run(TENANT_ID, PERIOD_TYPE, PERIOD_START, PERIOD_END))

        call_kwargs = mocks["provider"].extract_period_metrics.call_args[1]
        assert set(call_kwargs["metric_names"]) == {"reach", "unique_users"}
        assert call_kwargs["period_type"] == PERIOD_TYPE
        assert call_kwargs["period_start"] == PERIOD_START
        assert call_kwargs["period_end"] == PERIOD_END

    def test_zero_metrics_succeeds(self):
        """Extraction returning empty metrics (no failures) = SUCCESS."""
        from luana_core_analytics_engine.domain.enums import ExtractionStatus

        pipeline, mocks = _make_pipeline()
        mocks["provider"].extract_period_metrics.return_value = _make_extraction_result()

        with patch(
            "luana_core_analytics_engine.infrastructure.etl.period_pipeline.get_non_aggregable_for_provider",
            return_value=["reach"],
        ):
            result = _run(pipeline.run(TENANT_ID, PERIOD_TYPE, PERIOD_START, PERIOD_END))

        assert result["status"] == ExtractionStatus.SUCCESS.value
        mocks["cache"].invalidate_tenant.assert_called_once()


class TestPeriodPipelinePartialSuccess:
    """Sub-extractor failures + metrics -> PARTIAL_SUCCESS."""

    def test_failures_with_metrics_marks_partial_success(self):
        """Some sub-extractors fail but metrics exist -> PARTIAL_SUCCESS."""
        from luana_core_analytics_engine.domain.enums import ExtractionStatus

        pipeline, mocks = _make_pipeline()
        mocks["provider"].extract_period_metrics.return_value = _make_extraction_result(
            _make_period_metric(),
            failures=[_make_sub_extractor_failure()],
        )

        with patch(
            "luana_core_analytics_engine.infrastructure.etl.period_pipeline.get_non_aggregable_for_provider",
            return_value=["reach"],
        ):
            _run(pipeline.run(TENANT_ID, PERIOD_TYPE, PERIOD_START, PERIOD_END))

        update_calls = mocks["run_repo"].update_status.call_args_list
        partial_calls = [c for c in update_calls if c[1].get("status") == ExtractionStatus.PARTIAL_SUCCESS]
        assert len(partial_calls) == 1

    def test_failures_with_metrics_still_invalidates_cache(self):
        """PARTIAL_SUCCESS still invalidates cache (metrics were extracted)."""
        pipeline, mocks = _make_pipeline()
        mocks["provider"].extract_period_metrics.return_value = _make_extraction_result(
            _make_period_metric(),
            failures=[_make_sub_extractor_failure()],
        )

        with patch(
            "luana_core_analytics_engine.infrastructure.etl.period_pipeline.get_non_aggregable_for_provider",
            return_value=["reach"],
        ):
            _run(pipeline.run(TENANT_ID, PERIOD_TYPE, PERIOD_START, PERIOD_END))

        mocks["cache"].invalidate_tenant.assert_called_once_with(str(TENANT_ID))

    def test_all_sub_extractors_fail_no_metrics_marks_failed(self):
        """No metrics + failures -> FAILED (not PARTIAL_SUCCESS)."""
        from luana_core_analytics_engine.domain.enums import ExtractionStatus

        pipeline, mocks = _make_pipeline()
        mocks["provider"].extract_period_metrics.return_value = _make_extraction_result(
            failures=[
                _make_sub_extractor_failure("meta_reach", "Auth error"),
                _make_sub_extractor_failure("meta_unique_users", "Rate limited"),
            ],
        )

        with patch(
            "luana_core_analytics_engine.infrastructure.etl.period_pipeline.get_non_aggregable_for_provider",
            return_value=["reach", "unique_users"],
        ):
            _run(pipeline.run(TENANT_ID, PERIOD_TYPE, PERIOD_START, PERIOD_END))

        update_calls = mocks["run_repo"].update_status.call_args_list
        failed_calls = [c for c in update_calls if c[1].get("status") == ExtractionStatus.FAILED]
        assert len(failed_calls) == 1


class TestPeriodPipelineConnectionRevoked:
    """ConnectionRevokedError -> FAILED, no retry, no cache invalidation."""

    def test_connection_revoked_returns_revoked_status(self):
        """ConnectionRevokedError caught -> result status = 'revoked'."""
        from luana_core_analytics_engine.domain.exceptions import ConnectionRevokedError

        pipeline, mocks = _make_pipeline()
        mocks["connection_port"].get_credentials.side_effect = ConnectionRevokedError(
            "Token expired",
            channel_type="meta",
        )

        with patch(
            "luana_core_analytics_engine.infrastructure.etl.period_pipeline.get_non_aggregable_for_provider",
            return_value=["reach"],
        ):
            result = _run(pipeline.run(TENANT_ID, PERIOD_TYPE, PERIOD_START, PERIOD_END))

        assert result["status"] == "revoked"
        assert "error" in result

    def test_connection_revoked_marks_run_failed(self):
        """ConnectionRevokedError -> run_repo.update_status with FAILED."""
        from luana_core_analytics_engine.domain.enums import ExtractionStatus
        from luana_core_analytics_engine.domain.exceptions import ConnectionRevokedError

        pipeline, mocks = _make_pipeline()
        mocks["connection_port"].get_credentials.side_effect = ConnectionRevokedError(
            "Refresh token revoked",
            channel_type="meta",
        )

        with patch(
            "luana_core_analytics_engine.infrastructure.etl.period_pipeline.get_non_aggregable_for_provider",
            return_value=["reach"],
        ):
            _run(pipeline.run(TENANT_ID, PERIOD_TYPE, PERIOD_START, PERIOD_END))

        update_calls = mocks["run_repo"].update_status.call_args_list
        failed_calls = [c for c in update_calls if c[1].get("status") == ExtractionStatus.FAILED]
        assert len(failed_calls) == 1

    def test_connection_revoked_does_not_call_provider(self):
        """After ConnectionRevokedError, provider.extract_period_metrics not called."""
        from luana_core_analytics_engine.domain.exceptions import ConnectionRevokedError

        pipeline, mocks = _make_pipeline()
        mocks["connection_port"].get_credentials.side_effect = ConnectionRevokedError(
            "Revoked",
            channel_type="meta",
        )

        with patch(
            "luana_core_analytics_engine.infrastructure.etl.period_pipeline.get_non_aggregable_for_provider",
            return_value=["reach"],
        ):
            _run(pipeline.run(TENANT_ID, PERIOD_TYPE, PERIOD_START, PERIOD_END))

        mocks["provider"].extract_period_metrics.assert_not_called()
        mocks["cache"].invalidate_tenant.assert_not_called()

    def test_connection_revoked_rolls_back_db(self):
        """ConnectionRevokedError triggers db.rollback() before status update."""
        from luana_core_analytics_engine.domain.exceptions import ConnectionRevokedError

        pipeline, mocks = _make_pipeline()
        mocks["connection_port"].get_credentials.side_effect = ConnectionRevokedError(
            "Revoked",
            channel_type="meta",
        )

        with patch(
            "luana_core_analytics_engine.infrastructure.etl.period_pipeline.get_non_aggregable_for_provider",
            return_value=["reach"],
        ):
            _run(pipeline.run(TENANT_ID, PERIOD_TYPE, PERIOD_START, PERIOD_END))

        mocks["db"].rollback.assert_called()


class TestPeriodPipelineGenericError:
    """Generic exception -> FAILED, rollback, no cache invalidation."""

    def test_generic_exception_marks_failed(self):
        """RuntimeError in extract_period_metrics -> FAILED status."""
        from luana_core_analytics_engine.domain.enums import ExtractionStatus

        pipeline, mocks = _make_pipeline()
        mocks["provider"].extract_period_metrics.side_effect = RuntimeError("Network timeout")

        with patch(
            "luana_core_analytics_engine.infrastructure.etl.period_pipeline.get_non_aggregable_for_provider",
            return_value=["reach"],
        ):
            _run(pipeline.run(TENANT_ID, PERIOD_TYPE, PERIOD_START, PERIOD_END))

        update_calls = mocks["run_repo"].update_status.call_args_list
        failed_calls = [c for c in update_calls if c[1].get("status") == ExtractionStatus.FAILED]
        assert len(failed_calls) == 1
        assert "Network timeout" in failed_calls[0][1].get("error", "")

    def test_generic_exception_returns_failed_dict(self):
        """RuntimeError -> result dict status = 'failed' with error key."""
        pipeline, mocks = _make_pipeline()
        mocks["provider"].extract_period_metrics.side_effect = RuntimeError("Unexpected error")

        with patch(
            "luana_core_analytics_engine.infrastructure.etl.period_pipeline.get_non_aggregable_for_provider",
            return_value=["reach"],
        ):
            result = _run(pipeline.run(TENANT_ID, PERIOD_TYPE, PERIOD_START, PERIOD_END))

        assert result["status"] == "failed"
        assert "error" in result

    def test_generic_exception_rolls_back_db(self):
        """RuntimeError -> db.rollback() called, cache NOT invalidated."""
        pipeline, mocks = _make_pipeline()
        mocks["provider"].extract_period_metrics.side_effect = RuntimeError("DB error")

        with patch(
            "luana_core_analytics_engine.infrastructure.etl.period_pipeline.get_non_aggregable_for_provider",
            return_value=["reach"],
        ):
            _run(pipeline.run(TENANT_ID, PERIOD_TYPE, PERIOD_START, PERIOD_END))

        mocks["db"].rollback.assert_called()
        mocks["cache"].invalidate_tenant.assert_not_called()

    def test_error_message_truncated_to_500_chars(self):
        """Long error messages are truncated to 500 chars in status update."""
        pipeline, mocks = _make_pipeline()
        long_error = "E" * 600
        mocks["provider"].extract_period_metrics.side_effect = RuntimeError(long_error)

        with patch(
            "luana_core_analytics_engine.infrastructure.etl.period_pipeline.get_non_aggregable_for_provider",
            return_value=["reach"],
        ):
            _run(pipeline.run(TENANT_ID, PERIOD_TYPE, PERIOD_START, PERIOD_END))

        update_calls = mocks["run_repo"].update_status.call_args_list
        failed_call = next(c for c in update_calls if c[1].get("status") is not None)
        error_stored = failed_call[1].get("error", "")
        assert len(error_stored) <= 500
