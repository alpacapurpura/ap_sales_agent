"""Tests for Google Workspace API route functions.

Covers: get_auth_url, oauth_callback, get_status, toggle_service,
disconnect_all, test_connection, _test_gmail/calendar/analytics/youtube helpers.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from luana_core_connections.api.google_workspace import (
    _test_analytics,
    _test_calendar,
    _test_gmail,
    _test_youtube,
    disconnect_all,
    get_auth_url,
    get_status,
    oauth_callback,
    toggle_service,
)
from luana_core_connections.api.google_workspace import (
    test_connection as gw_test_connection,
)
from luana_core_connections.domain.enums import ChannelType

TENANT_ID = uuid4()


def _user():
    return SimpleNamespace(tenant_id=TENANT_ID, id=uuid4())


def _repo(**kwargs):
    repo = MagicMock()
    for k, v in kwargs.items():
        setattr(repo, k, v)
    return repo


def _conn(channel_type=ChannelType.GMAIL.value, creds=None, config=None, is_active=True):
    c = MagicMock()
    c.channel_type = channel_type
    c.credentials = creds if creds is not None else {"access_token": "tok", "refresh_token": "refresh"}
    c.config = config or {}
    c.is_active = is_active
    return c


# ---------------------------------------------------------------------------
# get_auth_url
# ---------------------------------------------------------------------------


class TestGetAuthUrl:
    @pytest.mark.asyncio
    async def test_returns_url_and_state(self):
        with patch("luana_core_connections.api.google_workspace.Flow") as MockFlow:
            mock_flow = MockFlow.from_client_config.return_value
            mock_flow.authorization_url.return_value = ("https://accounts.google.com/auth", "state_abc")
            mock_flow.redirect_uri = None

            result = await get_auth_url(_user())

        assert "url" in result
        assert "state" in result
        assert result["state"] == "state_abc"


# ---------------------------------------------------------------------------
# oauth_callback
# ---------------------------------------------------------------------------


class TestOauthCallback:
    @pytest.mark.asyncio
    async def test_raises_400_on_token_exchange_failure(self):
        repo = _repo()
        with patch("luana_core_connections.api.google_workspace.Flow") as MockFlow:
            mock_flow = MockFlow.from_client_config.return_value
            mock_flow.fetch_token.side_effect = Exception("invalid code")
            mock_flow.redirect_uri = None

            with pytest.raises(HTTPException) as exc_info:
                await oauth_callback("bad_code", _user(), repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_successful_callback_stores_all_services(self):
        repo = _repo(
            get_by_tenant_and_type=MagicMock(return_value=None),
            upsert=MagicMock(),
        )

        with (
            patch("luana_core_connections.api.google_workspace.Flow") as MockFlow,
            patch("luana_core_connections.api.google_workspace.Credentials") as MockCreds,
            patch("luana_core_connections.api.google_workspace.build") as mock_build,
            patch("luana_core_connections.api.google_workspace.YoutubeAdapter") as MockYT,
        ):
            mock_flow = MockFlow.from_client_config.return_value
            mock_flow.redirect_uri = None
            mock_flow.credentials.to_json.return_value = '{"token": "tok"}'
            mock_flow.fetch_token.return_value = None
            MockCreds.from_authorized_user_info.return_value = MagicMock()
            mock_build.return_value.users.return_value.getProfile.return_value.execute.return_value = {
                "emailAddress": "test@gmail.com"
            }
            MockYT.return_value.get_channel_info.return_value = None

            result = await oauth_callback("valid_code", _user(), repo)

        assert result["status"] == "connected"
        # Should upsert for all services in SERVICE_MAP (gmail, calendar, analytics, youtube, yta)
        assert repo.upsert.call_count >= 4


# ---------------------------------------------------------------------------
# get_status
# ---------------------------------------------------------------------------


class TestGetStatus:
    @pytest.mark.asyncio
    async def test_returns_not_connected_when_no_services(self):
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=None))
        result = await get_status(_user(), repo)
        assert result["is_connected"] is False
        assert "services" in result

    @pytest.mark.asyncio
    async def test_returns_connected_when_at_least_one_has_creds(self):
        gmail_conn = _conn(channel_type=ChannelType.GMAIL.value, config={"email": "user@gmail.com"})

        def _get_conn(tenant_id, channel_type):
            if channel_type == ChannelType.GMAIL:
                return gmail_conn
            return None

        repo = _repo(get_by_tenant_and_type=MagicMock(side_effect=_get_conn))
        result = await get_status(_user(), repo)
        assert result["is_connected"] is True

    @pytest.mark.asyncio
    async def test_returns_email_from_gmail_config(self):
        gmail_conn = _conn(channel_type=ChannelType.GMAIL.value, config={"email": "me@gmail.com"})

        def _get_conn(tenant_id, channel_type):
            if channel_type == ChannelType.GMAIL:
                return gmail_conn
            return None

        repo = _repo(get_by_tenant_and_type=MagicMock(side_effect=_get_conn))
        result = await get_status(_user(), repo)
        assert result["email"] == "me@gmail.com"


# ---------------------------------------------------------------------------
# toggle_service
# ---------------------------------------------------------------------------


class TestToggleService:
    @pytest.mark.asyncio
    async def test_raises_400_for_unknown_service(self):
        repo = _repo()
        with pytest.raises(HTTPException) as exc_info:
            await toggle_service("tiktok_unknown", True, _user(), repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_raises_404_when_no_connection(self):
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=None))
        with pytest.raises(HTTPException) as exc_info:
            await toggle_service("gmail", True, _user(), repo)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_activates_gmail(self):
        conn = _conn(is_active=False)
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=conn))
        result = await toggle_service("gmail", True, _user(), repo)
        repo.activate.assert_called_once_with(conn)
        assert result["status"] == "updated"
        assert result["is_active"] is True

    @pytest.mark.asyncio
    async def test_deactivates_analytics(self):
        conn = _conn(is_active=True)
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=conn))
        result = await toggle_service("analytics", False, _user(), repo)
        repo.deactivate.assert_called_once_with(conn)
        assert result["is_active"] is False


# ---------------------------------------------------------------------------
# disconnect_all
# ---------------------------------------------------------------------------


class TestDisconnectAll:
    @pytest.mark.asyncio
    async def test_revokes_all_connected_services(self):
        gmail_conn = _conn(is_active=True)
        calendar_conn = _conn(is_active=True)

        def _get_conn(tenant_id, channel_type):
            if channel_type == ChannelType.GMAIL:
                return gmail_conn
            if channel_type == ChannelType.GOOGLE_CALENDAR:
                return calendar_conn
            return None

        repo = _repo(get_by_tenant_and_type=MagicMock(side_effect=_get_conn))
        result = await disconnect_all(_user(), repo)

        assert result["status"] == "disconnected"
        assert repo.revoke.call_count == 2
        assert "gmail" in result["services"]

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_nothing_connected(self):
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=None))
        result = await disconnect_all(_user(), repo)
        assert result["services"] == []


# ---------------------------------------------------------------------------
# test_connection
# ---------------------------------------------------------------------------


class TestTestConnection:
    @pytest.mark.asyncio
    async def test_raises_404_when_no_connection(self):
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=None))
        with pytest.raises(HTTPException) as exc_info:
            await gw_test_connection(_user(), repo)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_active_when_gmail_ok(self):
        conn = _conn()

        def _get_conn(tenant_id, channel_type):
            return conn

        repo = _repo(get_by_tenant_and_type=MagicMock(side_effect=_get_conn))

        with patch("luana_core_connections.api.google_workspace._run_service_test") as mock_run:
            mock_run.return_value = {"status": "ok"}
            result = await gw_test_connection(_user(), repo)

        assert result.status in ("active", "partial")

    @pytest.mark.asyncio
    async def test_returns_auth_error_on_refresh_failure(self):
        conn = _conn()

        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=conn))

        with patch("luana_core_connections.api.google_workspace._run_service_test") as mock_run:
            mock_run.return_value = {"status": "error", "_auth_error": True}
            result = await gw_test_connection(_user(), repo)

        assert result.status == "auth_error"


# ---------------------------------------------------------------------------
# Helpers _test_gmail / _test_calendar / _test_analytics / _test_youtube
# ---------------------------------------------------------------------------


class TestHelpers:
    def test_test_gmail_calls_gmail_api(self):
        with (
            patch("luana_core_connections.api.google_workspace.Credentials") as MockCreds,
            patch("luana_core_connections.api.google_workspace.build") as mock_build,
        ):
            mock_profile = {"emailAddress": "x@gmail.com", "messagesTotal": 10, "threadsTotal": 5}
            mock_build.return_value.users.return_value.getProfile.return_value.execute.return_value = mock_profile
            MockCreds.from_authorized_user_info.return_value = MagicMock()

            result = _test_gmail({"token": "tok"})

        assert result["email"] == "x@gmail.com"

    def test_test_calendar_returns_calendars(self):
        with (
            patch("luana_core_connections.api.google_workspace.Credentials") as MockCreds,
            patch("luana_core_connections.api.google_workspace.build") as mock_build,
        ):
            mock_build.return_value.calendarList.return_value.list.return_value.execute.return_value = {
                "items": [{"id": "primary", "summary": "My Cal", "primary": True}]
            }
            MockCreds.from_authorized_user_info.return_value = MagicMock()

            result = _test_calendar({"token": "tok"})

        assert result["calendars_found"] == 1

    def test_test_analytics_returns_accounts(self):
        with (
            patch("luana_core_connections.api.google_workspace.Credentials") as MockCreds,
            patch("luana_core_connections.api.google_workspace.build") as mock_build,
        ):
            mock_build.return_value.accountSummaries.return_value.list.return_value.execute.return_value = {
                "accountSummaries": [{"displayName": "My Account", "propertySummaries": []}]
            }
            MockCreds.from_authorized_user_info.return_value = MagicMock()

            result = _test_analytics({"token": "tok"})

        assert result["accounts_found"] == 1

    def test_test_youtube_returns_channel_info(self):
        with (
            patch("luana_core_connections.api.google_workspace.Credentials") as MockCreds,
            patch("luana_core_connections.api.google_workspace.build") as mock_build,
        ):
            MockCreds.from_authorized_user_info.return_value = MagicMock()
            mock_build.return_value.channels.return_value.list.return_value.execute.return_value = {
                "items": [
                    {
                        "id": "UCxx",
                        "snippet": {"title": "My Channel"},
                        "statistics": {"subscriberCount": "1000", "videoCount": "5"},
                    }
                ]
            }
            result = _test_youtube({"token": "tok"})

        assert result["channel_id"] == "UCxx"
