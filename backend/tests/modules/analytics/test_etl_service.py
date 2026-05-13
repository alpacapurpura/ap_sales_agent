"""Tests for ETLService — multi-stage provider extraction, initial load, period extraction.

Covers:
- run_extraction: multi-stage iteration (mailerlite/shopify), default stage
- run_all_providers: unregistered provider skip, generic exception continue
- _get_period_config: tenant not found (default), tenant found (from DB)
- run_period_extraction: empty connections, skip no-period-support, skip already-extracted, happy path
- _sync_ig_dm: delegates to InstagramDMSyncService
- _try_period_extraction: no-op when provider lacks period support, happy path, exception silenced
- _stage_transform_upsert_aggregate: stage → transform → upsert → aggregate
- run_initial_load: all-days-already-loaded, missing days happy path, zero extracted
- _parse_shopify_datetime: valid ISO, empty string, invalid format
- run_sync_all: no providers, cooldown skip, provider exception
"""

import asyncio
import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _make_run_model(run_id=None):
    model = MagicMock()
    model.id = run_id or uuid.uuid4()
    return model


def _make_extraction_result(*metrics):
    from luana_core_analytics_engine.domain.extraction_result import ExtractionResult

    return ExtractionResult(metrics=list(metrics))


def _make_extracted_metric(**overrides):
    from luana_core_analytics_engine.infrastructure.providers.base import ExtractedMetric

    defaults = {
        "provider": "mailerlite",
        "channel_slug": "email-capture",
        "metric_name": "active_subscribers",
        "value": 100.0,
        "unit": "count",
        "date": date(2026, 4, 1),
    }
    defaults.update(overrides)
    return ExtractedMetric(**defaults)


