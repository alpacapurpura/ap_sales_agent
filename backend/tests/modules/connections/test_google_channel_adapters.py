"""Tests for Google infrastructure channel adapters:
YoutubeAdapter, YouTubeAnalyticsAdapter, GoogleAnalyticsAdapter,
GoogleCalendarAdapter, GmailAdapter.
"""

import datetime
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from google.auth.exceptions import RefreshError, TransportError

from luana_core_connections.infrastructure.channels.gmail import GmailAdapter
from luana_core_connections.infrastructure.channels.google_analytics import (
    GoogleAnalyticsAdapter,
)
from luana_core_connections.infrastructure.channels.google_calendar import (
    GoogleCalendarAdapter,
)
from luana_core_connections.infrastructure.channels.youtube import YoutubeAdapter
from luana_core_connections.infrastructure.channels.youtube_analytics import (
    YouTubeAnalyticsAdapter,
)

CLIENT_CONFIG = {"client_id": "cid", "client_secret": "csec"}
CREDS_DATA = {
    "token": "tok",
    "refresh_token": "rt",
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_id": "cid",
    "client_secret": "csec",
    "scopes": ["https://www.googleapis.com/auth/youtube.readonly"],
}


def _mock_creds():
    return MagicMock()


def _mock_flow(auth_url="https://accounts.google.com/auth", state="st_123"):
    flow = MagicMock()
    flow.authorization_url.return_value = (auth_url, state)
    flow.credentials.to_json.return_value = json.dumps({"access_token": "at", "refresh_token": "rt"})
    return flow


# ─────────────────────────────────────────────────────────────────────────────
# YoutubeAdapter
# ─────────────────────────────────────────────────────────────────────────────


class TestYoutubeAdapterInit:
    def test_init_without_credentials(self):
        adapter = YoutubeAdapter(client_config=CLIENT_CONFIG)
        assert adapter.creds is None

    def test_init_with_credentials_creates_creds(self):
        with patch(
            "luana_core_connections.infrastructure.channels.youtube.Credentials.from_authorized_user_info"
        ) as mock_creds:
            mock_creds.return_value = _mock_creds()
            adapter = YoutubeAdapter(client_config=CLIENT_CONFIG, credentials_data=CREDS_DATA)
        assert adapter.creds is not None


class TestYoutubeAdapterAuthUrl:
    def test_returns_url_and_state(self):
        mock_flow = _mock_flow()
        with patch(
            "luana_core_connections.infrastructure.channels.youtube.Flow.from_client_config", return_value=mock_flow
        ):
            adapter = YoutubeAdapter(client_config=CLIENT_CONFIG)
            url, state = adapter.get_authorization_url("https://redirect.example.com")
        assert url == "https://accounts.google.com/auth"
        assert state == "st_123"


class TestYoutubeAdapterExchangeCode:
    def test_returns_credentials_dict(self):
        mock_flow = _mock_flow()
        with patch(
            "luana_core_connections.infrastructure.channels.youtube.Flow.from_client_config", return_value=mock_flow
        ):
            adapter = YoutubeAdapter(client_config=CLIENT_CONFIG)
            result = adapter.exchange_code("code123", "https://redirect.example.com")
        assert result["access_token"] == "at"

    def test_raises_on_flow_error(self):
        mock_flow = MagicMock()
        mock_flow.fetch_token.side_effect = Exception("OAuth error")
        with patch(
            "luana_core_connections.infrastructure.channels.youtube.Flow.from_client_config", return_value=mock_flow
        ):
            adapter = YoutubeAdapter(client_config=CLIENT_CONFIG)
            with pytest.raises(Exception):  # noqa: B017
                adapter.exchange_code("bad_code", "https://redirect.example.com")


class TestYoutubeAdapterGetService:
    def test_raises_without_creds(self):
        adapter = YoutubeAdapter(client_config=CLIENT_CONFIG)
        with pytest.raises(ValueError):
            adapter.get_service()

    def test_builds_service_with_creds(self):
        with (
            patch(
                "luana_core_connections.infrastructure.channels.youtube.Credentials.from_authorized_user_info",
                return_value=_mock_creds(),
            ),
            patch("luana_core_connections.infrastructure.channels.youtube.build") as mock_build,
        ):
            mock_build.return_value = MagicMock()
            adapter = YoutubeAdapter(client_config=CLIENT_CONFIG, credentials_data=CREDS_DATA)
            svc = adapter.get_service()
        assert svc is not None
        mock_build.assert_called_once_with("youtube", "v3", credentials=adapter.creds)


