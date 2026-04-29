"""Tests for YouTube and YouTube Analytics API route functions."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from src.modules.connections.api.youtube import (
    disconnect,
    get_auth_url,
    get_status,
    oauth_callback,
    update_config,
)
from src.modules.connections.api.youtube import (
    test_connection as yt_test_connection,
)
from src.modules.connections.api.youtube_analytics import (
    _default_dates,
    get_countries,
    get_daily_views,
    get_demographics,
    get_overview,
    get_top_videos,
    get_top_videos_enriched,
    get_traffic_sources,
)
from src.modules.connections.api.youtube_analytics import (
    get_status as yta_get_status,
)
from src.modules.connections.api.youtube_analytics import (
    test_connection as yta_test_connection,
)

TENANT_ID = uuid4()


def _user():
    return SimpleNamespace(tenant_id=TENANT_ID, id=uuid4())


def _repo(**kwargs):
    repo = MagicMock()
    for k, v in kwargs.items():
        setattr(repo, k, v)
    return repo


def _conn(config=None, credentials=None, is_active=True):
    c = MagicMock()
    c.config = config or {}
    c.credentials = credentials or {"access_token": "tok", "refresh_token": "rt"}
    c.is_active = is_active
    return c


def _mock_db_with_tenant(config_json=None):
    db = MagicMock()
    tenant = MagicMock()
    tenant.config_json = config_json or {}
    db.execute.return_value.scalars.return_value.first.return_value = tenant
    return db, tenant


# ---------------------------------------------------------------------------
# update_config
# ---------------------------------------------------------------------------


class TestYouTubeUpdateConfig:
    @pytest.mark.asyncio
    async def test_saves_client_credentials(self):
        db, _tenant = _mock_db_with_tenant()
        user = _user()

        result = await update_config("new_cid", "new_csec", db, user)

        db.commit.assert_called_once()
        assert result["status"] == "updated"

    @pytest.mark.asyncio
    async def test_raises_404_when_tenant_not_found(self):
        db = MagicMock()
        db.execute.return_value.scalars.return_value.first.return_value = None
        user = _user()

        with pytest.raises(HTTPException) as exc_info:
            await update_config("cid", "csec", db, user)
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# get_auth_url
# ---------------------------------------------------------------------------


class TestYouTubeGetAuthUrl:
    @pytest.mark.asyncio
    async def test_returns_url_and_state(self):
        db, _ = _mock_db_with_tenant(
            config_json={"integrations": {"youtube": {"client_id": "cid", "client_secret": "csec"}}}
        )
        user = _user()

        with patch("src.modules.connections.api.youtube.YoutubeAdapter") as MockAdapter:
            MockAdapter.return_value.get_authorization_url.return_value = (
                "https://accounts.google.com/auth",
                "state_xyz",
            )
            result = await get_auth_url(user, db, redirect_uri=None)

        assert "url" in result
        assert result["state"] == "state_xyz"

    @pytest.mark.asyncio
    async def test_raises_400_when_not_configured(self):
        db, _ = _mock_db_with_tenant(config_json={})
        user = _user()

        with pytest.raises(HTTPException) as exc_info:
            await get_auth_url(user, db)
        assert exc_info.value.status_code == 400


# ---------------------------------------------------------------------------
# oauth_callback
# ---------------------------------------------------------------------------


class TestYouTubeOAuthCallback:
    @pytest.mark.asyncio
    async def test_raises_400_on_exchange_failure(self):
        db, _ = _mock_db_with_tenant(
            config_json={"integrations": {"youtube": {"client_id": "cid", "client_secret": "csec"}}}
        )
        user = _user()
        repo = _repo()

        with patch("src.modules.connections.api.youtube.YoutubeAdapter") as MockAdapter:
            MockAdapter.return_value.exchange_code.side_effect = Exception("bad code")
            with pytest.raises(HTTPException) as exc_info:
                await oauth_callback("bad_code", db, user, repo, redirect_uri=None)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_saves_credentials_on_success(self):
        db, _ = _mock_db_with_tenant(
            config_json={"integrations": {"youtube": {"client_id": "cid", "client_secret": "csec"}}}
        )
        user = _user()
        repo = _repo(upsert=MagicMock())
        creds = {"access_token": "at", "refresh_token": "rt"}
        channel_info = {
            "id": "UCxx",
            "title": "My Channel",
            "customUrl": "@mychannel",
            "thumbnails": {},
            "statistics": {},
        }

        with patch("src.modules.connections.api.youtube.YoutubeAdapter") as MockAdapter:
            MockAdapter.return_value.exchange_code.return_value = creds
            MockAdapter.return_value.get_channel_info.return_value = channel_info
            result = await oauth_callback("good_code", db, user, repo, redirect_uri=None)

        assert result["status"] == "connected"
        repo.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_400_when_no_channel_id(self):
        db, _ = _mock_db_with_tenant(
            config_json={"integrations": {"youtube": {"client_id": "cid", "client_secret": "csec"}}}
        )
        user = _user()
        repo = _repo()
        creds = {"access_token": "at", "refresh_token": "rt"}

        with patch("src.modules.connections.api.youtube.YoutubeAdapter") as MockAdapter:
            MockAdapter.return_value.exchange_code.return_value = creds
            # No channel id returned
            MockAdapter.return_value.get_channel_info.return_value = {"title": "No ID"}
            with pytest.raises(HTTPException) as exc_info:
                await oauth_callback("code", db, user, repo, redirect_uri=None)
        assert exc_info.value.status_code == 400


# ---------------------------------------------------------------------------
# get_status
# ---------------------------------------------------------------------------


class TestYouTubeGetStatus:
    @pytest.mark.asyncio
    async def test_not_connected_when_no_connection(self):
        db, _ = _mock_db_with_tenant()
        user = _user()
        repo = _repo(get_active=MagicMock(return_value=None))

        result = await get_status(db, user, repo)
        assert result.is_connected is False

    @pytest.mark.asyncio
    async def test_connected_returns_channel_info(self):
        db, _ = _mock_db_with_tenant(
            config_json={"integrations": {"youtube": {"client_id": "cid", "client_secret": "csec"}}}
        )
        user = _user()
        conn = _conn(config={"channel_id": "UCxx", "channel_title": "My Channel"})
        repo = _repo(get_active=MagicMock(return_value=conn))

        result = await get_status(db, user, repo)
        assert result.is_connected is True
        assert result.channel_id == "UCxx"


# ---------------------------------------------------------------------------
# disconnect
# ---------------------------------------------------------------------------


class TestYouTubeDisconnect:
    @pytest.mark.asyncio
    async def test_deactivates_connection(self):
        user = _user()
        conn = _conn()
        repo = _repo(
            get_by_tenant_and_type=MagicMock(return_value=conn),
            deactivate=MagicMock(),
        )
        result = await disconnect(user, repo)
        repo.deactivate.assert_called_once_with(conn)
        assert result["status"] == "disconnected"

    @pytest.mark.asyncio
    async def test_returns_disconnected_when_no_connection(self):
        user = _user()
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=None))
        result = await disconnect(user, repo)
        assert result["status"] == "disconnected"


# ---------------------------------------------------------------------------
# test_connection
# ---------------------------------------------------------------------------


class TestYouTubeTestConnection:
    @pytest.mark.asyncio
    async def test_raises_400_when_not_connected(self):
        db, _ = _mock_db_with_tenant()
        user = _user()
        repo = _repo(get_active=MagicMock(return_value=None))

        with pytest.raises(HTTPException) as exc_info:
            await yt_test_connection(db, user, repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_returns_ok_on_success(self):
        db, _ = _mock_db_with_tenant(
            config_json={"integrations": {"youtube": {"client_id": "cid", "client_secret": "csec"}}}
        )
        user = _user()
        conn = _conn()
        repo = _repo(get_active=MagicMock(return_value=conn))

        with patch("src.modules.connections.api.youtube.YoutubeAdapter") as MockAdapter:
            MockAdapter.return_value.get_channel_info.return_value = {"id": "UCxx", "title": "My Channel"}
            result = await yt_test_connection(db, user, repo)

        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_returns_error_on_exception(self):
        db, _ = _mock_db_with_tenant(
            config_json={"integrations": {"youtube": {"client_id": "cid", "client_secret": "csec"}}}
        )
        user = _user()
        conn = _conn()
        repo = _repo(get_active=MagicMock(return_value=conn))

        with patch("src.modules.connections.api.youtube.YoutubeAdapter") as MockAdapter:
            MockAdapter.return_value.get_channel_info.side_effect = Exception("API error")
            result = await yt_test_connection(db, user, repo)

        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# _default_dates (YouTube Analytics helper)
# ---------------------------------------------------------------------------


class TestDefaultDates:
    def test_fills_in_both_dates(self):
        start, end = _default_dates(None, None)
        assert start < end  # 30 days ago < today
        assert len(start) == 10  # YYYY-MM-DD

    def test_respects_provided_dates(self):
        start, end = _default_dates("2024-01-01", "2024-01-31")
        assert start == "2024-01-01"
        assert end == "2024-01-31"

    def test_fills_in_end_only(self):
        start, end = _default_dates("2024-01-01", None)
        assert start == "2024-01-01"
        assert end is not None


# ---------------------------------------------------------------------------
# get_status (YouTube Analytics)
# ---------------------------------------------------------------------------


class TestYTAGetStatus:
    @pytest.mark.asyncio
    async def test_not_connected_when_no_credentials(self):
        user = _user()
        repo = _repo(get_active=MagicMock(return_value=None))
        result = await yta_get_status(user, repo)
        assert result["is_connected"] is False

    @pytest.mark.asyncio
    async def test_connected_returns_channel_id(self):
        user = _user()
        conn = _conn()
        repo = _repo(get_active=MagicMock(return_value=conn))

        with patch("src.modules.connections.api.youtube_analytics.YouTubeAnalyticsAdapter") as MockAdapter:
            MockAdapter.return_value.get_channel_id.return_value = "UCxx"
            result = await yta_get_status(user, repo)

        assert result["is_connected"] is True
        assert result["channel_id"] == "UCxx"

    @pytest.mark.asyncio
    async def test_connected_but_channel_id_fails(self):
        user = _user()
        conn = _conn()
        repo = _repo(get_active=MagicMock(return_value=conn))

        with patch("src.modules.connections.api.youtube_analytics.YouTubeAnalyticsAdapter") as MockAdapter:
            MockAdapter.return_value.get_channel_id.side_effect = Exception("auth error")
            result = await yta_get_status(user, repo)

        assert result["is_connected"] is True
        assert result["channel_id"] is None


# ---------------------------------------------------------------------------
# Analytics data endpoints (overview, daily_views, top_videos, etc.)
# ---------------------------------------------------------------------------


class TestYTADataEndpoints:
    @pytest.mark.asyncio
    async def test_get_overview_returns_data(self):
        adapter = MagicMock()
        adapter.get_channel_overview.return_value = {"views": 1000}

        result = await get_overview(adapter, "2024-01-01", "2024-01-31")
        assert result["status"] == "ok"
        assert result["data"]["views"] == 1000

    @pytest.mark.asyncio
    async def test_get_overview_raises_500_on_error(self):
        adapter = MagicMock()
        adapter.get_channel_overview.side_effect = Exception("API error")

        with pytest.raises(HTTPException) as exc_info:
            await get_overview(adapter, "2024-01-01", "2024-01-31")
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_get_daily_views_returns_data(self):
        adapter = MagicMock()
        adapter.get_daily_views.return_value = [{"date": "2024-01-01", "views": 100}]

        result = await get_daily_views(adapter, "2024-01-01", "2024-01-31")
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_get_daily_views_raises_500_on_error(self):
        adapter = MagicMock()
        adapter.get_daily_views.side_effect = Exception("error")

        with pytest.raises(HTTPException) as exc_info:
            await get_daily_views(adapter)
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_get_top_videos_returns_list(self):
        adapter = MagicMock()
        adapter.get_top_videos.return_value = [{"video_id": "v1", "views": 500}]

        result = await get_top_videos(adapter, "2024-01-01", "2024-01-31", max_results=5)
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_get_top_videos_raises_500_on_error(self):
        adapter = MagicMock()
        adapter.get_top_videos.side_effect = Exception("error")

        with pytest.raises(HTTPException) as exc_info:
            await get_top_videos(adapter)
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_get_demographics_returns_data(self):
        adapter = MagicMock()
        adapter.get_demographics.return_value = [{"ageGroup": "25-34", "gender": "MALE", "viewerPercentage": 30}]

        result = await get_demographics(adapter)
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_get_demographics_raises_500_on_error(self):
        adapter = MagicMock()
        adapter.get_demographics.side_effect = Exception("error")

        with pytest.raises(HTTPException) as exc_info:
            await get_demographics(adapter)
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_get_traffic_sources_returns_data(self):
        adapter = MagicMock()
        adapter.get_traffic_sources.return_value = [{"source": "SEARCH", "views": 200}]

        result = await get_traffic_sources(adapter)
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_get_traffic_sources_raises_500_on_error(self):
        adapter = MagicMock()
        adapter.get_traffic_sources.side_effect = Exception("error")

        with pytest.raises(HTTPException) as exc_info:
            await get_traffic_sources(adapter)
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_get_countries_returns_data(self):
        adapter = MagicMock()
        adapter.get_countries.return_value = [{"country": "PE", "views": 1000}]

        result = await get_countries(adapter)
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_get_countries_raises_500_on_error(self):
        adapter = MagicMock()
        adapter.get_countries.side_effect = Exception("error")

        with pytest.raises(HTTPException) as exc_info:
            await get_countries(adapter)
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_get_top_videos_enriched_returns_response(self):
        adapter = MagicMock()
        video_data = [
            {
                "video_id": "v1",
                "title": "My Video",
                "thumbnail_url": "https://example.com/thumb.jpg",
                "duration": "PT5M30S",
                "published_at": "2024-01-01T00:00:00Z",
                "views": 500,
                "likes": 50,
                "watch_time_minutes": 250.0,
                "avg_view_duration": 30.0,
            }
        ]
        adapter.get_top_videos_enriched.return_value = video_data

        result = await get_top_videos_enriched(adapter)
        assert result.status == "ok"
        assert len(result.data) == 1
        assert result.data[0].video_id == "v1"

    @pytest.mark.asyncio
    async def test_get_top_videos_enriched_raises_500_on_error(self):
        adapter = MagicMock()
        adapter.get_top_videos_enriched.side_effect = Exception("error")

        with pytest.raises(HTTPException) as exc_info:
            await get_top_videos_enriched(adapter)
        assert exc_info.value.status_code == 500


# ---------------------------------------------------------------------------
# test_connection (YouTube Analytics)
# ---------------------------------------------------------------------------


class TestYTATestConnection:
    @pytest.mark.asyncio
    async def test_returns_ok_on_success(self):
        adapter = MagicMock()
        adapter.get_channel_overview.return_value = {"views": 1000}
        adapter.get_channel_id.return_value = "UCxx"

        result = await yta_test_connection(adapter)
        assert result["status"] == "ok"
        assert result["data"]["channel_id"] == "UCxx"

    @pytest.mark.asyncio
    async def test_returns_error_on_exception(self):
        adapter = MagicMock()
        adapter.get_channel_overview.side_effect = Exception("auth error")

        result = await yta_test_connection(adapter)
        assert result["status"] == "error"