class TestETLServiceMultiStageExtraction:
    """run_extraction must iterate all stages in PROVIDER_STAGES."""

    @patch(
        "luana_core_analytics_engine.application.services.etl_service.get_provider",
    )
    def test_run_extraction_iterates_provider_stages_for_mailerlite(
        self,
        mock_get_provider,
    ):
        """Mailerlite extraction must call pipeline.run for BOTH capture and nurture."""
        from luana_core_analytics_engine.application.services.etl_service import ETLService

        mock_provider = AsyncMock()
        mock_provider.provider_name.return_value = "mailerlite"
        mock_provider.extract_metrics.return_value = _make_extraction_result(
            _make_extracted_metric(),
        )
        mock_get_provider.return_value = mock_provider

        mock_db = MagicMock()
        mock_connection_port = AsyncMock()
        mock_connection_port.get_credentials.return_value = MagicMock(
            credentials={"api_key": "test_key"},
            config={},
        )
        mock_cache = AsyncMock()

        etl_service = ETLService(
            db=mock_db,
            connection_port=mock_connection_port,
            cache=mock_cache,
        )

        # Mock _get_period_config to avoid DB call
        etl_service._get_period_config = MagicMock()

        _run(etl_service.run_extraction(TENANT_ID, "mailerlite"))

        # Provider must have been called with BOTH stages
        extract_calls = mock_provider.extract_metrics.call_args_list
        stages_called = [call.kwargs.get("stage") for call in extract_calls]

        assert "capture" in stages_called, f"Expected 'capture' stage but got: {stages_called}"
        assert "nurture" in stages_called, f"Expected 'nurture' stage but got: {stages_called}"

    @patch(
        "luana_core_analytics_engine.application.services.etl_service.get_provider",
    )
    def test_run_extraction_uses_default_stage_for_unlisted_provider(
        self,
        mock_get_provider,
    ):
        """Providers NOT in PROVIDER_STAGES use the default stage (attraction)."""
        from luana_core_analytics_engine.application.services.etl_service import ETLService

        mock_provider = AsyncMock()
        mock_provider.provider_name.return_value = "meta"
        mock_provider.extract_metrics.return_value = _make_extraction_result(
            _make_extracted_metric(provider="meta", channel_slug="meta-ads"),
        )
        mock_get_provider.return_value = mock_provider

        mock_db = MagicMock()
        mock_connection_port = AsyncMock()
        mock_connection_port.get_credentials.return_value = MagicMock(
            credentials={"access_token": "test"},
            config={},
        )
        mock_cache = AsyncMock()

        etl_service = ETLService(
            db=mock_db,
            connection_port=mock_connection_port,
            cache=mock_cache,
        )
        etl_service._get_period_config = MagicMock()

        _run(etl_service.run_extraction(TENANT_ID, "meta"))

        # Only one call with default stage
        extract_calls = mock_provider.extract_metrics.call_args_list
        assert len(extract_calls) == 1
        assert extract_calls[0].kwargs.get("stage") == "attraction"

    @patch(
        "luana_core_analytics_engine.application.services.etl_service.get_provider",
    )
    def test_run_all_providers_extracts_all_stages_for_mailerlite(
        self,
        mock_get_provider,
    ):
        """run_all_providers must extract all stages for multi-stage providers."""
        from luana_core_analytics_engine.application.services.etl_service import ETLService

        mock_provider = AsyncMock()
        mock_provider.provider_name.return_value = "mailerlite"
        mock_provider.extract_metrics.return_value = _make_extraction_result(
            _make_extracted_metric(),
        )
        mock_get_provider.return_value = mock_provider

        mock_db = MagicMock()
        mock_connection = MagicMock()
        mock_connection.channel_type = "mailerlite"

        mock_connection_port = AsyncMock()
        mock_connection_port.list_active_connections.return_value = [mock_connection]
        mock_connection_port.get_credentials.return_value = MagicMock(
            credentials={"api_key": "test_key"},
            config={},
        )
        mock_cache = AsyncMock()

        etl_service = ETLService(
            db=mock_db,
            connection_port=mock_connection_port,
            cache=mock_cache,
        )
        etl_service._get_period_config = MagicMock()

        _run(etl_service.run_all_providers(TENANT_ID))

        # Provider must have been called with both capture and nurture
        extract_calls = mock_provider.extract_metrics.call_args_list
        stages_called = [call.kwargs.get("stage") for call in extract_calls]

        assert "capture" in stages_called, f"Expected 'capture' in stages but got: {stages_called}"
        assert "nurture" in stages_called, f"Expected 'nurture' in stages but got: {stages_called}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_service(*, connection_port=None, cache=None, db=None):
    """Construct ETLService with mocked dependencies."""
    from luana_core_analytics_engine.application.services.etl_service import ETLService

    _db = db or MagicMock()
    _port = connection_port or AsyncMock()
    _cache = cache or AsyncMock()
    svc = ETLService(db=_db, connection_port=_port, cache=_cache)
    svc._get_period_config = MagicMock()
    return svc, _db, _port, _cache


def _make_connection(channel_type="meta"):
    m = MagicMock()
    m.channel_type = channel_type
    return m


def _make_period_extraction_result(metrics=None):
    from luana_core_analytics_engine.domain.extraction_result import ExtractionResult

    return ExtractionResult(metrics=metrics or [])


# ---------------------------------------------------------------------------
# _get_period_config
# ---------------------------------------------------------------------------


class TestETLServiceGetPeriodConfig:
    """_get_period_config builds TenantPeriodConfig from DB."""

    def test_returns_default_config_when_tenant_not_found(self):
        """When tenant row missing, returns TenantPeriodConfig with defaults."""
        from luana_core_analytics_engine.application.services.etl_service import ETLService
        from luana_core_analytics_engine.domain.period_config import TenantPeriodConfig

        mock_db = MagicMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        svc = ETLService(db=mock_db, connection_port=AsyncMock(), cache=AsyncMock())

        config = svc._get_period_config(TENANT_ID)

        assert isinstance(config, TenantPeriodConfig)
        assert config.weekly_start_day == 0

    def test_returns_tenant_config_from_db(self):
        """When tenant exists, maps weekly_start_day/fiscal columns."""
        from luana_core_analytics_engine.application.services.etl_service import ETLService
        from luana_core_analytics_engine.domain.period_config import TenantPeriodConfig

        mock_tenant = MagicMock()
        mock_tenant.weekly_start_day = 1
        mock_tenant.fiscal_year_start_month = 4
        mock_tenant.fiscal_year_start_day = 1

        mock_db = MagicMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_tenant
        svc = ETLService(db=mock_db, connection_port=AsyncMock(), cache=AsyncMock())

        config = svc._get_period_config(TENANT_ID)

        assert isinstance(config, TenantPeriodConfig)
        assert config.weekly_start_day == 1
        assert config.fiscal_year_start_month == 4


