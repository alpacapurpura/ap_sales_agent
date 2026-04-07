"""
Unit tests for GoogleAnalyticsAdapter.run_report() — GA4 Data API wrapper.

Tests cover:
- Happy path: dimensions + metrics returned as normalized dict
- Empty response handling
- Missing credentials error
- asyncio.to_thread usage for sync-safe execution
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.connections.infrastructure.channels.google_analytics import (
    GoogleAnalyticsAdapter,
)


def _make_fake_response(rows=None, row_count=None):
    """Build a mock GA4 RunReportResponse."""
    response = MagicMock()
    response.dimension_headers = [
        MagicMock(name="date"),
        MagicMock(name="country"),
    ]
    # MagicMock.name is special — override via configure_mock
    response.dimension_headers[0].configure_mock(name="date")
    response.dimension_headers[1].configure_mock(name="country")

    response.metric_headers = [
        MagicMock(name="sessions"),
        MagicMock(name="activeUsers"),
    ]
    response.metric_headers[0].configure_mock(name="sessions")
    response.metric_headers[1].configure_mock(name="activeUsers")

    if rows is None:
        row1 = MagicMock()
        row1.dimension_values = [MagicMock(value="20260301"), MagicMock(value="US")]
        row1.metric_values = [MagicMock(value="120"), MagicMock(value="95")]
        row2 = MagicMock()
        row2.dimension_values = [MagicMock(value="20260302"), MagicMock(value="MX")]
        row2.metric_values = [MagicMock(value="80"), MagicMock(value="60")]
        response.rows = [row1, row2]
        response.row_count = 2
    else:
        response.rows = rows
        response.row_count = row_count if row_count is not None else len(rows)

    return response


class TestRunReportHappyPath:
    """run_report() returns a normalized dict with rows, row_count, metadata."""

    @pytest.mark.asyncio
    async def test_returns_normalized_dict(self):
        fake_response = _make_fake_response()

        with (
            patch(
                "src.modules.connections.infrastructure.channels.google_analytics.BetaAnalyticsDataClient"
            ) as MockClient,
            patch(
                "src.modules.connections.infrastructure.channels.google_analytics.asyncio"
            ) as mock_asyncio,
        ):
            mock_client_instance = MagicMock()
            MockClient.return_value = mock_client_instance

            # Make asyncio.to_thread call the function synchronously for testing
            async def fake_to_thread(fn, *args, **kwargs):
                return fn(*args, **kwargs)

            mock_asyncio.to_thread = AsyncMock(side_effect=fake_to_thread)
            mock_client_instance.run_report.return_value = fake_response

            adapter = GoogleAnalyticsAdapter(
                client_config={"client_id": "id", "client_secret": "secret"},
                credentials_data={
                    "token": "tok",
                    "refresh_token": "ref",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "client_id": "id",
                    "client_secret": "secret",
                },
            )

            result = await adapter.run_report(
                property_id="123456",
                dimensions=["date", "country"],
                metrics=["sessions", "activeUsers"],
                start_date="30daysAgo",
                end_date="today",
            )

        assert result["row_count"] == 2
        assert len(result["rows"]) == 2
        assert result["rows"][0]["dimensions"] == ["20260301", "US"]
        assert result["rows"][0]["metrics"] == ["120", "95"]
        assert result["rows"][1]["dimensions"] == ["20260302", "MX"]
        assert result["rows"][1]["metrics"] == ["80", "60"]
        assert result["metadata"]["dimensions"] == ["date", "country"]
        assert result["metadata"]["metrics"] == ["sessions", "activeUsers"]

    @pytest.mark.asyncio
    async def test_creates_client_with_credentials(self):
        fake_response = _make_fake_response()

        with (
            patch(
                "src.modules.connections.infrastructure.channels.google_analytics.BetaAnalyticsDataClient"
            ) as MockClient,
            patch(
                "src.modules.connections.infrastructure.channels.google_analytics.asyncio"
            ) as mock_asyncio,
        ):
            mock_client_instance = MagicMock()
            MockClient.return_value = mock_client_instance

            async def fake_to_thread(fn, *args, **kwargs):
                return fn(*args, **kwargs)

            mock_asyncio.to_thread = AsyncMock(side_effect=fake_to_thread)
            mock_client_instance.run_report.return_value = fake_response

            adapter = GoogleAnalyticsAdapter(
                client_config={"client_id": "id", "client_secret": "secret"},
                credentials_data={
                    "token": "tok",
                    "refresh_token": "ref",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "client_id": "id",
                    "client_secret": "secret",
                },
            )

            await adapter.run_report(
                property_id="99",
                dimensions=["date"],
                metrics=["sessions"],
            )

        MockClient.assert_called_once_with(credentials=adapter.creds)

    @pytest.mark.asyncio
    async def test_constructs_request_with_correct_property_format(self):
        fake_response = _make_fake_response()

        with (
            patch(
                "src.modules.connections.infrastructure.channels.google_analytics.BetaAnalyticsDataClient"
            ) as MockClient,
            patch(
                "src.modules.connections.infrastructure.channels.google_analytics.asyncio"
            ) as mock_asyncio,
            patch(
                "src.modules.connections.infrastructure.channels.google_analytics.RunReportRequest"
            ) as MockRequest,
        ):
            mock_client_instance = MagicMock()
            MockClient.return_value = mock_client_instance

            async def fake_to_thread(fn, *args, **kwargs):
                return fn(*args, **kwargs)

            mock_asyncio.to_thread = AsyncMock(side_effect=fake_to_thread)
            mock_client_instance.run_report.return_value = fake_response

            adapter = GoogleAnalyticsAdapter(
                client_config={"client_id": "id", "client_secret": "secret"},
                credentials_data={
                    "token": "tok",
                    "refresh_token": "ref",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "client_id": "id",
                    "client_secret": "secret",
                },
            )

            await adapter.run_report(
                property_id="123456",
                dimensions=["date"],
                metrics=["sessions"],
                start_date="7daysAgo",
                end_date="yesterday",
            )

        # Verify the property format includes "properties/" prefix
        call_kwargs = MockRequest.call_args
        assert (
            call_kwargs.kwargs.get("property") == "properties/123456"
            or (False)
            or call_kwargs[1].get("property") == "properties/123456"
        )


class TestRunReportAsyncSafety:
    """run_report() wraps sync SDK call in asyncio.to_thread()."""

    @pytest.mark.asyncio
    async def test_uses_asyncio_to_thread(self):
        fake_response = _make_fake_response()

        with (
            patch(
                "src.modules.connections.infrastructure.channels.google_analytics.BetaAnalyticsDataClient"
            ) as MockClient,
            patch(
                "src.modules.connections.infrastructure.channels.google_analytics.asyncio"
            ) as mock_asyncio,
        ):
            mock_client_instance = MagicMock()
            MockClient.return_value = mock_client_instance

            async def fake_to_thread(fn, *args, **kwargs):
                return fn(*args, **kwargs)

            mock_asyncio.to_thread = AsyncMock(side_effect=fake_to_thread)
            mock_client_instance.run_report.return_value = fake_response

            adapter = GoogleAnalyticsAdapter(
                client_config={"client_id": "id", "client_secret": "secret"},
                credentials_data={
                    "token": "tok",
                    "refresh_token": "ref",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "client_id": "id",
                    "client_secret": "secret",
                },
            )

            await adapter.run_report(
                property_id="123",
                dimensions=["date"],
                metrics=["sessions"],
            )

        mock_asyncio.to_thread.assert_called_once()


class TestRunReportEmptyResponse:
    """run_report() with empty response returns zero rows."""

    @pytest.mark.asyncio
    async def test_empty_response(self):
        fake_response = _make_fake_response(rows=[], row_count=0)

        with (
            patch(
                "src.modules.connections.infrastructure.channels.google_analytics.BetaAnalyticsDataClient"
            ) as MockClient,
            patch(
                "src.modules.connections.infrastructure.channels.google_analytics.asyncio"
            ) as mock_asyncio,
        ):
            mock_client_instance = MagicMock()
            MockClient.return_value = mock_client_instance

            async def fake_to_thread(fn, *args, **kwargs):
                return fn(*args, **kwargs)

            mock_asyncio.to_thread = AsyncMock(side_effect=fake_to_thread)
            mock_client_instance.run_report.return_value = fake_response

            adapter = GoogleAnalyticsAdapter(
                client_config={"client_id": "id", "client_secret": "secret"},
                credentials_data={
                    "token": "tok",
                    "refresh_token": "ref",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "client_id": "id",
                    "client_secret": "secret",
                },
            )

            result = await adapter.run_report(
                property_id="123",
                dimensions=["date"],
                metrics=["sessions"],
            )

        assert result["row_count"] == 0
        assert result["rows"] == []
        assert "metadata" in result
        assert result["metadata"]["dimensions"] == ["date", "country"]
        assert result["metadata"]["metrics"] == ["sessions", "activeUsers"]


class TestRunReportNoCredentials:
    """run_report() raises ValueError when credentials not initialized."""

    @pytest.mark.asyncio
    async def test_raises_without_credentials(self):
        adapter = GoogleAnalyticsAdapter(
            client_config={"client_id": "id", "client_secret": "secret"}
        )

        with pytest.raises(ValueError, match="Credentials not initialized"):
            await adapter.run_report(
                property_id="123",
                dimensions=["date"],
                metrics=["sessions"],
            )
