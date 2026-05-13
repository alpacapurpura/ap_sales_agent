"""Tests for Meta API route functions.

Tests route logic directly (no HTTP stack) using mock user + mock repo.
Covers: configure, get_auth_url, oauth_callback, get_status, disconnect,
test_connection, get_assets, sync_assets, set_primary_asset, toggle_asset.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from luana_core_connections.api.dto.meta import MetaConfigRequest, ToggleAssetRequest
from luana_core_connections.api.meta import (
    SetPrimaryAssetRequest,
    configure,
    disconnect,
    get_assets,
    get_auth_url,
    get_status,
    oauth_callback,
    set_primary_asset,
    sync_assets,
    toggle_asset,
)
from luana_core_connections.api.meta import (
    test_connection as meta_test_connection,
)
from luana_core_connections.domain.enums import ChannelType
from luana_core_connections.infrastructure.models import ChannelConnectionModel

TENANT_ID = uuid4()


def _user(tenant_id=None):
    u = SimpleNamespace(tenant_id=tenant_id or TENANT_ID, id=uuid4())
    return u


def _repo(**kwargs):
    repo = MagicMock()
    for k, v in kwargs.items():
        setattr(repo, k, v)
    return repo


def _conn(channel_type=ChannelType.META.value, creds=None, config=None, is_active=True):
    c = MagicMock(spec=ChannelConnectionModel)
    c.channel_type = channel_type
    # Use None sentinel to differentiate "no creds" from "explicit empty creds"
    c.credentials = {"access_token": "tok"} if creds is None else creds
    c.config = config or {}
    c.is_active = is_active
    c.id = uuid4()
    return c


# ---------------------------------------------------------------------------
# configure
# ---------------------------------------------------------------------------


class TestConfigure:
    @pytest.mark.asyncio
    async def test_updates_existing_connection_credentials(self):
        existing = _conn()
        existing.credentials = {}
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=existing))
        data = MetaConfigRequest(app_id="app_123", app_secret="sec_456")

        result = await configure(data, _user(), repo)

        repo.update_credentials.assert_called_once()
        assert result == {"status": "config_saved"}

    @pytest.mark.asyncio
    async def test_creates_new_connection_when_none_exists(self):
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=None))
        repo.db = MagicMock()
        data = MetaConfigRequest(app_id="app_new", app_secret="sec_new")

        result = await configure(data, _user(), repo)

        repo.db.add.assert_called_once()
        repo.db.commit.assert_called_once()
        assert result == {"status": "config_saved"}


# ---------------------------------------------------------------------------
# get_auth_url
# ---------------------------------------------------------------------------


class TestGetAuthUrl:
    @pytest.mark.asyncio
    async def test_raises_400_without_redirect_uri(self):
        with pytest.raises(HTTPException) as exc_info:
            await get_auth_url(_user(), redirect_uri=None)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_raises_500_when_meta_not_configured(self):
        with patch("luana_core_connections.api.meta.settings") as mock_settings:
            mock_settings.META_APP_ID = None
            mock_settings.META_APP_SECRET = None
            with pytest.raises(HTTPException) as exc_info:
                await get_auth_url(_user(), redirect_uri="https://example.com/callback")
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_returns_url_and_state(self):
        with (
            patch("luana_core_connections.api.meta.settings") as mock_settings,
            patch("luana_core_connections.api.meta.MetaAdapter") as MockAdapter,
        ):
            mock_settings.META_APP_ID = "app_id"
            mock_settings.META_APP_SECRET = "app_secret"
            MockAdapter.return_value.get_authorization_url.return_value = ("https://facebook.com/oauth", "state_xyz")
            result = await get_auth_url(_user(), redirect_uri="https://example.com/cb")

        assert "url" in result
        assert "state" in result


# ---------------------------------------------------------------------------
# oauth_callback
# ---------------------------------------------------------------------------


class TestOauthCallback:
    @pytest.mark.asyncio
    async def test_raises_400_on_exchange_failure(self):
        repo = _repo()
        with patch("luana_core_connections.api.meta.MetaAdapter") as MockAdapter:
            MockAdapter.return_value.exchange_code = AsyncMock(side_effect=Exception("fail"))
            with pytest.raises(HTTPException) as exc_info:
                await oauth_callback("bad_code", "https://cb.example.com", _user(), repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_successful_callback_saves_connection(self):
        repo = _repo(
            get_by_tenant_and_type=MagicMock(return_value=None),
            upsert=MagicMock(return_value=_conn()),
        )
        repo.db = MagicMock()

        creds_data = {"access_token": "tok123"}
        profile_data = {"id": "meta_user_1", "name": "Test User"}

        with (
            patch("luana_core_connections.api.meta.MetaAdapter") as MockAdapter,
            patch("luana_core_connections.api.meta._sync_assets_for_tenant", new_callable=AsyncMock) as mock_sync,
        ):
            MockAdapter.return_value.exchange_code = AsyncMock(return_value=creds_data)
            MockAdapter.return_value.get_user_profile = AsyncMock(return_value=profile_data)
            mock_sync.return_value = ({}, [])

            result = await oauth_callback("code_ok", "https://cb.example.com", _user(), repo)

        assert result.get("status") == "ok" or "connected" in str(result)


# ---------------------------------------------------------------------------
# get_status
# ---------------------------------------------------------------------------


class TestGetStatus:
    @pytest.mark.asyncio
    async def test_returns_not_connected_when_no_connection(self):
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=None))
        with patch("luana_core_connections.api.meta.settings") as mock_settings:
            mock_settings.META_APP_ID = "app"
            mock_settings.META_APP_SECRET = "sec"
            result = await get_status(_user(), repo)
        assert result["is_connected"] is False

    @pytest.mark.asyncio
    async def test_returns_connected_with_valid_token(self):
        conn = _conn(creds={"access_token": "valid_tok"}, config={"name": "My Page"})
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=conn))
        with patch("luana_core_connections.api.meta.settings") as mock_settings:
            mock_settings.META_APP_ID = "app"
            mock_settings.META_APP_SECRET = "sec"
            result = await get_status(_user(), repo)
        assert result["is_connected"] is True

    @pytest.mark.asyncio
    async def test_debug_flag_adds_diagnostic_info(self):
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=None))
        with patch("luana_core_connections.api.meta.settings") as mock_settings:
            mock_settings.META_APP_ID = "app"
            mock_settings.META_APP_SECRET = "sec"
            result = await get_status(_user(), repo, debug=True)
        assert "debug" in result

    @pytest.mark.asyncio
    async def test_inactive_connection_returns_not_connected(self):
        conn = _conn(creds={"access_token": "tok"}, is_active=False)
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=conn))
        with patch("luana_core_connections.api.meta.settings") as mock_settings:
            mock_settings.META_APP_ID = "app"
            mock_settings.META_APP_SECRET = "sec"
            result = await get_status(_user(), repo)
        assert result["is_connected"] is False


# ---------------------------------------------------------------------------
# disconnect
# ---------------------------------------------------------------------------


class TestDisconnect:
    @pytest.mark.asyncio
    async def test_deactivates_master_and_assets(self):
        master = _conn()
        child1 = _conn(channel_type=ChannelType.FACEBOOK_PAGE.value)
        child2 = _conn(channel_type=ChannelType.INSTAGRAM_ACCOUNT.value)
        repo = _repo(
            get_by_tenant_and_type=MagicMock(return_value=master),
            get_all_by_tenant_and_types=MagicMock(return_value=[child1, child2]),
        )

        result = await disconnect(_user(), repo)

        assert repo.deactivate.call_count == 3  # 2 children + 1 master
        assert result == {"status": "disconnected"}

    @pytest.mark.asyncio
    async def test_disconnect_returns_ok_when_no_connection(self):
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=None))
        result = await disconnect(_user(), repo)
        assert result == {"status": "disconnected"}


# ---------------------------------------------------------------------------
# test_connection
# ---------------------------------------------------------------------------


class TestTestConnection:
    @pytest.mark.asyncio
    async def test_raises_400_when_no_connection(self):
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=None))
        with pytest.raises(HTTPException) as exc_info:
            await meta_test_connection(_user(), repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_raises_400_when_no_access_token(self):
        conn = _conn(creds={})
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=conn))
        with pytest.raises(HTTPException) as exc_info:
            await meta_test_connection(_user(), repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_returns_ok_on_valid_token(self):
        conn = _conn(creds={"access_token": "valid"})
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=conn))
        profile = {"id": "123", "name": "Test"}
        with patch("luana_core_connections.api.meta.MetaAdapter") as MockAdapter:
            MockAdapter.return_value.get_user_profile = AsyncMock(return_value=profile)
            result = await meta_test_connection(_user(), repo)
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_returns_error_on_adapter_exception(self):
        conn = _conn(creds={"access_token": "tok"})
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=conn))
        with patch("luana_core_connections.api.meta.MetaAdapter") as MockAdapter:
            MockAdapter.return_value.get_user_profile = AsyncMock(side_effect=Exception("network err"))
            result = await meta_test_connection(_user(), repo)
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# get_assets
# ---------------------------------------------------------------------------


class TestGetAssets:
    @pytest.mark.asyncio
    async def test_returns_empty_assets_when_none(self):
        repo = _repo(get_all_by_tenant_and_types=MagicMock(return_value=[]))
        result = await get_assets(_user(), repo)
        assert result.pages == []
        assert result.instagram_accounts == []
        assert result.ads_accounts == []

    @pytest.mark.asyncio
    async def test_groups_assets_by_type(self):
        page_cfg = {"asset_id": "p1", "page_name": "My Page"}
        page = MagicMock(spec=ChannelConnectionModel)
        page.channel_type = ChannelType.FACEBOOK_PAGE.value
        page.config = page_cfg
        page.credentials = {"access_token": "tok"}
        page.is_active = True

        ig_cfg = {"asset_id": "ig1", "ig_username": "mypage"}
        ig = MagicMock(spec=ChannelConnectionModel)
        ig.channel_type = ChannelType.INSTAGRAM_ACCOUNT.value
        ig.config = ig_cfg
        ig.credentials = {}
        ig.is_active = True

        repo = _repo(get_all_by_tenant_and_types=MagicMock(return_value=[page, ig]))
        result = await get_assets(_user(), repo)
        assert len(result.pages) == 1
        assert len(result.instagram_accounts) == 1


# ---------------------------------------------------------------------------
# set_primary_asset
# ---------------------------------------------------------------------------


class TestSetPrimaryAsset:
    @pytest.mark.asyncio
    async def test_raises_400_for_invalid_asset_type(self):
        repo = _repo()
        body = SetPrimaryAssetRequest(asset_type="invalid_type", asset_id="123")
        with pytest.raises(HTTPException) as exc_info:
            await set_primary_asset(body, _user(), repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_raises_404_when_no_meta_master(self):
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=None))
        body = SetPrimaryAssetRequest(asset_type="facebook_page", asset_id="p1")
        with pytest.raises(HTTPException) as exc_info:
            await set_primary_asset(body, _user(), repo)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_updates_primary_page_and_returns_status(self):
        master = _conn(config={"primary_page_id": None})
        repo = _repo(
            get_by_tenant_and_type=MagicMock(return_value=master),
            get_all_by_tenant_and_types=MagicMock(return_value=[]),
        )
        body = SetPrimaryAssetRequest(asset_type="facebook_page", asset_id="page_x")
        result = await set_primary_asset(body, _user(), repo)
        assert result["status"] == "primary_set"
        assert result["asset_id"] == "page_x"


# ---------------------------------------------------------------------------
# sync_assets
# ---------------------------------------------------------------------------


class TestSyncAssets:
    @pytest.mark.asyncio
    async def test_raises_400_when_not_connected(self):
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=None))
        with pytest.raises(HTTPException) as exc_info:
            await sync_assets(_user(), repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_raises_400_when_no_access_token(self):
        conn = _conn(creds={})
        repo = _repo(
            get_by_tenant_and_type=MagicMock(return_value=conn),
            get_all_by_tenant_and_types=MagicMock(return_value=[]),
        )
        with pytest.raises(HTTPException) as exc_info:
            await sync_assets(_user(), repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_returns_assets_on_success(self):
        conn = _conn(creds={"access_token": "tok"})
        repo = _repo(
            get_by_tenant_and_type=MagicMock(return_value=conn),
            get_all_by_tenant_and_types=MagicMock(return_value=[]),
        )
        with patch("luana_core_connections.api.meta._sync_assets_for_tenant", new_callable=AsyncMock) as mock_sync:
            mock_sync.return_value = ({}, [])
            result = await sync_assets(_user(), repo)
        assert hasattr(result, "pages")


# ---------------------------------------------------------------------------
# toggle_asset
# ---------------------------------------------------------------------------


class TestToggleAsset:
    @pytest.mark.asyncio
    async def test_raises_400_for_invalid_channel_type(self):
        repo = _repo()
        body = ToggleAssetRequest(is_active=True)
        with pytest.raises(HTTPException) as exc_info:
            await toggle_asset("invalid_type", "missing_id", body, _user(), repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_raises_404_when_asset_not_found(self):
        repo = _repo(get_by_asset_id=MagicMock(return_value=None))
        body = ToggleAssetRequest(is_active=True)
        with pytest.raises(HTTPException) as exc_info:
            await toggle_asset(ChannelType.FACEBOOK_PAGE.value, "missing_id", body, _user(), repo)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_activates_asset(self):
        asset = _conn(channel_type=ChannelType.FACEBOOK_PAGE.value, is_active=False)
        master = _conn()
        repo = _repo(
            get_by_asset_id=MagicMock(return_value=asset),
            get_by_tenant_and_type=MagicMock(return_value=master),
            get_all_by_tenant_and_types=MagicMock(return_value=[]),
        )
        body = ToggleAssetRequest(is_active=True)
        result = await toggle_asset(ChannelType.FACEBOOK_PAGE.value, "p1", body, _user(), repo)
        repo.activate.assert_called_once_with(asset)
        assert result["status"] == "updated"

    @pytest.mark.asyncio
    async def test_deactivates_asset(self):
        asset = _conn(channel_type=ChannelType.FACEBOOK_PAGE.value, is_active=True)
        master = _conn()
        repo = _repo(
            get_by_asset_id=MagicMock(return_value=asset),
            get_by_tenant_and_type=MagicMock(return_value=master),
            get_all_by_tenant_and_types=MagicMock(return_value=[]),
        )
        body = ToggleAssetRequest(is_active=False)
        result = await toggle_asset(ChannelType.FACEBOOK_PAGE.value, "p1", body, _user(), repo)
        repo.deactivate.assert_called_once_with(asset)
        assert result["status"] == "updated"