class TestYoutubeAdapterGetChannelInfo:
    def test_returns_channel_data(self):
        mock_service = MagicMock()
        mock_service.channels.return_value.list.return_value.execute.return_value = {
            "items": [
                {
                    "id": "UC123",
                    "snippet": {"title": "My Channel", "description": "desc", "customUrl": "@me"},
                    "statistics": {"viewCount": "1000"},
                }
            ]
        }
        with (
            patch(
                "luana_core_connections.infrastructure.channels.youtube.Credentials.from_authorized_user_info",
                return_value=_mock_creds(),
            ),
            patch("luana_core_connections.infrastructure.channels.youtube.build", return_value=mock_service),
        ):
            adapter = YoutubeAdapter(client_config=CLIENT_CONFIG, credentials_data=CREDS_DATA)
            result = adapter.get_channel_info()
        assert result["id"] == "UC123"
        assert result["title"] == "My Channel"

    def test_returns_empty_when_no_items(self):
        mock_service = MagicMock()
        mock_service.channels.return_value.list.return_value.execute.return_value = {"items": []}
        with (
            patch(
                "luana_core_connections.infrastructure.channels.youtube.Credentials.from_authorized_user_info",
                return_value=_mock_creds(),
            ),
            patch("luana_core_connections.infrastructure.channels.youtube.build", return_value=mock_service),
        ):
            adapter = YoutubeAdapter(client_config=CLIENT_CONFIG, credentials_data=CREDS_DATA)
            result = adapter.get_channel_info()
        assert result == {}

    def test_raises_on_api_error(self):
        mock_service = MagicMock()
        mock_service.channels.return_value.list.return_value.execute.side_effect = Exception("API error")
        with (
            patch(
                "luana_core_connections.infrastructure.channels.youtube.Credentials.from_authorized_user_info",
                return_value=_mock_creds(),
            ),
            patch("luana_core_connections.infrastructure.channels.youtube.build", return_value=mock_service),
        ):
            adapter = YoutubeAdapter(client_config=CLIENT_CONFIG, credentials_data=CREDS_DATA)
            with pytest.raises(Exception):  # noqa: B017
                adapter.get_channel_info()


# ─────────────────────────────────────────────────────────────────────────────
# YouTubeAnalyticsAdapter
# ─────────────────────────────────────────────────────────────────────────────


def _yta(creds_data: dict | None = None) -> YouTubeAnalyticsAdapter:
    creds_data = creds_data or CREDS_DATA
    with patch(
        "luana_core_connections.infrastructure.channels.youtube_analytics.Credentials.from_authorized_user_info",
        return_value=_mock_creds(),
    ):
        return YouTubeAnalyticsAdapter(credentials_data=creds_data)


class TestYouTubeAnalyticsGetChannelId:
    def test_returns_channel_id(self):
        mock_data_svc = MagicMock()
        mock_data_svc.channels.return_value.list.return_value.execute.return_value = {"items": [{"id": "UC_test"}]}
        adapter = _yta()
        with patch.object(adapter, "_get_data_service", return_value=mock_data_svc):
            result = adapter.get_channel_id()
        assert result == "UC_test"

    def test_raises_when_no_channel(self):
        mock_data_svc = MagicMock()
        mock_data_svc.channels.return_value.list.return_value.execute.return_value = {"items": []}
        adapter = _yta()
        with patch.object(adapter, "_get_data_service", return_value=mock_data_svc), pytest.raises(ValueError):
            adapter.get_channel_id()