# ---------------------------------------------------------------------------
# run_all_providers error paths
# ---------------------------------------------------------------------------


class TestETLServiceRunAllProvidersErrors:
    """run_all_providers continues after unregistered/exception providers."""

    @patch("luana_core_analytics_engine.application.services.etl_service.get_provider")
    def test_skips_unregistered_provider_and_continues(self, mock_get_provider):
        """ValueError from get_provider -> skips that provider, keeps going."""
        mock_get_provider.side_effect = ValueError("Provider not registered")

        svc, _db, port, _cache = _make_service()
        port.list_active_connections.return_value = [
            _make_connection("unknown_provider"),
        ]

        results = _run(svc.run_all_providers(TENANT_ID))

        assert results == []

    def test_continues_after_extraction_exception(self):
        """Generic exception from run_extraction -> provider skipped, no re-raise."""
        svc, _db, port, _cache = _make_service()
        port.list_active_connections.return_value = [_make_connection("meta")]
        # Simulate run_extraction blowing up for this provider
        svc.run_extraction = AsyncMock(side_effect=RuntimeError("Unexpected failure"))

        # Should NOT raise — Exception handler in run_all_providers silences it
        results = _run(svc.run_all_providers(TENANT_ID))

        assert results == []


# ---------------------------------------------------------------------------
# run_period_extraction
# ---------------------------------------------------------------------------


class TestETLServiceRunPeriodExtraction:
    """run_period_extraction iterates connections, skips non-eligible."""

    def test_returns_empty_when_no_connections(self):
        """No active connections -> empty results list."""
        svc, _db, port, _cache = _make_service()
        port.list_active_connections.return_value = []

        results = _run(svc.run_period_extraction(TENANT_ID, "weekly", date(2026, 3, 3), date(2026, 3, 9)))

        assert results == []

    @patch("luana_core_analytics_engine.application.services.etl_service.get_provider")
    def test_skips_provider_without_period_extraction(self, mock_get_provider):
        """Provider.has_period_extraction() == False -> skip."""
        mock_provider = MagicMock()
        mock_provider.has_period_extraction.return_value = False
        mock_get_provider.return_value = mock_provider

        svc, _db, port, _cache = _make_service()
        port.list_active_connections.return_value = [_make_connection("meta")]

        results = _run(svc.run_period_extraction(TENANT_ID, "weekly", date(2026, 3, 3), date(2026, 3, 9)))

        assert results == []

    @patch("luana_core_analytics_engine.application.services.etl_service.get_provider")
    def test_skips_already_extracted_period(self, mock_get_provider):
        """Period already in period_metrics -> status=skipped, reason=already_extracted."""
        mock_provider = MagicMock()
        mock_provider.has_period_extraction.return_value = True
        mock_get_provider.return_value = mock_provider

        svc, _db, port, _cache = _make_service()
        port.list_active_connections.return_value = [_make_connection("meta")]

        period_start = date(2026, 3, 3)
        # Lazy import path: patch at the source module
        with patch(
            "luana_core_analytics_engine.infrastructure.repositories.period_metrics_repository.PeriodMetricsRepository"
        ) as MockRepo:
            mock_period_repo = MagicMock()
            mock_period_repo.get_existing_periods.return_value = {period_start}
            MockRepo.return_value = mock_period_repo

            results = _run(svc.run_period_extraction(TENANT_ID, "weekly", period_start, date(2026, 3, 9)))

        assert len(results) == 1
        assert results[0]["status"] == "skipped"
        assert results[0]["reason"] == "already_extracted"

    @patch("luana_core_analytics_engine.application.services.etl_service.get_provider")
    def test_runs_pipeline_for_eligible_provider(self, mock_get_provider):
        """Eligible provider (period_extraction + not extracted) -> pipeline.run called."""
        mock_provider = MagicMock()
        mock_provider.has_period_extraction.return_value = True
        mock_get_provider.return_value = mock_provider

        svc, _db, port, _cache = _make_service()
        port.list_active_connections.return_value = [_make_connection("meta")]

        period_start = date(2026, 3, 3)
        pipeline_result = {"provider": "meta", "status": "success", "metrics_count": 5}

        # Both are lazy imports inside the method — patch at source module level
        with (
            patch(
                "luana_core_analytics_engine.infrastructure.repositories.period_metrics_repository.PeriodMetricsRepository"
            ) as MockPeriodRepo,
            patch(
                "luana_core_analytics_engine.infrastructure.etl.period_pipeline.PeriodExtractionPipeline"
            ) as MockPipeline,
        ):
            mock_period_repo = MagicMock()
            mock_period_repo.get_existing_periods.return_value = set()
            MockPeriodRepo.return_value = mock_period_repo

            mock_pipeline_instance = AsyncMock()
            mock_pipeline_instance.run.return_value = pipeline_result
            MockPipeline.return_value = mock_pipeline_instance

            results = _run(svc.run_period_extraction(TENANT_ID, "weekly", period_start, date(2026, 3, 9)))

        assert len(results) == 1
        assert results[0]["status"] == "success"
        mock_pipeline_instance.run.assert_called_once()

    @patch("luana_core_analytics_engine.application.services.etl_service.get_provider")
    def test_skips_when_provider_not_registered(self, mock_get_provider):
        """ValueError from get_provider -> connection skipped silently."""
        mock_get_provider.side_effect = ValueError("Not registered")

        svc, _db, port, _cache = _make_service()
        port.list_active_connections.return_value = [_make_connection("unknown")]

        results = _run(svc.run_period_extraction(TENANT_ID, "weekly", date(2026, 3, 3), date(2026, 3, 9)))

        assert results == []


