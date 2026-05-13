"""Tests for marketing connectors: Shopify, MailerLite, ManyChat."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from luana_core_connections.infrastructure.marketing_connectors.mailerlite import (
    MailerliteConnector,
)
from luana_core_connections.infrastructure.marketing_connectors.manychat import (
    ManyChatConnector,
)
from luana_core_connections.infrastructure.marketing_connectors.shopify import (
    ShopifyConnector,
)


def _mock_http(status_code: int, json_data: dict | None = None, text: str = ""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.text = text
    return resp


# ---------------------------------------------------------------------------
# ShopifyConnector
# ---------------------------------------------------------------------------


class TestShopifyGetAuthUrl:
    def test_returns_auth_url_with_domain(self):
        with patch("luana_core_connections.infrastructure.marketing_connectors.shopify.settings") as mock_settings:
            mock_settings.SHOPIFY_API_KEY = "test_key"
            url = ShopifyConnector.get_auth_url("mystore.myshopify.com", "state_xyz", "https://example.com/callback")
        assert "mystore.myshopify.com" in url
        assert "state_xyz" in url

    def test_appends_myshopify_com_when_missing(self):
        with patch("luana_core_connections.infrastructure.marketing_connectors.shopify.settings") as mock_settings:
            mock_settings.SHOPIFY_API_KEY = "test_key"
            url = ShopifyConnector.get_auth_url("mystore", "state", "https://example.com/cb")
        assert "mystore.myshopify.com" in url

    def test_strips_https_prefix(self):
        with patch("luana_core_connections.infrastructure.marketing_connectors.shopify.settings") as mock_settings:
            mock_settings.SHOPIFY_API_KEY = "test_key"
            url = ShopifyConnector.get_auth_url("https://mystore.myshopify.com/", "state", "https://cb.example.com")
        assert "mystore.myshopify.com" in url
        assert "https://https://" not in url


class TestShopifyVerifyHmac:
    def test_returns_false_when_no_hmac(self):
        with patch("luana_core_connections.infrastructure.marketing_connectors.shopify.settings") as mock_settings:
            mock_settings.SHOPIFY_API_SECRET = "test_secret"
            result = ShopifyConnector.verify_hmac({"shop": "store.myshopify.com"})
        assert result is False


class TestShopifyExchangeToken:
    @pytest.mark.asyncio
    async def test_returns_token_on_success(self):
        ok_resp = _mock_http(200, {"access_token": "shpat_abc123"})
        with (
            patch("luana_core_connections.infrastructure.marketing_connectors.shopify.settings") as mock_settings,
            patch("httpx.AsyncClient") as MockClient,
        ):
            mock_settings.SHOPIFY_API_KEY = "k"
            mock_settings.SHOPIFY_API_SECRET = "s"
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.post = AsyncMock(return_value=ok_resp)
            token, error = await ShopifyConnector.exchange_token("mystore.myshopify.com", "auth_code")
        assert token == "shpat_abc123"
        assert error is None

    @pytest.mark.asyncio
    async def test_returns_error_on_non_200(self):
        fail_resp = _mock_http(400, {}, "invalid code")
        with (
            patch("luana_core_connections.infrastructure.marketing_connectors.shopify.settings") as mock_settings,
            patch("httpx.AsyncClient") as MockClient,
        ):
            mock_settings.SHOPIFY_API_KEY = "k"
            mock_settings.SHOPIFY_API_SECRET = "s"
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.post = AsyncMock(return_value=fail_resp)
            token, error = await ShopifyConnector.exchange_token("mystore.myshopify.com", "bad_code")
        assert token is None
        assert error is not None

    @pytest.mark.asyncio
    async def test_returns_error_on_exception(self):
        import httpx

        with (
            patch("luana_core_connections.infrastructure.marketing_connectors.shopify.settings") as mock_settings,
            patch("httpx.AsyncClient") as MockClient,
        ):
            mock_settings.SHOPIFY_API_KEY = "k"
            mock_settings.SHOPIFY_API_SECRET = "s"
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.post = AsyncMock(side_effect=Exception("network error"))
            token, error = await ShopifyConnector.exchange_token("mystore.myshopify.com", "code")
        assert token is None
        assert error is not None


class TestShopifyClientCredentials:
    @pytest.mark.asyncio
    async def test_returns_token_on_success(self):
        ok_resp = _mock_http(200, {"access_token": "token_cc"})
        with (
            patch("luana_core_connections.infrastructure.marketing_connectors.shopify.settings") as mock_settings,
            patch("httpx.AsyncClient") as MockClient,
        ):
            mock_settings.SHOPIFY_API_KEY = "k"
            mock_settings.SHOPIFY_API_SECRET = "s"
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.post = AsyncMock(return_value=ok_resp)
            token, _error = await ShopifyConnector.client_credentials_token("mystore")
        assert token == "token_cc"

    @pytest.mark.asyncio
    async def test_returns_error_on_failure(self):
        fail_resp = _mock_http(401, {}, "unauthorized")
        with (
            patch("luana_core_connections.infrastructure.marketing_connectors.shopify.settings") as mock_settings,
            patch("httpx.AsyncClient") as MockClient,
        ):
            mock_settings.SHOPIFY_API_KEY = "k"
            mock_settings.SHOPIFY_API_SECRET = "s"
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.post = AsyncMock(return_value=fail_resp)
            token, error = await ShopifyConnector.client_credentials_token("mystore")
        assert token is None
        assert error is not None


class TestShopifyVerifyConnection:
    @pytest.mark.asyncio
    async def test_returns_shop_info_on_success(self):
        shop_data = {
            "shop": {
                "id": 1,
                "name": "My Store",
                "email": "owner@store.com",
                "domain": "mystore.myshopify.com",
                "currency": "USD",
                "shop_owner": "Owner",
                "plan_name": "basic",
            }
        }
        ok_resp = _mock_http(200, shop_data)
        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=ok_resp)
            valid, info = await ShopifyConnector.verify_connection("mystore.myshopify.com", "token")
        assert valid is True
        assert info["name"] == "My Store"

    @pytest.mark.asyncio
    async def test_returns_false_on_401(self):
        fail_resp = _mock_http(401)
        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=fail_resp)
            valid, info = await ShopifyConnector.verify_connection("mystore.myshopify.com", "bad_token")
        assert valid is False
        assert "error" in info

    @pytest.mark.asyncio
    async def test_returns_false_on_404(self):
        fail_resp = _mock_http(404)
        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=fail_resp)
            valid, _info = await ShopifyConnector.verify_connection("notfound.myshopify.com", "token")
        assert valid is False

    @pytest.mark.asyncio
    async def test_returns_false_on_network_error(self):
        import httpx

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(side_effect=httpx.RequestError("timeout"))
            valid, _info = await ShopifyConnector.verify_connection("mystore.myshopify.com", "token")
        assert valid is False

    @pytest.mark.asyncio
    async def test_returns_false_on_generic_exception(self):
        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(side_effect=ValueError("unexpected"))
            valid, _info = await ShopifyConnector.verify_connection("mystore.myshopify.com", "token")
        assert valid is False


class TestShopifySyncMethods:
    def test_sync_contacts_returns_empty_list(self):
        conn = ShopifyConnector()
        result = conn.sync_contacts("tenant_1")
        assert result == []

    def test_sync_events_returns_empty_list(self):
        conn = ShopifyConnector()
        result = conn.sync_events("tenant_1")
        assert result == []


# ---------------------------------------------------------------------------
# MailerliteConnector
# ---------------------------------------------------------------------------


class TestMailerliteVerifyConnection:
    @pytest.mark.asyncio
    async def test_returns_true_on_success(self):
        ok_resp = _mock_http(200, {"account": {"name": "My Account"}})
        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=ok_resp)
            valid, _info = await MailerliteConnector.verify_connection("valid_api_key")
        assert valid is True

    @pytest.mark.asyncio
    async def test_returns_false_on_401(self):
        fail_resp = _mock_http(401, {}, "unauthorized")
        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=fail_resp)
            valid, _info = await MailerliteConnector.verify_connection("bad_key")
        assert valid is False

    @pytest.mark.asyncio
    async def test_returns_false_on_network_error(self):
        import httpx

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(side_effect=httpx.HTTPError("timeout"))
            valid, _info = await MailerliteConnector.verify_connection("key")
        assert valid is False


class TestMailerliteGetRecentActivity:
    @pytest.mark.asyncio
    async def test_returns_empty_on_campaigns_api_error(self):
        fail_resp = _mock_http(500, {}, "server error")
        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=fail_resp)
            connector = MailerliteConnector(api_key="test_key")
            result = await connector.get_recent_campaign_activity(hours=1)
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_activities_for_recent_campaigns(self):
        import datetime

        now = datetime.datetime.now(datetime.UTC)
        recent_iso = (now - datetime.timedelta(hours=1)).isoformat()

        campaigns_resp = _mock_http(200, {"data": [{"id": "camp_1", "name": "Newsletter", "finished_at": recent_iso}]})
        activity_resp = _mock_http(200, {"data": [{"subscriber": {"email": "sub@test.com"}}]})

        call_count = [0]

        async def side_effect(url, **kwargs):
            call_count[0] += 1
            if "campaigns" in url and "subscriber-activity" not in url:
                return campaigns_resp
            return activity_resp

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(side_effect=side_effect)
            connector = MailerliteConnector(api_key="test_key")
            result = await connector.get_recent_campaign_activity(hours=2)

        assert len(result) >= 1
        assert result[0]["email"] == "sub@test.com"

    @pytest.mark.asyncio
    async def test_returns_empty_on_http_error(self):
        import httpx

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(side_effect=httpx.HTTPError("timeout"))
            connector = MailerliteConnector(api_key="key")
            result = await connector.get_recent_campaign_activity()
        assert result == []


class TestMailerliteSyncMethods:
    def test_sync_contacts_returns_empty_list(self):
        connector = MailerliteConnector(api_key="key")
        assert connector.sync_contacts("tenant_1") == []

    def test_sync_events_returns_empty_list(self):
        connector = MailerliteConnector(api_key="key")
        assert connector.sync_events("tenant_1") == []


# ---------------------------------------------------------------------------
# ManyChatConnector
# ---------------------------------------------------------------------------


class TestManyChatVerifyConnection:
    @pytest.mark.asyncio
    async def test_returns_true_on_success(self):
        ok_resp = _mock_http(200, {"status": "success", "data": {"id": "page_123"}})
        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=ok_resp)
            valid, data = await ManyChatConnector.verify_connection("valid_key")
        assert valid is True
        assert data["id"] == "page_123"

    @pytest.mark.asyncio
    async def test_returns_false_when_status_not_success(self):
        fail_resp = _mock_http(200, {"status": "error", "message": "Invalid token"})
        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=fail_resp)
            valid, data = await ManyChatConnector.verify_connection("bad_key")
        assert valid is False
        assert "error" in data

    @pytest.mark.asyncio
    async def test_returns_false_on_non_200(self):
        fail_resp = _mock_http(403, {}, "forbidden")
        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=fail_resp)
            valid, _data = await ManyChatConnector.verify_connection("key")
        assert valid is False

    @pytest.mark.asyncio
    async def test_returns_false_on_http_error(self):
        import httpx

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(side_effect=httpx.HTTPError("timeout"))
            valid, _data = await ManyChatConnector.verify_connection("key")
        assert valid is False


class TestManyChatGetSubscriber:
    @pytest.mark.asyncio
    async def test_returns_subscriber_data_on_success(self):
        ok_resp = _mock_http(200, {"status": "success", "data": {"id": "sub_123", "name": "Alice"}})
        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=ok_resp)
            valid, data = await ManyChatConnector.get_subscriber("api_key", "sub_123")
        assert valid is True
        assert data["id"] == "sub_123"

    @pytest.mark.asyncio
    async def test_returns_false_on_api_error(self):
        fail_resp = _mock_http(404)
        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=fail_resp)
            valid, _data = await ManyChatConnector.get_subscriber("api_key", "missing")
        assert valid is False


class TestManyChatFindByEmail:
    @pytest.mark.asyncio
    async def test_returns_list_on_success(self):
        ok_resp = _mock_http(200, {"status": "success", "data": [{"id": "sub_1"}]})
        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=ok_resp)
            valid, data = await ManyChatConnector.find_subscriber_by_email("key", "user@test.com")
        assert valid is True
        assert data[0]["id"] == "sub_1"

    @pytest.mark.asyncio
    async def test_returns_false_on_error(self):
        import httpx

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(side_effect=httpx.HTTPError("timeout"))
            valid, _data = await ManyChatConnector.find_subscriber_by_email("key", "user@test.com")
        assert valid is False


class TestManyChatGetTags:
    @pytest.mark.asyncio
    async def test_returns_tags_list(self):
        ok_resp = _mock_http(200, {"status": "success", "data": [{"id": "tag_1", "name": "lead"}]})
        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=ok_resp)
            valid, tags = await ManyChatConnector.get_tags("key")
        assert valid is True
        assert tags[0]["name"] == "lead"

    @pytest.mark.asyncio
    async def test_returns_empty_on_error(self):
        import httpx

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(side_effect=httpx.HTTPError("timeout"))
            valid, tags = await ManyChatConnector.get_tags("key")
        assert valid is False
        assert tags == []


class TestManyChatGetCustomFields:
    @pytest.mark.asyncio
    async def test_returns_custom_fields(self):
        ok_resp = _mock_http(200, {"status": "success", "data": [{"id": "field_1", "name": "Consultas"}]})
        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=ok_resp)
            valid, fields = await ManyChatConnector.get_custom_fields("key")
        assert valid is True
        assert fields[0]["name"] == "Consultas"