class TestYouTubeAnalyticsQuery:
    def _make_report(self, rows=None):
        resp = {
            "columnHeaders": [{"name": "views"}, {"name": "day"}],
            "rows": rows or [["100", "2024-01-01"]],
        }
        return resp

    def test_rows_to_dicts(self):
        adapter = _yta()
        resp = {"columnHeaders": [{"name": "views"}, {"name": "day"}], "rows": [["100", "2024-01-01"]]}
        result = adapter._rows_to_dicts(resp)
        assert result == [{"views": "100", "day": "2024-01-01"}]

    def test_rows_to_dicts_empty(self):
        adapter = _yta()
        result = adapter._rows_to_dicts({"columnHeaders": [], "rows": []})
        assert result == []

    def test_get_channel_overview_returns_dict(self):
        adapter = _yta()
        resp = {"columnHeaders": [{"name": "views"}], "rows": [["500"]]}
        with patch.object(adapter, "_query", return_value=resp):
            result = adapter.get_channel_overview("2024-01-01", "2024-01-31")
        assert result == {"views": "500"}

    def test_get_channel_overview_returns_empty_on_no_rows(self):
        adapter = _yta()
        resp = {"columnHeaders": [{"name": "views"}], "rows": []}
        with patch.object(adapter, "_query", return_value=resp):
            result = adapter.get_channel_overview("2024-01-01", "2024-01-31")
        assert result == {}

    def test_get_daily_views(self):
        adapter = _yta()
        resp = {"columnHeaders": [{"name": "day"}, {"name": "views"}], "rows": [["2024-01-01", "50"]]}
        with patch.object(adapter, "_query", return_value=resp):
            result = adapter.get_daily_views("2024-01-01", "2024-01-31")
        assert len(result) == 1

    def test_get_top_videos(self):
        adapter = _yta()
        resp = {"columnHeaders": [{"name": "video"}, {"name": "views"}], "rows": [["vid1", "200"]]}
        with patch.object(adapter, "_query", return_value=resp):
            result = adapter.get_top_videos("2024-01-01", "2024-01-31", max_results=5)
        assert result[0]["video"] == "vid1"

    def test_get_demographics(self):
        adapter = _yta()
        resp = {"columnHeaders": [{"name": "ageGroup"}, {"name": "gender"}], "rows": [["18-24", "MALE"]]}
        with patch.object(adapter, "_query", return_value=resp):
            result = adapter.get_demographics("2024-01-01", "2024-01-31")
        assert len(result) == 1

    def test_get_traffic_sources(self):
        adapter = _yta()
        resp = {"columnHeaders": [{"name": "insightTrafficSourceType"}, {"name": "views"}], "rows": [["SEARCH", "100"]]}
        with patch.object(adapter, "_query", return_value=resp):
            result = adapter.get_traffic_sources("2024-01-01", "2024-01-31")
        assert result[0]["insightTrafficSourceType"] == "SEARCH"

    def test_get_card_metrics(self):
        adapter = _yta()
        resp = {"columnHeaders": [{"name": "cardClicks"}], "rows": [["10"]]}
        with patch.object(adapter, "_query", return_value=resp):
            result = adapter.get_card_metrics("2024-01-01", "2024-01-31")
        assert result == {"cardClicks": "10"}

    def test_get_card_metrics_empty(self):
        adapter = _yta()
        resp = {"columnHeaders": [], "rows": []}
        with patch.object(adapter, "_query", return_value=resp):
            result = adapter.get_card_metrics("2024-01-01", "2024-01-31")
        assert result == {}

    def test_get_countries(self):
        adapter = _yta()
        resp = {"columnHeaders": [{"name": "country"}, {"name": "views"}], "rows": [["PE", "100"]]}
        with patch.object(adapter, "_query", return_value=resp):
            result = adapter.get_countries("2024-01-01", "2024-01-31")
        assert result[0]["country"] == "PE"


class TestYouTubeAnalyticsTopVideosEnriched:
    def test_returns_empty_when_no_analytics_videos(self):
        adapter = _yta()
        with patch.object(adapter, "get_top_videos", return_value=[]):
            result = adapter.get_top_videos_enriched("2024-01-01", "2024-01-31")
        assert result == []

    def test_returns_analytics_when_no_video_ids(self):
        adapter = _yta()
        videos = [{"views": "100"}]  # no 'video' key
        with patch.object(adapter, "get_top_videos", return_value=videos):
            result = adapter.get_top_videos_enriched("2024-01-01", "2024-01-31")
        assert result == videos

    def test_enriches_with_data_api(self):
        adapter = _yta()
        analytics_videos = [
            {
                "video": "vid1",
                "views": "100",
                "likes": "10",
                "estimatedMinutesWatched": "50",
                "averageViewDuration": "30",
            }
        ]
        mock_data_svc = MagicMock()
        mock_data_svc.videos.return_value.list.return_value.execute.return_value = {
            "items": [
                {
                    "id": "vid1",
                    "snippet": {
                        "title": "My Video",
                        "thumbnails": {"medium": {"url": "http://thumb.jpg"}},
                        "publishedAt": "2024-01-01",
                    },
                    "contentDetails": {"duration": "PT5M"},
                }
            ]
        }
        with (
            patch.object(adapter, "get_top_videos", return_value=analytics_videos),
            patch.object(adapter, "_get_data_service", return_value=mock_data_svc),
        ):
            result = adapter.get_top_videos_enriched("2024-01-01", "2024-01-31")
        assert len(result) == 1
        assert result[0]["video_id"] == "vid1"
        assert result[0]["title"] == "My Video"


