"""Tests for ETLService — multi-stage provider extraction.

Regression test: run_extraction() must iterate through PROVIDER_STAGES
for multi-stage providers (e.g. mailerlite -> capture + nurture),
not just the default "attraction" stage.

Bug: run_extraction() used stage="attraction" by default, which is invalid
for mailerlite. The provider returned 0 metrics because "attraction" is
not in EMAIL_STAGES. PROVIDER_STAGES was defined but only used in
run_initial_load(), never in run_extraction() or run_all_providers().
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
    from src.modules.analytics.domain.extraction_result import ExtractionResult

    return ExtractionResult(metrics=list(metrics))


def _make_extracted_metric(**overrides):
    from src.modules.analytics.infrastructure.providers.base import ExtractedMetric

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
        "src.modules.analytics.application.services.etl_service.get_provider",
    )
    def test_run_extraction_iterates_provider_stages_for_mailerlite(
        self,
        mock_get_provider,
    ):
        """Mailerlite extraction must call pipeline.run for BOTH capture and nurture."""
        from src.modules.analytics.application.services.etl_service import ETLService

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

        assert "capture" in stages_called, (
            f"Expected 'capture' stage but got: {stages_called}"
        )
        assert "nurture" in stages_called, (
            f"Expected 'nurture' stage but got: {stages_called}"
        )

    @patch(
        "src.modules.analytics.application.services.etl_service.get_provider",
    )
    def test_run_extraction_uses_default_stage_for_unlisted_provider(
        self,
        mock_get_provider,
    ):
        """Providers NOT in PROVIDER_STAGES use the default stage (attraction)."""
        from src.modules.analytics.application.services.etl_service import ETLService

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
        "src.modules.analytics.application.services.etl_service.get_provider",
    )
    def test_run_all_providers_extracts_all_stages_for_mailerlite(
        self,
        mock_get_provider,
    ):
        """run_all_providers must extract all stages for multi-stage providers."""
        from src.modules.analytics.application.services.etl_service import ETLService

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

        assert "capture" in stages_called, (
            f"Expected 'capture' in stages but got: {stages_called}"
        )
        assert "nurture" in stages_called, (
            f"Expected 'nurture' in stages but got: {stages_called}"
        )