# ---------------------------------------------------------------------------
# _sync_ig_dm
# ---------------------------------------------------------------------------


class TestETLServiceSyncIgDm:
    """_sync_ig_dm delegates to InstagramDMSyncService."""

    def test_delegates_to_ig_dm_sync_service(self):
        """_sync_ig_dm instantiates InstagramDMSyncService and calls sync."""
        svc, _db, _port, _cache = _make_service()
        expected_result = {"synced": 5, "skipped": 0}

        # Lazy import inside method — patch at source module
        with patch(
            "luana_core_analytics_engine.application.services.ig_dm_sync_service.InstagramDMSyncService"
        ) as MockSyncSvc:
            mock_instance = AsyncMock()
            mock_instance.sync.return_value = expected_result
            MockSyncSvc.return_value = mock_instance

            result = _run(svc._sync_ig_dm(TENANT_ID))

        assert result == expected_result
        mock_instance.sync.assert_called_once_with(TENANT_ID)


# ---------------------------------------------------------------------------
# _try_period_extraction
# ---------------------------------------------------------------------------


class TestETLServiceTryPeriodExtraction:
    """_try_period_extraction is non-fatal: exceptions silenced."""

    @patch("luana_core_analytics_engine.application.services.etl_service.get_provider")
    def test_no_op_when_provider_lacks_period_extraction(self, mock_get_provider):
        """Provider.has_period_extraction() == False -> early return, no pipeline."""
        mock_provider = MagicMock()
        mock_provider.has_period_extraction.return_value = False
        mock_get_provider.return_value = mock_provider

        svc, _db, _port, _cache = _make_service()
        mock_run_repo = MagicMock()

        # Lazy import — patch at source module
        with patch(
            "luana_core_analytics_engine.infrastructure.etl.period_pipeline.PeriodExtractionPipeline"
        ) as MockPipeline:
            _run(svc._try_period_extraction(TENANT_ID, "meta", date(2026, 3, 1), date(2026, 3, 14), mock_run_repo))
            MockPipeline.assert_not_called()

    @patch("luana_core_analytics_engine.application.services.etl_service.get_provider")
    def test_runs_period_pipeline_when_supported(self, mock_get_provider):
        """Provider supports period extraction -> PeriodExtractionPipeline.run called."""
        mock_provider = MagicMock()
        mock_provider.has_period_extraction.return_value = True
        mock_get_provider.return_value = mock_provider

        svc, _db, _port, _cache = _make_service()
        mock_run_repo = MagicMock()

        # Lazy imports — patch at source modules
        with (
            patch(
                "luana_core_analytics_engine.infrastructure.repositories.period_metrics_repository.PeriodMetricsRepository"
            ),
            patch(
                "luana_core_analytics_engine.infrastructure.etl.period_pipeline.PeriodExtractionPipeline"
            ) as MockPipeline,
        ):
            mock_pipeline_instance = AsyncMock()
            MockPipeline.return_value = mock_pipeline_instance

            _run(svc._try_period_extraction(TENANT_ID, "meta", date(2026, 3, 1), date(2026, 3, 14), mock_run_repo))

        mock_pipeline_instance.run.assert_called_once()

    @patch("luana_core_analytics_engine.application.services.etl_service.get_provider")
    def test_exception_is_silenced(self, mock_get_provider):
        """Any exception in _try_period_extraction is caught and logged, not re-raised."""
        mock_get_provider.side_effect = RuntimeError("Registry error")

        svc, _db, _port, _cache = _make_service()
        mock_run_repo = MagicMock()

        # Should NOT raise
        _run(svc._try_period_extraction(TENANT_ID, "meta", date(2026, 3, 1), date(2026, 3, 14), mock_run_repo))