# ─────────────────────────────────────────────────────────────────────────────
# GoogleAnalyticsAdapter
# ─────────────────────────────────────────────────────────────────────────────


def _ga(creds_data: dict | None = None) -> GoogleAnalyticsAdapter:
    creds_data = creds_data or CREDS_DATA
    with patch(
        "luana_core_connections.infrastructure.channels.google_analytics.Credentials.from_authorized_user_info",
        return_value=_mock_creds(),
    ):
        return GoogleAnalyticsAdapter(client_config=CLIENT_CONFIG, credentials_data=creds_data)


class TestGoogleAnalyticsAdapterInit:
    def test_init_without_credentials(self):
        adapter = GoogleAnalyticsAdapter(client_config=CLIENT_CONFIG)
        assert adapter.creds is None

    def test_init_with_credentials(self):
        adapter = _ga()
        assert adapter.creds is not None


class TestGoogleAnalyticsAdapterAuthUrl:
    def test_returns_url_and_state(self):
        mock_flow = _mock_flow()
        with patch(
            "luana_core_connections.infrastructure.channels.google_analytics.Flow.from_client_config",
            return_value=mock_flow,
        ):
            adapter = GoogleAnalyticsAdapter(client_config=CLIENT_CONFIG)
            url, _state = adapter.get_authorization_url("https://redirect.example.com")
        assert "accounts.google.com" in url


class TestGoogleAnalyticsAdapterExchangeCode:
    def test_returns_credentials(self):
        mock_flow = _mock_flow()
        with patch(
            "luana_core_connections.infrastructure.channels.google_analytics.Flow.from_client_config",
            return_value=mock_flow,
        ):
            adapter = GoogleAnalyticsAdapter(client_config=CLIENT_CONFIG)
            result = adapter.exchange_code("code123")
        assert result["access_token"] == "at"

    def test_raises_on_error(self):
        mock_flow = MagicMock()
        mock_flow.fetch_token.side_effect = Exception("OAuth error")
        with patch(
            "luana_core_connections.infrastructure.channels.google_analytics.Flow.from_client_config",
            return_value=mock_flow,
        ):
            adapter = GoogleAnalyticsAdapter(client_config=CLIENT_CONFIG)
            with pytest.raises(Exception):  # noqa: B017
                adapter.exchange_code("bad_code")


class TestGoogleAnalyticsAdapterService:
    def test_raises_without_creds(self):
        adapter = GoogleAnalyticsAdapter(client_config=CLIENT_CONFIG)
        with pytest.raises(ValueError):
            adapter.get_service()

    def test_builds_analytics_admin_service(self):
        with patch("luana_core_connections.infrastructure.channels.google_analytics.build") as mock_build:
            mock_build.return_value = MagicMock()
            adapter = _ga()
            svc = adapter.get_service()
        assert svc is not None
        mock_build.assert_called_once()


