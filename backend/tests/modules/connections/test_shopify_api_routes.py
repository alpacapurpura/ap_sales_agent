"""Tests for Shopify API routes."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from luana_core_connections.api.shopify import (
    ShopifyAuthUrlRequest,
    ShopifyExchangeRequest,
    _resolve_tenant_id,
    auth_callback,
    disconnect_shopify,
    exchange_shopify_token,
    generate_auth_url,
    get_shopify_status,
    quick_connect_shopify,
)
from luana_core_connections.api.shopify import (
    test_shopify_connection as shopify_test_connection,
)

TENANT_ID = uuid.uuid4()


def _user(tenant_id=None):
    u = MagicMock()
    u.tenant_id = tenant_id or TENANT_ID
    return u


def _repo():
    return MagicMock()


def _conn(config=None, credentials=None):
    c = MagicMock()
    c.config = {"shop_url": "https://test.myshopify.com"} if config is None else config
    c.credentials = {"access_token": "token123"} if credentials is None else credentials
    c.tenant_id = TENANT_ID
    return c


# ---------------------------------------------------------------------------
# _resolve_tenant_id
# ---------------------------------------------------------------------------


class TestResolveTenantId:
    def test_returns_uuid_from_valid_state(self):
        repo = _repo()
        tid = uuid.uuid4()
        result = _resolve_tenant_id(repo, "test.myshopify.com", str(tid))
        assert result == tid

    def test_raises_400_on_invalid_state_uuid(self):
        from fastapi import HTTPException

        repo = _repo()
        with pytest.raises(HTTPException) as exc_info:
            _resolve_tenant_id(repo, "test.myshopify.com", "not-a-uuid")
        assert exc_info.value.status_code == 400

    def test_falls_back_to_shop_lookup_when_no_state(self):
        repo = _repo()
        conn = _conn()
        repo.get_active_shopify_by_shop.return_value = conn
        result = _resolve_tenant_id(repo, "test.myshopify.com", None)
        assert result == TENANT_ID

    def test_raises_400_when_shop_not_found(self):
        from fastapi import HTTPException

        repo = _repo()
        repo.get_active_shopify_by_shop.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            _resolve_tenant_id(repo, "unknown.myshopify.com", None)
        assert exc_info.value.status_code == 400


# ---------------------------------------------------------------------------
# get_shopify_status
# ---------------------------------------------------------------------------


class TestGetShopifyStatus:
    @pytest.mark.asyncio
    async def test_not_connected_when_no_active_connection(self):
        repo = _repo()
        repo.get_active.return_value = None
        result = await get_shopify_status(_user(), repo)
        assert result.is_connected is False

    @pytest.mark.asyncio
    async def test_connected_returns_shop_url_and_info(self):
        repo = _repo()
        conn = _conn(config={"shop_url": "https://mystore.myshopify.com", "shop_info": {"name": "My Store"}})
        repo.get_active.return_value = conn
        result = await get_shopify_status(_user(), repo)
        assert result.is_connected is True
        assert result.shop_url == "https://mystore.myshopify.com"
        assert result.shop_info == {"name": "My Store"}

    @pytest.mark.asyncio
    async def test_connected_with_no_shop_info(self):
        repo = _repo()
        conn = _conn(config={"shop_url": "https://mystore.myshopify.com"})
        repo.get_active.return_value = conn
        result = await get_shopify_status(_user(), repo)
        assert result.is_connected is True
        assert result.shop_info is None


# ---------------------------------------------------------------------------
# generate_auth_url
# ---------------------------------------------------------------------------


class TestGenerateAuthUrl:
    @pytest.mark.asyncio
    async def test_returns_auth_url(self):
        user = _user()
        req = ShopifyAuthUrlRequest(shop_url="mystore.myshopify.com")

        with (
            patch("luana_core_connections.api.shopify.settings") as mock_settings,
            patch(
                "luana_core_connections.api.shopify.ShopifyConnector.get_auth_url",
                return_value="https://mystore.myshopify.com/admin/oauth/authorize?...",
            ) as mock_get,
        ):
            mock_settings.DASHBOARD_DOMAIN = "https://app.nicolify.com"
            result = await generate_auth_url(req, user)

        assert "auth_url" in result
        mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_converts_http_to_https_in_redirect_uri(self):
        user = _user()
        req = ShopifyAuthUrlRequest(shop_url="mystore.myshopify.com")

        captured_args = {}

        def _capture_get_auth_url(shop_domain, state, redirect_uri):
            captured_args["redirect_uri"] = redirect_uri
            return "https://shopify.com/auth"

        with (
            patch("luana_core_connections.api.shopify.settings") as mock_settings,
            patch(
                "luana_core_connections.api.shopify.ShopifyConnector.get_auth_url", side_effect=_capture_get_auth_url
            ),
        ):
            mock_settings.DASHBOARD_DOMAIN = "http://localhost:3000"
            await generate_auth_url(req, user)

        assert captured_args["redirect_uri"].startswith("https://")


# ---------------------------------------------------------------------------
# exchange_shopify_token
# ---------------------------------------------------------------------------


class TestExchangeShopifyToken:
    @pytest.mark.asyncio
    async def test_raises_400_on_invalid_hmac(self):
        from fastapi import HTTPException

        repo = _repo()
        req = ShopifyExchangeRequest(code="code1", shop="test.myshopify.com", hmac="bad")

        with (
            patch("luana_core_connections.api.shopify.ShopifyConnector.verify_hmac", return_value=False),
            pytest.raises(HTTPException) as exc_info,
        ):
            await exchange_shopify_token(req, repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_raises_400_on_token_exchange_error(self):
        from fastapi import HTTPException

        repo = _repo()
        repo.get_active_shopify_by_shop.return_value = None
        req = ShopifyExchangeRequest(code="code1", shop="test.myshopify.com", hmac="sig", state=str(TENANT_ID))

        with (
            patch("luana_core_connections.api.shopify.ShopifyConnector.verify_hmac", return_value=True),
            patch(
                "luana_core_connections.api.shopify.ShopifyConnector.exchange_token",
                new_callable=AsyncMock,
                return_value=(None, "token error"),
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            await exchange_shopify_token(req, repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_raises_400_on_verify_connection_failure(self):
        from fastapi import HTTPException

        repo = _repo()
        req = ShopifyExchangeRequest(code="code1", shop="test.myshopify.com", hmac="sig", state=str(TENANT_ID))

        with (
            patch("luana_core_connections.api.shopify.ShopifyConnector.verify_hmac", return_value=True),
            patch(
                "luana_core_connections.api.shopify.ShopifyConnector.exchange_token",
                new_callable=AsyncMock,
                return_value=("token", None),
            ),
            patch(
                "luana_core_connections.api.shopify.ShopifyConnector.verify_connection",
                new_callable=AsyncMock,
                return_value=(False, {}),
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            await exchange_shopify_token(req, repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_successful_exchange_upserts_and_returns_connected(self):
        repo = _repo()
        shop_details = {"name": "Test Store"}
        req = ShopifyExchangeRequest(code="code1", shop="test.myshopify.com", hmac="sig", state=str(TENANT_ID))

        with (
            patch("luana_core_connections.api.shopify.ShopifyConnector.verify_hmac", return_value=True),
            patch(
                "luana_core_connections.api.shopify.ShopifyConnector.exchange_token",
                new_callable=AsyncMock,
                return_value=("access_token", None),
            ),
            patch(
                "luana_core_connections.api.shopify.ShopifyConnector.verify_connection",
                new_callable=AsyncMock,
                return_value=(True, shop_details),
            ),
        ):
            result = await exchange_shopify_token(req, repo)

        assert result.status == "connected"
        repo.upsert.assert_called_once()


# ---------------------------------------------------------------------------
# auth_callback
# ---------------------------------------------------------------------------


class TestAuthCallback:
    def _make_request(self, params: dict):
        req = MagicMock()
        req.query_params = params
        return req

    @pytest.mark.asyncio
    async def test_raises_400_on_invalid_hmac(self):
        from fastapi import HTTPException

        repo = _repo()
        request = self._make_request({"shop": "s.myshopify.com", "code": "c", "hmac": "bad"})

        with (
            patch("luana_core_connections.api.shopify.ShopifyConnector.verify_hmac", return_value=False),
            pytest.raises(HTTPException) as exc_info,
        ):
            await auth_callback(request, repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_raises_400_when_missing_shop_or_code(self):
        from fastapi import HTTPException

        repo = _repo()
        request = self._make_request({"hmac": "sig"})

        with (
            patch("luana_core_connections.api.shopify.ShopifyConnector.verify_hmac", return_value=True),
            pytest.raises(HTTPException) as exc_info,
        ):
            await auth_callback(request, repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_successful_callback_redirects(self):
        from fastapi.responses import RedirectResponse

        repo = _repo()
        request = self._make_request(
            {"shop": "s.myshopify.com", "code": "code", "hmac": "sig", "state": str(TENANT_ID)}
        )

        with (
            patch("luana_core_connections.api.shopify.ShopifyConnector.verify_hmac", return_value=True),
            patch(
                "luana_core_connections.api.shopify.ShopifyConnector.exchange_token",
                new_callable=AsyncMock,
                return_value=("token", None),
            ),
            patch(
                "luana_core_connections.api.shopify.ShopifyConnector.verify_connection",
                new_callable=AsyncMock,
                return_value=(True, {"name": "Store"}),
            ),
            patch("luana_core_connections.api.shopify.settings") as mock_settings,
        ):
            mock_settings.DASHBOARD_DOMAIN = "https://app.nicolify.com"
            result = await auth_callback(request, repo)

        assert isinstance(result, RedirectResponse)

    @pytest.mark.asyncio
    async def test_raises_500_when_dashboard_domain_not_configured(self):
        from fastapi import HTTPException

        repo = _repo()
        request = self._make_request(
            {"shop": "s.myshopify.com", "code": "code", "hmac": "sig", "state": str(TENANT_ID)}
        )

        with (
            patch("luana_core_connections.api.shopify.ShopifyConnector.verify_hmac", return_value=True),
            patch(
                "luana_core_connections.api.shopify.ShopifyConnector.exchange_token",
                new_callable=AsyncMock,
                return_value=("token", None),
            ),
            patch(
                "luana_core_connections.api.shopify.ShopifyConnector.verify_connection",
                new_callable=AsyncMock,
                return_value=(True, {}),
            ),
            patch("luana_core_connections.api.shopify.settings") as mock_settings,
            pytest.raises(HTTPException) as exc_info,
        ):
            mock_settings.DASHBOARD_DOMAIN = None
            await auth_callback(request, repo)
        assert exc_info.value.status_code == 500


# ---------------------------------------------------------------------------
# quick_connect_shopify
# ---------------------------------------------------------------------------


class TestQuickConnectShopify:
    @pytest.mark.asyncio
    async def test_normalizes_shop_url(self):
        repo = _repo()
        user = _user()
        req = ShopifyAuthUrlRequest(shop_url="mystore")

        with (
            patch(
                "luana_core_connections.api.shopify.ShopifyConnector.client_credentials_token",
                new_callable=AsyncMock,
                return_value=("token", None),
            ),
            patch(
                "luana_core_connections.api.shopify.ShopifyConnector.verify_connection",
                new_callable=AsyncMock,
                return_value=(True, {}),
            ),
        ):
            result = await quick_connect_shopify(req, user, repo)

        assert result.status == "connected"
        repo.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_400_on_client_credentials_error(self):
        from fastapi import HTTPException

        repo = _repo()
        user = _user()
        req = ShopifyAuthUrlRequest(shop_url="mystore.myshopify.com")

        with (
            patch(
                "luana_core_connections.api.shopify.ShopifyConnector.client_credentials_token",
                new_callable=AsyncMock,
                return_value=(None, "auth error"),
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            await quick_connect_shopify(req, user, repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_raises_400_when_verify_fails(self):
        from fastapi import HTTPException

        repo = _repo()
        user = _user()
        req = ShopifyAuthUrlRequest(shop_url="mystore.myshopify.com")

        with (
            patch(
                "luana_core_connections.api.shopify.ShopifyConnector.client_credentials_token",
                new_callable=AsyncMock,
                return_value=("token", None),
            ),
            patch(
                "luana_core_connections.api.shopify.ShopifyConnector.verify_connection",
                new_callable=AsyncMock,
                return_value=(False, {}),
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            await quick_connect_shopify(req, user, repo)
        assert exc_info.value.status_code == 400


# ---------------------------------------------------------------------------
# disconnect_shopify
# ---------------------------------------------------------------------------


class TestDisconnectShopify:
    @pytest.mark.asyncio
    async def test_raises_404_when_no_connection(self):
        from fastapi import HTTPException

        repo = _repo()
        repo.get_by_tenant_and_type.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            await disconnect_shopify(_user(), repo)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_deactivates_connection(self):
        repo = _repo()
        conn = _conn()
        repo.get_by_tenant_and_type.return_value = conn
        result = await disconnect_shopify(_user(), repo)
        repo.deactivate.assert_called_once_with(conn)
        assert result.status == "disconnected"


# ---------------------------------------------------------------------------
# test_shopify_connection
# ---------------------------------------------------------------------------


class TestTestShopifyConnection:
    @pytest.mark.asyncio
    async def test_raises_404_when_no_active_connection(self):
        from fastapi import HTTPException

        repo = _repo()
        repo.get_active.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            await shopify_test_connection(_user(), repo)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_400_when_missing_credentials(self):
        from fastapi import HTTPException

        repo = _repo()
        conn = _conn(config={}, credentials={})
        repo.get_active.return_value = conn
        with pytest.raises(HTTPException) as exc_info:
            await shopify_test_connection(_user(), repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_returns_active_when_valid(self):
        repo = _repo()
        conn = _conn()
        repo.get_active.return_value = conn

        with patch(
            "luana_core_connections.api.shopify.ShopifyConnector.verify_connection",
            new_callable=AsyncMock,
            return_value=(True, {"name": "Store"}),
        ):
            result = await shopify_test_connection(_user(), repo)

        assert result.status == "active"
        repo.update_config.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_error_when_invalid(self):
        repo = _repo()
        conn = _conn()
        repo.get_active.return_value = conn

        with patch(
            "luana_core_connections.api.shopify.ShopifyConnector.verify_connection",
            new_callable=AsyncMock,
            return_value=(False, {"error": "bad token"}),
        ):
            result = await shopify_test_connection(_user(), repo)

        assert result.status == "error"