# ---------------------------------------------------------------------------
# _parse_shopify_datetime
# ---------------------------------------------------------------------------


class TestETLServiceParseShopifyDatetime:
    """_parse_shopify_datetime converts Shopify ISO strings."""

    def test_parses_valid_iso_string(self):
        from luana_core_analytics_engine.application.services.etl_service import ETLService

        result = ETLService._parse_shopify_datetime("2026-03-10T14:30:00")

        assert result is not None
        assert result.year == 2026
        assert result.month == 3
        assert result.day == 10

    def test_returns_none_for_empty_string(self):
        from luana_core_analytics_engine.application.services.etl_service import ETLService

        result = ETLService._parse_shopify_datetime("")

        assert result is None

    def test_returns_none_for_invalid_format(self):
        from luana_core_analytics_engine.application.services.etl_service import ETLService

        result = ETLService._parse_shopify_datetime("not-a-date")

        assert result is None


# ---------------------------------------------------------------------------
# _stage_transform_upsert_aggregate
# ---------------------------------------------------------------------------


class TestETLServiceStageTransformUpsertAggregate:
    """_stage_transform_upsert_aggregate: stage → transform → upsert → aggregate."""

    @patch("luana_core_analytics_engine.application.services.etl_service.compute_aggregations")
    @patch("luana_core_analytics_engine.application.services.etl_service.transform_staging_to_official")
    def test_calls_pipeline_in_order(self, mock_transform, mock_compute):
        """staging_repo.bulk_insert → transform → upsert → compute_aggs."""
        from luana_core_analytics_engine.application.services.etl_service import ETLService
        from luana_core_analytics_engine.infrastructure.providers.base import ExtractedMetric

        run_id = uuid.uuid4()
        mock_transform.return_value = [
            {
                "tenant_id": TENANT_ID,
                "channel_slug": "meta-ads",
                "metric_name": "impressions",
                "value": 1000.0,
                "unit": "count",
                "currency": None,
                "cost_type": "investment",
                "metric_date": date(2026, 3, 10),
            }
        ]
        mock_compute.return_value = []  # no aggregations

        mock_db = MagicMock()
        svc = ETLService(db=mock_db, connection_port=AsyncMock(), cache=AsyncMock())

        mock_staging_repo = MagicMock()
        mock_official_repo = MagicMock()
        mock_period_config = MagicMock()

        extracted = [
            ExtractedMetric(
                provider="meta",
                channel_slug="meta-ads",
                metric_name="impressions",
                value=1000.0,
                unit="count",
                date=date(2026, 3, 10),
            )
        ]

        svc._stage_transform_upsert_aggregate(
            TENANT_ID,
            "meta",
            extracted,
            run_id,
            mock_period_config,
            mock_staging_repo,
            mock_official_repo,
        )

        mock_staging_repo.delete_by_tenant_provider.assert_called_once_with(TENANT_ID, "meta")
        mock_staging_repo.bulk_insert.assert_called_once()
        mock_transform.assert_called_once()
        mock_official_repo.upsert_from_staging.assert_called_once()
        mock_compute.assert_called_once()

    @patch("luana_core_analytics_engine.application.services.etl_service.compute_aggregations")
    @patch("luana_core_analytics_engine.application.services.etl_service.transform_staging_to_official")
    @patch("luana_core_analytics_engine.application.services.etl_service.MetricAggregationRepository")
    def test_calls_replace_aggregations_when_aggs_exist(self, mock_agg_repo_cls, mock_transform, mock_compute):
        """When compute_aggregations returns data, replace_aggregations is called per channel."""
        from luana_core_analytics_engine.application.services.etl_service import ETLService
        from luana_core_analytics_engine.infrastructure.providers.base import ExtractedMetric

        run_id = uuid.uuid4()
        mock_transform.return_value = []
        mock_compute.return_value = [
            {"channel_slug": "meta-ads", "metric_name": "impressions", "value": 500.0},
            {"channel_slug": "meta-ads", "metric_name": "clicks", "value": 50.0},
        ]

        mock_agg_repo_instance = MagicMock()
        mock_agg_repo_cls.return_value = mock_agg_repo_instance

        mock_db = MagicMock()
        svc = ETLService(db=mock_db, connection_port=AsyncMock(), cache=AsyncMock())

        extracted = [
            ExtractedMetric(
                provider="meta",
                channel_slug="meta-ads",
                metric_name="impressions",
                value=1000.0,
                unit="count",
                date=date(2026, 3, 10),
            )
        ]

        svc._stage_transform_upsert_aggregate(
            TENANT_ID,
            "meta",
            extracted,
            run_id,
            MagicMock(),
            MagicMock(),
            MagicMock(),
        )

        mock_agg_repo_instance.replace_aggregations.assert_called_once()