class TestGoogleAnalyticsAdapterProperties:
    def test_get_account_summaries(self):
        mock_service = MagicMock()
        mock_service.accountSummaries.return_value.list.return_value.execute.return_value = {
            "accountSummaries": [{"displayName": "Acc1", "propertySummaries": []}]
        }
        adapter = _ga()
        with patch.object(adapter, "get_service", return_value=mock_service):
            result = adapter.get_account_summaries()
        assert len(result) == 1

    def test_get_account_summaries_raises(self):
        adapter = _ga()
        with patch.object(adapter, "get_service", side_effect=Exception("API down")), pytest.raises(Exception):  # noqa: B017
            adapter.get_account_summaries()

    def test_get_flat_properties(self):
        mock_service = MagicMock()
        mock_service.accountSummaries.return_value.list.return_value.execute.return_value = {
            "accountSummaries": [
                {
                    "displayName": "Acc1",
                    "propertySummaries": [{"property": "properties/123", "displayName": "My Site"}],
                }
            ]
        }
        adapter = _ga()
        with patch.object(adapter, "get_service", return_value=mock_service):
            result = adapter.get_flat_properties()
        assert len(result) == 1
        assert result[0]["property_id"] == "123"
        assert result[0]["account_name"] == "Acc1"

    def test_get_flat_properties_returns_empty_on_error(self):
        adapter = _ga()
        with patch.object(adapter, "get_account_summaries", side_effect=Exception("API error")):
            result = adapter.get_flat_properties()
        assert result == []


