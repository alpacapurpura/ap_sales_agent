"""Tests for Google Analytics API route functions."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from luana_core_connections.api.dto.google_analytics import PropertySelectRequest
from luana_core_connections.api.google_analytics import (
    GoogleAnalyticsConfig,
    disconnect,
    get_auth_url,
    get_properties,
    get_status,
    oauth_callback,
    save_config,
    select_property,
)
from luana_core_connections.api.google_analytics import (
    test_connection as ga_test_connection,
)
from luana_core_connections.domain.enums import ChannelType

TENANT_ID = uuid4()


def _user():
    return SimpleNamespace(tenant_id=TENANT_ID, id=uuid4())


def _repo(**kwargs):
    repo = MagicMock()
    repo.db = MagicMock()
    for k, v in kwargs.items():
        setattr(repo, k, v)
    return repo


def _conn(creds=None, config=None, is_active=True):
    c = MagicMock()
    c.credentials = (
        creds if creds is not None else {"client_id": "cid", "client_secret": "csec", "refresh_token": "rtok"}
    )
    c.config = config or {}
    c.is_active = is_active
    return c


# ---------------------------------------------------------------------------
# save_config
# ---------------------------------------------------------------------------


class TestSaveConfig:
    @pytest.mark.asyncio
    async def test_updates_existing_connection(self):
        conn = _conn()
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=conn))
        cfg = GoogleAnalyticsConfig(client_id="new_cid", client_secret="new_csec")

        result = await save_config(cfg, _user(), repo)

        repo.update_credentials.assert_called_once()
        assert result == {"status": "config_saved"}

    @pytest.mark.asyncio
    async def test_creates_new_connection_when_none_exists(self):
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=None))
        cfg = GoogleAnalyticsConfig(client_id="new_cid", client_secret="new_csec")

        result = await save_config(cfg, _user(), repo)

        repo.db.add.assert_called_once()
        repo.db.commit.assert_called_once()
        assert result == {"status": "config_saved"}


# ---------------------------------------------------------------------------
# get_auth_url
# ---------------------------------------------------------------------------


class TestGetAuthUrl:
    @pytest.mark.asyncio
    async def test_raises_400_when_no_credentials(self):
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=None))
        with pytest.raises(HTTPException) as exc_info:
            await get_auth_url(_user(), repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_raises_400_when_credentials_missing_client_id(self):
        conn = _conn(creds={"client_secret": "sec"})
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=conn))
        with pytest.raises(HTTPException) as exc_info:
            await get_auth_url(_user(), repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_returns_url_and_state(self):
        conn = _conn()
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=conn))

        with patch("luana_core_connections.api.google_analytics._build_adapter") as mock_adapter:
            mock_adapter.return_value.get_authorization_url.return_value = (
                "https://accounts.google.com/auth",
                "state_xyz",
            )
            result = await get_auth_url(_user(), repo)

        assert "url" in result
        assert result["state"] == "state_xyz"


# ---------------------------------------------------------------------------
# oauth_callback
# ---------------------------------------------------------------------------


class TestOauthCallback:
    @pytest.mark.asyncio
    async def test_raises_400_when_no_connection(self):
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=None))
        with pytest.raises(HTTPException) as exc_info:
            await oauth_callback("code", _user(), repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_raises_400_on_exchange_failure(self):
        conn = _conn()
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=conn))

        with patch("luana_core_connections.api.google_analytics._build_adapter") as mock_adapter:
            mock_adapter.return_value.exchange_code.side_effect = Exception("token exchange failed")
            with pytest.raises(HTTPException) as exc_info:
                await oauth_callback("bad_code", _user(), repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_saves_credentials_and_returns_connected(self):
        conn = _conn()
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=conn))
        token_data = {"access_token": "at", "refresh_token": "rt"}

        with patch("luana_core_connections.api.google_analytics._build_adapter") as mock_adapter:
            mock_adapter.return_value.exchange_code.return_value = token_data
            mock_adapter.return_value.get_flat_properties.return_value = []
            result = await oauth_callback("good_code", _user(), repo)

        assert result.status == "connected"


# ---------------------------------------------------------------------------
# get_status
# ---------------------------------------------------------------------------


class TestGetStatus:
    @pytest.mark.asyncio
    async def test_returns_not_connected_when_no_row(self):
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=None))
        result = await get_status(_user(), repo)
        assert result.is_connected is False
        assert result.is_configured is False

    @pytest.mark.asyncio
    async def test_returns_configured_when_client_id_present(self):
        conn = _conn(creds={"client_id": "cid", "client_secret": "csec"}, is_active=False)
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=conn))
        result = await get_status(_user(), repo)
        assert result.is_configured is True
        assert result.is_connected is False

    @pytest.mark.asyncio
    async def test_returns_connected_when_refresh_token_present(self):
        conn = _conn()  # has refresh_token + is_active
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=conn))
        result = await get_status(_user(), repo)
        assert result.is_connected is True

    @pytest.mark.asyncio
    async def test_returns_selected_property_from_config(self):
        conn = _conn(config={"property_id": "properties/123", "property_display_name": "My Site"})
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=conn))
        result = await get_status(_user(), repo)
        assert result.selected_property is not None
        assert result.selected_property.property_id == "properties/123"


# ---------------------------------------------------------------------------
# get_properties
# ---------------------------------------------------------------------------


class TestGetProperties:
    @pytest.mark.asyncio
    async def test_raises_400_when_no_connection(self):
        repo = _repo(get_active=MagicMock(return_value=None))
        with pytest.raises(HTTPException) as exc_info:
            await get_properties(_user(), repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_returns_properties_list(self):
        conn = _conn()
        repo = _repo(get_active=MagicMock(return_value=conn))
        props = [{"property_id": "p/1", "account_name": "Acc", "display_name": "My Site", "account_id": "a/1"}]

        with patch("luana_core_connections.api.google_analytics._build_adapter") as mock_adapter:
            mock_adapter.return_value.get_flat_properties.return_value = props
            result = await get_properties(_user(), repo)

        assert len(result) == 1
        assert result[0].property_id == "p/1"

    @pytest.mark.asyncio
    async def test_raises_500_on_adapter_error(self):
        conn = _conn()
        repo = _repo(get_active=MagicMock(return_value=conn))

        with patch("luana_core_connections.api.google_analytics._build_adapter") as mock_adapter:
            mock_adapter.return_value.get_flat_properties.side_effect = Exception("API error")
            with pytest.raises(HTTPException) as exc_info:
                await get_properties(_user(), repo)
        assert exc_info.value.status_code == 500


# ---------------------------------------------------------------------------
# select_property
# ---------------------------------------------------------------------------


class TestSelectProperty:
    @pytest.mark.asyncio
    async def test_raises_400_when_not_connected(self):
        repo = _repo(get_active=MagicMock(return_value=None))
        body = PropertySelectRequest(property_id="properties/123")
        with pytest.raises(HTTPException) as exc_info:
            await select_property(body, _user(), repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_saves_property_and_returns_ok(self):
        conn = _conn()
        repo = _repo(get_active=MagicMock(return_value=conn))
        body = PropertySelectRequest(property_id="properties/123")

        with patch("luana_core_connections.api.google_analytics._build_adapter") as mock_adapter:
            mock_adapter.return_value.get_flat_properties.return_value = [
                {"property_id": "properties/123", "display_name": "My Site", "account_name": "Acc", "account_id": "a/1"}
            ]
            result = await select_property(body, _user(), repo)

        assert result.status == "ok"
        assert result.property_id == "properties/123"
        repo.update_credentials.assert_called_once()
        repo.update_config.assert_called_once()


# ---------------------------------------------------------------------------
# disconnect
# ---------------------------------------------------------------------------


class TestDisconnect:
    @pytest.mark.asyncio
    async def test_deactivates_connection(self):
        conn = _conn()
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=conn))
        result = await disconnect(_user(), repo)
        repo.deactivate.assert_called_once_with(conn)
        assert result == {"status": "disconnected"}

    @pytest.mark.asyncio
    async def test_returns_ok_when_no_connection(self):
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=None))
        result = await disconnect(_user(), repo)
        repo.deactivate.assert_not_called()
        assert result == {"status": "disconnected"}


# ---------------------------------------------------------------------------
# test_connection
# ---------------------------------------------------------------------------


class TestTestConnectionGA:
    @pytest.mark.asyncio
    async def test_raises_400_when_not_connected(self):
        repo = _repo(get_active=MagicMock(return_value=None))
        with pytest.raises(HTTPException) as exc_info:
            await ga_test_connection(_user(), repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_returns_ok_on_success(self):
        conn = _conn()
        repo = _repo(get_active=MagicMock(return_value=conn))
        summaries = [{"name": "acc/1", "displayName": "My Account"}]

        with patch("luana_core_connections.api.google_analytics._build_adapter") as mock_adapter:
            mock_adapter.return_value.get_account_summaries.return_value = summaries
            result = await ga_test_connection(_user(), repo)

        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_returns_error_on_exception(self):
        conn = _conn()
        repo = _repo(get_active=MagicMock(return_value=conn))

        with patch("luana_core_connections.api.google_analytics._build_adapter") as mock_adapter:
            mock_adapter.return_value.get_account_summaries.side_effect = Exception("network error")
            result = await ga_test_connection(_user(), repo)

        assert result["status"] == "error"