# ---------------------------------------------------------------------------
# run_initial_load
# ---------------------------------------------------------------------------


class TestETLServiceRunInitialLoad:
    """run_initial_load: gap detection, extract, stage, aggregate."""

    @patch("luana_core_analytics_engine.application.services.etl_service.OfficialMetricsRepository")
    def test_returns_early_when_all_days_already_loaded(self, mock_official_repo_cls):
        """No missing days -> return immediately without extraction."""
        from datetime import timedelta

        from luana_core_platform.domain.datetime_utils import utc_today

        svc, _mock_db, port, _cache = _make_service()

        start_date = utc_today() - timedelta(days=30)
        all_days = {start_date + timedelta(days=i) for i in range(31)}

        mock_official_repo = MagicMock()
        mock_official_repo.get_existing_dates.return_value = all_days
        mock_official_repo_cls.return_value = mock_official_repo

        result = _run(svc.run_initial_load(TENANT_ID, "meta"))

        assert result["loaded"] == 0
        assert result["skipped"] == len(all_days)
        port.get_credentials.assert_not_called()

    @patch("luana_core_analytics_engine.application.services.etl_service.get_provider")
    @patch("luana_core_analytics_engine.application.services.etl_service.OfficialMetricsRepository")
    @patch("luana_core_analytics_engine.application.services.etl_service.StagingMetricsRepository")
    @patch("luana_core_analytics_engine.application.services.etl_service.ExtractionRunRepository")
    def test_extracts_missing_days_and_returns_loaded_count(
        self, mock_run_repo_cls, mock_staging_repo_cls, mock_official_repo_cls, mock_get_provider
    ):
        """When missing days exist, extracts, stages, and returns loaded count."""
        from datetime import timedelta

        from luana_core_analytics_engine.domain.extraction_result import ExtractionResult
        from luana_core_analytics_engine.infrastructure.providers.base import ExtractedMetric
        from luana_core_platform.domain.datetime_utils import utc_today

        today = utc_today()
        start_date = today - timedelta(days=5)

        # 3 days already loaded, 2 missing
        day_0 = start_date
        day_1 = start_date + timedelta(days=1)
        day_2 = start_date + timedelta(days=2)
        existing = {day_0, day_1, day_2}

        mock_official_repo = MagicMock()
        mock_official_repo.get_existing_dates.return_value = existing
        mock_official_repo_cls.return_value = mock_official_repo

        # Provider returns metrics for days NOT in existing
        missing_day = start_date + timedelta(days=3)
        mock_provider = AsyncMock()
        mock_provider.extract_metrics_daily.return_value = ExtractionResult(
            metrics=[
                ExtractedMetric(
                    provider="meta",
                    channel_slug="meta-ads",
                    metric_name="impressions",
                    value=1000.0,
                    unit="count",
                    date=missing_day,
                )
            ]
        )
        mock_get_provider.return_value = mock_provider

        mock_run_model = MagicMock()
        mock_run_model.id = uuid.uuid4()
        mock_run_repo_cls.return_value.create.return_value = mock_run_model

        svc, _mock_db, port, cache = _make_service()
        port.get_credentials.return_value = MagicMock(
            credentials={"access_token": "test"},
            config={},
        )

        # Patch the heavy internal methods
        svc._stage_transform_upsert_aggregate = MagicMock()
        svc._try_period_extraction = AsyncMock()

        result = _run(svc.run_initial_load(TENANT_ID, "meta", days=5))

        assert result["loaded"] == 1
        svc._stage_transform_upsert_aggregate.assert_called_once()
        cache.invalidate_tenant.assert_called_once_with(str(TENANT_ID))

    @patch("luana_core_analytics_engine.application.services.etl_service.get_provider")
    @patch("luana_core_analytics_engine.application.services.etl_service.OfficialMetricsRepository")
    def test_returns_early_when_zero_metrics_extracted(self, mock_official_repo_cls, mock_get_provider):
        """Provider returns 0 metrics for missing days -> early return."""
        from luana_core_analytics_engine.domain.extraction_result import ExtractionResult

        existing = set()  # no existing days = all missing

        mock_official_repo = MagicMock()
        mock_official_repo.get_existing_dates.return_value = existing
        mock_official_repo_cls.return_value = mock_official_repo

        mock_provider = AsyncMock()
        mock_provider.extract_metrics_daily.return_value = ExtractionResult(metrics=[])
        mock_get_provider.return_value = mock_provider

        svc, _db, port, _cache = _make_service()
        port.get_credentials.return_value = MagicMock(credentials={}, config={})

        result = _run(svc.run_initial_load(TENANT_ID, "meta", days=3))

        assert result["loaded"] == 0

    @patch("luana_core_analytics_engine.application.services.etl_service.get_provider")
    @patch("luana_core_analytics_engine.application.services.etl_service.OfficialMetricsRepository")
    @patch("luana_core_analytics_engine.application.services.etl_service.StagingMetricsRepository")
    @patch("luana_core_analytics_engine.application.services.etl_service.ExtractionRunRepository")
    def test_calls_progress_callback(
        self, mock_run_repo_cls, mock_staging_repo_cls, mock_official_repo_cls, mock_get_provider
    ):
        """progress_callback is called with correct phases."""
        from datetime import timedelta

        from luana_core_analytics_engine.domain.extraction_result import ExtractionResult
        from luana_core_analytics_engine.infrastructure.providers.base import ExtractedMetric
        from luana_core_platform.domain.datetime_utils import utc_today

        today = utc_today()
        missing_day = today - timedelta(days=2)

        mock_official_repo = MagicMock()
        mock_official_repo.get_existing_dates.return_value = set()
        mock_official_repo_cls.return_value = mock_official_repo

        mock_provider = AsyncMock()
        mock_provider.extract_metrics_daily.return_value = ExtractionResult(
            metrics=[
                ExtractedMetric(
                    provider="meta",
                    channel_slug="meta-ads",
                    metric_name="impressions",
                    value=100.0,
                    unit="count",
                    date=missing_day,
                )
            ]
        )
        mock_get_provider.return_value = mock_provider

        mock_run_model = MagicMock()
        mock_run_model.id = uuid.uuid4()
        mock_run_repo_cls.return_value.create.return_value = mock_run_model

        svc, _db, port, _cache = _make_service()
        port.get_credentials.return_value = MagicMock(credentials={}, config={})
        svc._stage_transform_upsert_aggregate = MagicMock()
        svc._try_period_extraction = AsyncMock()

        phases = []
        _run(
            svc.run_initial_load(
                TENANT_ID,
                "meta",
                days=2,
                progress_callback=lambda cur, tot, phase: phases.append(phase),
            )
        )

        assert "extracting" in phases
        assert "completed" in phases