class TestGoogleAnalyticsAdapterRunReport:
    @pytest.mark.asyncio
    async def test_run_report_success(self):
        mock_response = MagicMock()
        mock_response.row_count = 1
        mock_response.rows = []
        mock_response.dimension_headers = []
        mock_response.metric_headers = []

        adapter = _ga()
        with patch(
            "luana_core_connections.infrastructure.channels.google_analytics.asyncio.to_thread",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            result = await adapter.run_report("123", ["date"], ["sessions"])
        assert result["row_count"] == 1

    @pytest.mark.asyncio
    async def test_run_report_raises_refresh_error(self):
        adapter = _ga()
        with (
            patch(
                "luana_core_connections.infrastructure.channels.google_analytics.asyncio.to_thread",
                new_callable=AsyncMock,
                side_effect=RefreshError("token revoked"),
            ),
            pytest.raises(RefreshError),
        ):
            await adapter.run_report("123", ["date"], ["sessions"])

    @pytest.mark.asyncio
    async def test_run_report_raises_transport_error(self):
        adapter = _ga()
        with (
            patch(
                "luana_core_connections.infrastructure.channels.google_analytics.asyncio.to_thread",
                new_callable=AsyncMock,
                side_effect=TransportError("network error"),
            ),
            pytest.raises(TransportError),
        ):
            await adapter.run_report("123", ["date"], ["sessions"])


# ─────────────────────────────────────────────────────────────────────────────
# GoogleCalendarAdapter
# ─────────────────────────────────────────────────────────────────────────────


def _gcal(creds_data: dict | None = None) -> GoogleCalendarAdapter:
    if creds_data is None:
        creds_data = CREDS_DATA
    with patch(
        "luana_core_connections.infrastructure.channels.google_calendar.Credentials.from_authorized_user_info",
        return_value=_mock_creds(),
    ):
        return GoogleCalendarAdapter(credentials_data=creds_data)


class TestGoogleCalendarAdapterInit:
    def test_init_without_credentials(self):
        adapter = GoogleCalendarAdapter()
        assert adapter.creds is None

    def test_init_with_credentials(self):
        adapter = _gcal()
        assert adapter.creds is not None


class TestGoogleCalendarAdapterSyncMethods:
    def test_sync_contacts_returns_empty(self):
        adapter = _gcal()
        assert adapter.sync_contacts("tenant_1") == []

    def test_sync_events_calls_list_events(self):
        adapter = _gcal()
        with patch.object(adapter, "list_events", return_value=[{"id": "evt1"}]) as mock_list:
            result = adapter.sync_events("tenant_1")
        assert len(result) == 1
        mock_list.assert_called_once()


class TestGoogleCalendarAdapterAuthUrl:
    def test_returns_url_and_state(self):
        mock_flow = _mock_flow()
        with patch(
            "luana_core_connections.infrastructure.channels.google_calendar.Flow.from_client_config",
            return_value=mock_flow,
        ):
            url, _state = GoogleCalendarAdapter.get_authorization_url()
        assert "accounts.google.com" in url

    def test_exchange_code_returns_creds(self):
        mock_flow = _mock_flow()
        with patch(
            "luana_core_connections.infrastructure.channels.google_calendar.Flow.from_client_config",
            return_value=mock_flow,
        ):
            result = GoogleCalendarAdapter.exchange_code("code123")
        assert result["access_token"] == "at"

    def test_exchange_code_raises_on_error(self):
        mock_flow = MagicMock()
        mock_flow.fetch_token.side_effect = Exception("OAuth error")
        with (
            patch(
                "luana_core_connections.infrastructure.channels.google_calendar.Flow.from_client_config",
                return_value=mock_flow,
            ),
            pytest.raises(Exception),  # noqa: B017
        ):
            GoogleCalendarAdapter.exchange_code("bad_code")


class TestGoogleCalendarAdapterService:
    def test_raises_without_creds(self):
        adapter = GoogleCalendarAdapter()
        with pytest.raises(ValueError):
            adapter.get_service()

    def test_builds_calendar_service(self):
        adapter = _gcal()
        with patch("luana_core_connections.infrastructure.channels.google_calendar.build") as mock_build:
            mock_build.return_value = MagicMock()
            svc = adapter.get_service()
        assert svc is not None
        mock_build.assert_called_once_with("calendar", "v3", credentials=adapter.creds)


class TestGoogleCalendarListBusyPeriods:
    def test_returns_busy_list(self):
        mock_service = MagicMock()
        mock_service.freebusy.return_value.query.return_value.execute.return_value = {
            "calendars": {"primary": {"busy": [{"start": "2024-01-01T09:00:00Z", "end": "2024-01-01T10:00:00Z"}]}}
        }
        adapter = _gcal()
        with patch.object(adapter, "get_service", return_value=mock_service):
            start = datetime.datetime(2024, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
            end = datetime.datetime(2024, 1, 1, 23, 59, tzinfo=datetime.timezone.utc)
            result = adapter.list_busy_periods(start, end)
        assert len(result) == 1

    def test_raises_on_api_error(self):
        mock_service = MagicMock()
        mock_service.freebusy.return_value.query.return_value.execute.side_effect = Exception("API error")
        adapter = _gcal()
        with patch.object(adapter, "get_service", return_value=mock_service), pytest.raises(Exception):  # noqa: B017
            start = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
            end = datetime.datetime(2024, 1, 2, tzinfo=datetime.timezone.utc)
            adapter.list_busy_periods(start, end)


class TestGoogleCalendarCreateEvent:
    def test_creates_event(self):
        mock_event = {"id": "evt1", "htmlLink": "https://calendar.google.com/event/1"}
        mock_service = MagicMock()
        mock_service.events.return_value.insert.return_value.execute.return_value = mock_event
        adapter = _gcal()
        with patch.object(adapter, "get_service", return_value=mock_service):
            start = datetime.datetime(2024, 1, 1, 9, 0, tzinfo=datetime.timezone.utc)
            end = datetime.datetime(2024, 1, 1, 10, 0, tzinfo=datetime.timezone.utc)
            result = adapter.create_event("Meeting", "desc", start, end, ["guest@example.com"])
        assert result["id"] == "evt1"

    def test_raises_on_create_error(self):
        mock_service = MagicMock()
        mock_service.events.return_value.insert.return_value.execute.side_effect = Exception("API error")
        adapter = _gcal()
        with patch.object(adapter, "get_service", return_value=mock_service):
            start = datetime.datetime(2024, 1, 1, 9, 0, tzinfo=datetime.timezone.utc)
            end = datetime.datetime(2024, 1, 1, 10, 0, tzinfo=datetime.timezone.utc)
            with pytest.raises(Exception):  # noqa: B017
                adapter.create_event("Meeting", "desc", start, end, [])


class TestGoogleCalendarListEvents:
    def test_returns_events_list(self):
        mock_service = MagicMock()
        mock_service.events.return_value.list.return_value.execute.return_value = {
            "items": [{"id": "evt1", "summary": "Meeting"}]
        }
        adapter = _gcal()
        with patch.object(adapter, "get_service", return_value=mock_service):
            start = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
            end = datetime.datetime(2024, 1, 7, tzinfo=datetime.timezone.utc)
            result = adapter.list_events(start, end)
        assert len(result) == 1

    def test_raises_on_list_error(self):
        mock_service = MagicMock()
        mock_service.events.return_value.list.return_value.execute.side_effect = Exception("quota")
        adapter = _gcal()
        with patch.object(adapter, "get_service", return_value=mock_service), pytest.raises(Exception):  # noqa: B017
            start = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
            end = datetime.datetime(2024, 1, 7, tzinfo=datetime.timezone.utc)
            adapter.list_events(start, end)


# ─────────────────────────────────────────────────────────────────────────────
# GmailAdapter
# ─────────────────────────────────────────────────────────────────────────────


def _gmail(creds_data: dict | None = None) -> GmailAdapter:
    if creds_data is None:
        creds_data = CREDS_DATA
    with patch(
        "luana_core_connections.infrastructure.channels.gmail.Credentials.from_authorized_user_info",
        return_value=_mock_creds(),
    ):
        return GmailAdapter(credentials_data=creds_data)


class TestGmailAdapterInit:
    def test_init_without_credentials(self):
        adapter = GmailAdapter()
        assert adapter.creds is None

    def test_init_with_credentials(self):
        adapter = _gmail()
        assert adapter.creds is not None


class TestGmailAdapterAuthUrl:
    def test_returns_url_and_state(self):
        mock_flow = _mock_flow()
        with patch(
            "luana_core_connections.infrastructure.channels.gmail.Flow.from_client_config", return_value=mock_flow
        ):
            url, _state = GmailAdapter.get_authorization_url()
        assert "accounts.google.com" in url

    def test_exchange_code_returns_creds(self):
        mock_flow = _mock_flow()
        with patch(
            "luana_core_connections.infrastructure.channels.gmail.Flow.from_client_config", return_value=mock_flow
        ):
            result = GmailAdapter.exchange_code("code123")
        assert result["access_token"] == "at"

    def test_exchange_code_raises_on_error(self):
        mock_flow = MagicMock()
        mock_flow.fetch_token.side_effect = Exception("OAuth error")
        with (
            patch(
                "luana_core_connections.infrastructure.channels.gmail.Flow.from_client_config", return_value=mock_flow
            ),
            pytest.raises(Exception),  # noqa: B017
        ):
            GmailAdapter.exchange_code("bad_code")


class TestGmailAdapterService:
    def test_raises_without_creds(self):
        adapter = GmailAdapter()
        with pytest.raises(ValueError):
            adapter.get_service()

    def test_builds_gmail_service(self):
        adapter = _gmail()
        with patch("luana_core_connections.infrastructure.channels.gmail.build") as mock_build:
            mock_build.return_value = MagicMock()
            svc = adapter.get_service()
        assert svc is not None
        mock_build.assert_called_once_with("gmail", "v1", credentials=adapter.creds)


class TestGmailAdapterGetProfile:
    def test_returns_profile(self):
        mock_service = MagicMock()
        mock_service.users.return_value.getProfile.return_value.execute.return_value = {
            "emailAddress": "user@gmail.com",
            "messagesTotal": 100,
        }
        adapter = _gmail()
        with patch.object(adapter, "get_service", return_value=mock_service):
            result = adapter.get_profile()
        assert result["emailAddress"] == "user@gmail.com"

    def test_raises_when_no_email(self):
        mock_service = MagicMock()
        mock_service.users.return_value.getProfile.return_value.execute.return_value = {}
        adapter = _gmail()
        with patch.object(adapter, "get_service", return_value=mock_service), pytest.raises((ValueError, Exception)):
            adapter.get_profile()

    def test_raises_on_api_error(self):
        mock_service = MagicMock()
        mock_service.users.return_value.getProfile.return_value.execute.side_effect = Exception("API error")
        adapter = _gmail()
        with patch.object(adapter, "get_service", return_value=mock_service), pytest.raises(Exception):  # noqa: B017
            adapter.get_profile()


class TestGmailAdapterSendEmail:
    def test_sends_email(self):
        mock_service = MagicMock()
        sent_msg = {"id": "msg_123", "labelIds": ["SENT"]}
        mock_service.users.return_value.messages.return_value.send.return_value.execute.return_value = sent_msg
        adapter = _gmail()
        with patch.object(adapter, "get_service", return_value=mock_service):
            result = adapter.send_email("to@example.com", "Subject", "<p>Body</p>")
        assert result["id"] == "msg_123"

    def test_raises_on_send_error(self):
        mock_service = MagicMock()
        mock_service.users.return_value.messages.return_value.send.return_value.execute.side_effect = Exception(
            "quota exceeded"
        )
        adapter = _gmail()
        with patch.object(adapter, "get_service", return_value=mock_service), pytest.raises(Exception):  # noqa: B017
            adapter.send_email("to@example.com", "Subject", "<p>Body</p>")
