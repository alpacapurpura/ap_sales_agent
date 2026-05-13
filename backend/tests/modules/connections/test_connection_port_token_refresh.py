"""Tests for ConnectionPortImpl token refresh logic.

Covers: expiry detection, Meta token refresh, Google token refresh,
credential aliasing, child-provider resolution, list_active_connections.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from luana_core_connections.application.services.connection_port_impl import (
    CHILD_PROVIDER_PARENT,
    EXPIRY_BUFFER_SECONDS,
    PROVIDER_TO_CHANNEL_TYPE_ALIAS,
    ConnectionPortImpl,
)
from luana_core_connections.domain.enums import ChannelType
from luana_core_platform.domain.ports import ConnectionRevokedError, TokenRefreshError

TENANT_ID = uuid4()


def _make_conn(channel_type: str, credentials: dict, config: dict | None = None, is_active: bool = True) -> MagicMock:
    conn = MagicMock()
    conn.channel_type = channel_type
    conn.credentials = credentials
    conn.config = config or {}
    conn.is_active = is_active
    return conn


def _port() -> ConnectionPortImpl:
    return ConnectionPortImpl(MagicMock())


# ---------------------------------------------------------------------------
# _is_token_expired
# ---------------------------------------------------------------------------


class TestIsTokenExpired:
    def test_no_expires_at_not_expired(self):
        port = _port()
        assert port._is_token_expired({}) is False

    def test_future_expiry_not_expired(self):
        port = _port()
        future = datetime.now(UTC) + timedelta(hours=1)
        assert port._is_token_expired({"expires_at": future.isoformat()}) is False

    def test_past_expiry_is_expired(self):
        port = _port()
        past = datetime.now(UTC) - timedelta(hours=1)
        assert port._is_token_expired({"expires_at": past.isoformat()}) is True

    def test_within_buffer_is_expired(self):
        port = _port()
        # expires in 1 second — inside 300s buffer
        soon = datetime.now(UTC) + timedelta(seconds=1)
        assert port._is_token_expired({"expires_at": soon.isoformat()}) is True

    def test_outside_buffer_not_expired(self):
        port = _port()
        outside = datetime.now(UTC) + timedelta(seconds=EXPIRY_BUFFER_SECONDS + 60)
        assert port._is_token_expired({"expires_at": outside.isoformat()}) is False

    def test_naive_datetime_treated_as_utc(self):
        port = _port()
        past_naive = (datetime.now(UTC) - timedelta(hours=1)).replace(tzinfo=None)
        assert port._is_token_expired({"expires_at": past_naive.isoformat()}) is True

    def test_invalid_expires_at_not_expired(self):
        port = _port()
        assert port._is_token_expired({"expires_at": "not-a-date"}) is False


# ---------------------------------------------------------------------------
# get_credentials — happy path (no refresh needed)
# ---------------------------------------------------------------------------


class TestGetCredentialsValid:
    @pytest.mark.asyncio
    async def test_returns_credentials_when_valid(self):
        port = _port()
        future = datetime.now(UTC) + timedelta(hours=2)
        conn = _make_conn("meta", {"access_token": "tok", "expires_at": future.isoformat()})

        with patch.object(port.repo, "get_active", return_value=conn):
            result = await port.get_credentials(TENANT_ID, "meta")

        assert result.credentials["access_token"] == "tok"
        assert result.channel_type == "meta"

    @pytest.mark.asyncio
    async def test_unknown_channel_type_raises_revoked(self):
        port = _port()
        with pytest.raises(ConnectionRevokedError):
            await port.get_credentials(TENANT_ID, "totally_unknown_provider")

    @pytest.mark.asyncio
    async def test_no_active_connection_raises_revoked(self):
        port = _port()
        with (
            patch.object(port.repo, "get_active", return_value=None),
            pytest.raises(ConnectionRevokedError, match="No active connection"),
        ):
            await port.get_credentials(TENANT_ID, "meta")

    @pytest.mark.asyncio
    async def test_search_console_alias_resolves_to_google_analytics(self):
        port = _port()
        conn = _make_conn("google_analytics", {"access_token": "gtok"})
        with patch.object(port.repo, "get_active", return_value=conn):
            result = await port.get_credentials(TENANT_ID, "search_console")
        assert result.credentials["access_token"] == "gtok"


# ---------------------------------------------------------------------------
# get_credentials — token refresh path
# ---------------------------------------------------------------------------


class TestGetCredentialsTriggerRefresh:
    @pytest.mark.asyncio
    async def test_meta_token_refreshed_on_expiry(self):
        port = _port()
        past = datetime.now(UTC) - timedelta(hours=1)
        conn = _make_conn(
            "meta",
            {"access_token": "old", "expires_at": past.isoformat()},
            config={"app_id": "123", "app_secret": "secret"},
        )

        new_token_response = {"access_token": "new_tok", "expires_in": 5184000}

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = new_token_response

        with (
            patch.object(port.repo, "get_active", return_value=conn),
            patch.object(port.repo, "update_credentials") as mock_update,
            patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response),
        ):
            result = await port.get_credentials(TENANT_ID, "meta")

        assert result.credentials["access_token"] == "new_tok"
        mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_google_token_refreshed_on_expiry(self):
        port = _port()
        past = datetime.now(UTC) - timedelta(hours=1)
        conn = _make_conn(
            "google_analytics",
            {
                "access_token": "old",
                "refresh_token": "refresh_tok",
                "client_id": "cid",
                "client_secret": "csec",
                "expires_at": past.isoformat(),
            },
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "new_g_tok", "expires_in": 3600}

        with (
            patch.object(port.repo, "get_active", return_value=conn),
            patch.object(port.repo, "update_credentials"),
            patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response),
        ):
            result = await port.get_credentials(TENANT_ID, "google_analytics")

        assert result.credentials["access_token"] == "new_g_tok"

    @pytest.mark.asyncio
    async def test_meta_refresh_http_error_raises_token_refresh_error(self):
        port = _port()
        past = datetime.now(UTC) - timedelta(hours=1)
        conn = _make_conn(
            "meta",
            {"access_token": "old", "expires_at": past.isoformat()},
        )

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "invalid token"

        with (
            patch.object(port.repo, "get_active", return_value=conn),
            patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response),
            pytest.raises(TokenRefreshError),
        ):
            await port.get_credentials(TENANT_ID, "meta")

    @pytest.mark.asyncio
    async def test_google_refresh_http_error_raises_token_refresh_error(self):
        port = _port()
        past = datetime.now(UTC) - timedelta(hours=1)
        conn = _make_conn(
            "google_analytics",
            {
                "access_token": "old",
                "refresh_token": "rtok",
                "client_id": "cid",
                "client_secret": "csec",
                "expires_at": past.isoformat(),
            },
        )

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "invalid_grant"

        with (
            patch.object(port.repo, "get_active", return_value=conn),
            patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response),
            pytest.raises(TokenRefreshError),
        ):
            await port.get_credentials(TENANT_ID, "google_analytics")

    @pytest.mark.asyncio
    async def test_meta_no_access_token_raises_token_refresh_error(self):
        port = _port()
        past = datetime.now(UTC) - timedelta(hours=1)
        conn = _make_conn("meta", {"expires_at": past.isoformat()})

        with patch.object(port.repo, "get_active", return_value=conn), pytest.raises(TokenRefreshError):
            await port.get_credentials(TENANT_ID, "meta")

    @pytest.mark.asyncio
    async def test_google_no_refresh_token_raises_token_refresh_error(self):
        port = _port()
        past = datetime.now(UTC) - timedelta(hours=1)
        conn = _make_conn(
            "google_analytics",
            {"access_token": "tok", "expires_at": past.isoformat()},
        )

        with patch.object(port.repo, "get_active", return_value=conn), pytest.raises(TokenRefreshError):
            await port.get_credentials(TENANT_ID, "google_analytics")

    @pytest.mark.asyncio
    async def test_unsupported_channel_type_raises_token_refresh_error(self):
        port = _port()
        past = datetime.now(UTC) - timedelta(hours=1)
        conn = _make_conn("shopify", {"access_token": "tok", "expires_at": past.isoformat()})

        with (
            patch.object(port.repo, "get_active", return_value=conn),
            pytest.raises(TokenRefreshError, match="not implemented"),
        ):
            await port.get_credentials(TENANT_ID, "shopify")


# ---------------------------------------------------------------------------
# _get_child_credentials (meta_pixel → meta)
# ---------------------------------------------------------------------------


class TestChildCredentials:
    @pytest.mark.asyncio
    async def test_meta_pixel_uses_meta_parent_token(self):
        port = _port()
        future = datetime.now(UTC) + timedelta(hours=2)
        meta_conn = _make_conn("meta", {"access_token": "meta_tok", "expires_at": future.isoformat()})
        pixel_conn = _make_conn("meta_pixel", {}, config={"asset_id": "pix_123"})

        def fake_get_active(tenant_id, channel_enum):
            if channel_enum == ChannelType.META:
                return meta_conn
            if channel_enum == ChannelType.META_PIXEL:
                return pixel_conn
            return None

        with patch.object(port.repo, "get_active", side_effect=fake_get_active):
            result = await port.get_credentials(TENANT_ID, "meta_pixel")

        assert result.credentials["access_token"] == "meta_tok"
        assert result.config["asset_id"] == "pix_123"
        assert result.channel_type == "meta_pixel"

    @pytest.mark.asyncio
    async def test_child_no_connection_raises_revoked(self):
        port = _port()
        with patch.object(port.repo, "get_active", return_value=None), pytest.raises(ConnectionRevokedError):
            await port.get_credentials(TENANT_ID, "meta_pixel")

    def test_child_provider_parent_map_has_meta_pixel(self):
        assert "meta_pixel" in CHILD_PROVIDER_PARENT
        assert CHILD_PROVIDER_PARENT["meta_pixel"] == "meta"


# ---------------------------------------------------------------------------
# list_active_connections
# ---------------------------------------------------------------------------


class TestListActiveConnections:
    @pytest.mark.asyncio
    async def test_returns_only_active_connections(self):
        port = _port()
        active = _make_conn("meta", {"access_token": "tok"}, is_active=True)
        inactive = _make_conn("shopify", {"access_token": "tok2"}, is_active=False)

        with patch.object(port.repo, "get_all_by_tenant", return_value=[active, inactive]):
            results = await port.list_active_connections(TENANT_ID)

        assert len(results) == 1
        assert results[0].channel_type == "meta"

    @pytest.mark.asyncio
    async def test_empty_tenant_returns_empty_list(self):
        port = _port()
        with patch.object(port.repo, "get_all_by_tenant", return_value=[]):
            results = await port.list_active_connections(TENANT_ID)
        assert results == []

    @pytest.mark.asyncio
    async def test_credentials_and_config_mapped_correctly(self):
        port = _port()
        conn = _make_conn("telegram", {"bot_token": "btoken"}, config={"chat_id": "123"}, is_active=True)
        with patch.object(port.repo, "get_all_by_tenant", return_value=[conn]):
            results = await port.list_active_connections(TENANT_ID)
        assert results[0].credentials["bot_token"] == "btoken"
        assert results[0].config["chat_id"] == "123"