# ---------------------------------------------------------------------------
# run_sync_all
# ---------------------------------------------------------------------------


class TestETLServiceRunSyncAll:
    """run_sync_all: cooldown, parallel execution, aggregation."""

    def test_returns_zero_counts_when_no_registered_providers(self):
        """No CHANNEL_TYPE_TO_PROVIDERS matches -> providers_synced=0."""
        svc, _db, port, _cache = _make_service()
        port.list_active_connections.return_value = [_make_connection("unknown_channel")]

        with (
            patch(
                "luana_core_analytics_engine.application.services.etl_service.CHANNEL_TYPE_TO_PROVIDERS",
                {},
            ),
            patch(
                "luana_core_analytics_engine.application.services.etl_service.PROVIDER_REGISTRY",
                {},
            ),
        ):
            result = _run(svc.run_sync_all(TENANT_ID))

        assert result["providers_synced"] == 0
        assert result["status"] == "ok"

    def test_skips_provider_on_cooldown(self):
        """Provider with recent run < 15min cooldown -> skipped_cooldown."""
        from datetime import UTC, datetime, timedelta

        svc, _db, port, _cache = _make_service()
        port.list_active_connections.return_value = [_make_connection("meta")]

        # Latest run started 5 minutes ago = within cooldown
        recent_run = MagicMock()
        recent_run.started_at = datetime.now(UTC) - timedelta(minutes=5)

        with (
            patch(
                "luana_core_analytics_engine.application.services.etl_service.CHANNEL_TYPE_TO_PROVIDERS",
                {"meta": {"meta"}},
            ),
            patch(
                "luana_core_analytics_engine.application.services.etl_service.PROVIDER_REGISTRY",
                {"meta": MagicMock()},
            ),
            patch(
                "luana_core_analytics_engine.application.services.etl_service.ExtractionRunRepository"
            ) as MockRunRepo,
        ):
            MockRunRepo.return_value.get_latest.return_value = recent_run

            result = _run(svc.run_sync_all(TENANT_ID))

        assert result["providers_skipped_cooldown"] == 1
        assert result["providers_synced"] == 0

    def test_provider_exception_counted_as_failed(self):
        """_run_provider_isolated raises -> result counted in providers_failed."""
        svc, _db, port, _cache = _make_service()
        port.list_active_connections.return_value = [_make_connection("meta")]

        with (
            patch(
                "luana_core_analytics_engine.application.services.etl_service.CHANNEL_TYPE_TO_PROVIDERS",
                {"meta": {"meta"}},
            ),
            patch(
                "luana_core_analytics_engine.application.services.etl_service.PROVIDER_REGISTRY",
                {"meta": MagicMock()},
            ),
            patch(
                "luana_core_analytics_engine.application.services.etl_service.ExtractionRunRepository"
            ) as MockRunRepo,
        ):
            # No cooldown (no recent run)
            MockRunRepo.return_value.get_latest.return_value = None

            # _run_provider_isolated raises (via asyncio.gather return_exceptions=True)
            svc._run_provider_isolated = AsyncMock(side_effect=RuntimeError("Network error"))

            result = _run(svc.run_sync_all(TENANT_ID))

        assert result["providers_failed"] == 1
        assert result["providers_synced"] == 0
