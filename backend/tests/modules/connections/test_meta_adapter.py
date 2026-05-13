"""Tests for Meta (Facebook) channel adapter: MetaAdapter + module helpers."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from luana_core_connections.infrastructure.channels.meta import (
    MetaAdapter,
    _fetch_pixels,
    _fetch_wabas,
    _fetch_whatsapp_accounts,
    _parse_ad_accounts,
    _parse_linked_ig,
)


def _ok_resp(json_data: dict | None = None, text: str = "") -> MagicMock:
    r = MagicMock()
    r.status_code = 200
    r.json.return_value = json_data or {}
    r.text = text
    return r


def _fail_resp(status: int = 400, text: str = "error") -> MagicMock:
    r = MagicMock()
    r.status_code = status
    r.text = text
    return r


# ─────────────────────────────────────────────────────────────────────────────
# Module-level helpers
# ─────────────────────────────────────────────────────────────────────────────


class TestParseLinkedIg:
    def test_noop_when_exception(self):
        instagram_accounts: list = []
        _parse_linked_ig({"id": "p1"}, {}, Exception("network error"), instagram_accounts)
        assert instagram_accounts == []

    def test_noop_when_non_200_response(self):
        instagram_accounts: list = []
        fail = _fail_resp(404)
        _parse_linked_ig({"id": "p1"}, {}, fail, instagram_accounts)
        assert instagram_accounts == []

    def test_noop_when_no_ig_account(self):
        instagram_accounts: list = []
        ok = _ok_resp({"data": []})  # no instagram_business_account key
        _parse_linked_ig({"id": "p1"}, {}, ok, instagram_accounts)
        assert instagram_accounts == []

    def test_appends_ig_account(self):
        instagram_accounts: list = []
        page_entry: dict = {}
        ig_data = {
            "instagram_business_account": {
                "id": "ig123",
                "username": "mypage",
                "profile_picture_url": "http://pic.jpg",
                "followers_count": 1000,
            }
        }
        ok = _ok_resp(ig_data)
        _parse_linked_ig({"id": "p1", "name": "My Page", "access_token": "tok"}, page_entry, ok, instagram_accounts)
        assert len(instagram_accounts) == 1
        assert instagram_accounts[0]["ig_account_id"] == "ig123"
        assert page_entry["instagram_account_id"] == "ig123"


class TestParseAdAccounts:
    def test_returns_empty_on_non_200(self):
        result = _parse_ad_accounts(_fail_resp(401))
        assert result == []

    def test_parses_ad_accounts(self):
        resp = _ok_resp(
            {"data": [{"account_id": "123", "id": "act_123", "name": "My Ads", "currency": "USD", "account_status": 1}]}
        )
        result = _parse_ad_accounts(resp)
        assert len(result) == 1
        assert result[0]["ad_account_id"] == "123"
        assert result[0]["currency"] == "USD"

    def test_uses_id_fallback_when_no_account_id(self):
        resp = _ok_resp({"data": [{"id": "act_456", "name": "Ad Acc", "currency": "PEN"}]})
        result = _parse_ad_accounts(resp)
        assert result[0]["ad_account_id"] == "456"


class TestFetchPixels:
    @pytest.mark.asyncio
    async def test_returns_empty_when_no_accounts(self):
        result = await _fetch_pixels([], "tok", "https://graph.facebook.com/v24.0")
        assert result == []

    @pytest.mark.asyncio
    async def test_fetches_pixels_for_accounts(self):
        ok_resp = _ok_resp({"data": [{"id": "px1", "name": "Pixel 1"}]})

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=ok_resp)

            result = await _fetch_pixels([{"ad_account_id": "123"}], "tok", "https://graph.facebook.com/v24.0")

        assert len(result) == 1
        assert result[0]["pixel_id"] == "px1"

    @pytest.mark.asyncio
    async def test_skips_exception_response(self):
        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(side_effect=httpx.ConnectError("timeout"))

            # gather with return_exceptions=True means no raise here
            # but the inner gather catches and returns exception
            import asyncio

            with patch("asyncio.gather", new_callable=AsyncMock, return_value=[Exception("timeout")]):
                result = await _fetch_pixels([{"ad_account_id": "123"}], "tok", "https://graph.facebook.com/v24.0")
            assert result == []

    @pytest.mark.asyncio
    async def test_skips_failed_pixel_response(self):
        fail = _fail_resp(500)

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=fail)

            result = await _fetch_pixels([{"ad_account_id": "123"}], "tok", "https://graph.facebook.com/v24.0")

        assert result == []


class TestFetchWabas:
    @pytest.mark.asyncio
    async def test_fetches_wabas(self):
        ok_resp = _ok_resp({"data": [{"id": "waba1", "name": "WABA 1"}]})

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=ok_resp)

            result = await _fetch_wabas([{"id": "biz1", "name": "Biz 1"}], "tok", "https://graph.facebook.com/v24.0")

        assert len(result) == 1
        assert result[0]["id"] == "waba1"
        assert result[0]["business_id"] == "biz1"

    @pytest.mark.asyncio
    async def test_skips_exception_waba_response(self):
        import asyncio

        with patch("asyncio.gather", new_callable=AsyncMock, return_value=[Exception("timeout")]):
            result = await _fetch_wabas([{"id": "biz1", "name": "Biz 1"}], "tok", "https://graph.facebook.com/v24.0")
        assert result == []

    @pytest.mark.asyncio
    async def test_skips_failed_waba_response(self):
        fail = _fail_resp(500)
        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=fail)

            result = await _fetch_wabas([{"id": "biz1"}], "tok", "https://graph.facebook.com/v24.0")
        assert result == []


class TestFetchWhatsappAccounts:
    @pytest.mark.asyncio
    async def test_returns_empty_when_businesses_fail(self):
        fail = _fail_resp(400)
        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=fail)

            result = await _fetch_whatsapp_accounts("tok", "https://graph.facebook.com/v24.0")

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_businesses(self):
        ok = _ok_resp({"data": []})
        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=ok)

            result = await _fetch_whatsapp_accounts("tok", "https://graph.facebook.com/v24.0")

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_on_exception(self):
        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(side_effect=Exception("network error"))

            result = await _fetch_whatsapp_accounts("tok", "https://graph.facebook.com/v24.0")

        assert result == []


# ─────────────────────────────────────────────────────────────────────────────
# MetaAdapter class
# ─────────────────────────────────────────────────────────────────────────────


class TestMetaAdapterInit:
    def test_init_without_token(self):
        with patch("luana_core_connections.infrastructure.channels.meta.settings") as mock_settings:
            mock_settings.META_APP_ID = "app123"
            mock_settings.META_APP_SECRET = "secret"
            mock_settings.META_CONFIG_ID = None
            adapter = MetaAdapter()
        assert adapter.access_token is None
        assert adapter._api_instance is None

    def test_init_with_token_calls_init_api(self):
        with (
            patch("luana_core_connections.infrastructure.channels.meta.settings") as mock_settings,
            patch("luana_core_connections.infrastructure.channels.meta.FacebookSession") as MockSession,
            patch("luana_core_connections.infrastructure.channels.meta.FacebookAdsApi") as MockApi,
        ):
            mock_settings.META_APP_ID = "app123"
            mock_settings.META_APP_SECRET = "secret"
            mock_settings.META_CONFIG_ID = None
            MockSession.return_value = MagicMock()
            MockApi.return_value = MagicMock()
            adapter = MetaAdapter(access_token="tok123")
        assert adapter._api_instance is not None


class TestMetaAdapterGetAuthorizationUrl:
    def test_returns_url_with_state(self):
        with patch("luana_core_connections.infrastructure.channels.meta.settings") as mock_settings:
            mock_settings.META_APP_ID = "app123"
            mock_settings.META_APP_SECRET = "secret"
            mock_settings.META_CONFIG_ID = None
            adapter = MetaAdapter(app_id="app123", app_secret="secret")

        url, state = adapter.get_authorization_url("https://redirect.example.com")
        assert "meta_" in state
        assert "client_id=app123" in url

    def test_adds_config_id_when_configured(self):
        with patch("luana_core_connections.infrastructure.channels.meta.settings") as mock_settings:
            mock_settings.META_APP_ID = "app123"
            mock_settings.META_APP_SECRET = "secret"
            mock_settings.META_CONFIG_ID = "cfg_123"
            adapter = MetaAdapter(app_id="app123", app_secret="secret")
            url, _state = adapter.get_authorization_url("https://redirect.example.com")

        assert "config_id=cfg_123" in url

    def test_uses_provided_state(self):
        with patch("luana_core_connections.infrastructure.channels.meta.settings") as mock_settings:
            mock_settings.META_APP_ID = "app123"
            mock_settings.META_APP_SECRET = "secret"
            mock_settings.META_CONFIG_ID = None
            adapter = MetaAdapter(app_id="app123", app_secret="secret")

        _url, state = adapter.get_authorization_url("https://redirect.example.com", state="meta_existing")
        assert state == "meta_existing"

    def test_adds_meta_prefix_to_non_meta_state(self):
        with patch("luana_core_connections.infrastructure.channels.meta.settings") as mock_settings:
            mock_settings.META_APP_ID = "app123"
            mock_settings.META_APP_SECRET = "secret"
            mock_settings.META_CONFIG_ID = None
            adapter = MetaAdapter(app_id="app123", app_secret="secret")

        _url, state = adapter.get_authorization_url("https://redirect.example.com", state="custom_state")
        assert state.startswith("meta_")


class TestMetaAdapterExchangeCode:
    @pytest.mark.asyncio
    async def test_exchanges_code_and_extends_token(self):
        short_tok_resp = _ok_resp({"access_token": "short_token"})
        long_tok_resp = _ok_resp({"access_token": "long_token", "token_type": "bearer", "expires_in": 5184000})

        call_count = 0

        async def fake_get(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return short_tok_resp
            return long_tok_resp

        with (
            patch("luana_core_connections.infrastructure.channels.meta.settings") as mock_settings,
            patch("httpx.AsyncClient") as MockClient,
        ):
            mock_settings.META_APP_ID = "app123"
            mock_settings.META_APP_SECRET = "secret"
            mock_settings.META_CONFIG_ID = None
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(side_effect=fake_get)

            adapter = MetaAdapter(app_id="app123", app_secret="secret")
            result = await adapter.exchange_code("code123", "https://redirect.example.com")

        assert result["access_token"] == "long_token"

    @pytest.mark.asyncio
    async def test_raises_when_initial_exchange_fails(self):
        fail = _fail_resp(400, "bad code")
        fail.raise_for_status = MagicMock(side_effect=httpx.HTTPStatusError("bad", request=MagicMock(), response=fail))

        with (
            patch("luana_core_connections.infrastructure.channels.meta.settings") as mock_settings,
            patch("httpx.AsyncClient") as MockClient,
        ):
            mock_settings.META_APP_ID = "app123"
            mock_settings.META_APP_SECRET = "secret"
            mock_settings.META_CONFIG_ID = None
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=fail)

            adapter = MetaAdapter(app_id="app123", app_secret="secret")
            with pytest.raises(Exception):  # noqa: B017
                await adapter.exchange_code("bad_code", "https://redirect.example.com")

    @pytest.mark.asyncio
    async def test_uses_short_token_when_extension_fails(self):
        short_tok_resp = _ok_resp({"access_token": "short_token"})

        call_count = 0

        async def fake_get(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return short_tok_resp
            msg = "extension API down"
            raise RuntimeError(msg)

        with (
            patch("luana_core_connections.infrastructure.channels.meta.settings") as mock_settings,
            patch("httpx.AsyncClient") as MockClient,
        ):
            mock_settings.META_APP_ID = "app123"
            mock_settings.META_APP_SECRET = "secret"
            mock_settings.META_CONFIG_ID = None
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(side_effect=fake_get)

            adapter = MetaAdapter(app_id="app123", app_secret="secret")
            result = await adapter.exchange_code("code123", "https://redirect.example.com")

        assert result["access_token"] == "short_token"


class TestMetaAdapterGetTokenPermissions:
    @pytest.mark.asyncio
    async def test_returns_granted_permissions(self):
        ok = _ok_resp(
            {
                "data": [
                    {"permission": "pages_show_list", "status": "granted"},
                    {"permission": "ads_read", "status": "declined"},
                ]
            }
        )
        with (
            patch("luana_core_connections.infrastructure.channels.meta.settings") as mock_settings,
            patch("httpx.AsyncClient") as MockClient,
        ):
            mock_settings.META_APP_ID = "app123"
            mock_settings.META_APP_SECRET = "secret"
            mock_settings.META_CONFIG_ID = None
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=ok)

            adapter = MetaAdapter(app_id="app123", app_secret="secret", access_token="tok")
            with patch.object(adapter, "_init_api"):
                adapter._api_instance = MagicMock()
            result = await adapter.get_token_permissions()

        assert result == ["pages_show_list"]

    @pytest.mark.asyncio
    async def test_returns_empty_on_api_failure(self):
        fail = _fail_resp(400)
        with (
            patch("luana_core_connections.infrastructure.channels.meta.settings") as mock_settings,
            patch("httpx.AsyncClient") as MockClient,
        ):
            mock_settings.META_APP_ID = "app123"
            mock_settings.META_APP_SECRET = "secret"
            mock_settings.META_CONFIG_ID = None
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=fail)

            adapter = MetaAdapter(app_id="app123", app_secret="secret")
            adapter._api_instance = MagicMock()
            result = await adapter.get_token_permissions()

        assert result == []


class TestMetaAdapterGetBusinessAssets:
    @pytest.mark.asyncio
    async def test_raises_when_no_token(self):
        with patch("luana_core_connections.infrastructure.channels.meta.settings") as mock_settings:
            mock_settings.META_APP_ID = "app123"
            mock_settings.META_APP_SECRET = "secret"
            mock_settings.META_CONFIG_ID = None
            adapter = MetaAdapter(app_id="app123", app_secret="secret")

        with pytest.raises(ValueError):
            await adapter.get_business_assets()

    @pytest.mark.asyncio
    async def test_returns_structured_assets(self):
        pages_resp = _ok_resp({"data": [{"id": "p1", "name": "Page 1", "access_token": "page_tok"}]})
        ads_resp = _ok_resp({"data": []})
        ig_resp = _ok_resp({"instagram_business_account": {"id": "ig1", "username": "mypageinsta"}})
        _ok_resp({"data": []})
        biz_resp = _ok_resp({"data": []})

        call_count = [0]

        async def fake_get(url, **kwargs):
            call_count[0] += 1
            if "me/accounts" in url:
                return pages_resp
            if "me/adaccounts" in url:
                return ads_resp
            if "p1" in url and "instagram" not in url:
                return ig_resp
            if "me/businesses" in url:
                return biz_resp
            return _ok_resp({"data": []})

        with (
            patch("luana_core_connections.infrastructure.channels.meta.settings") as mock_settings,
            patch("httpx.AsyncClient") as MockClient,
            patch("luana_core_connections.infrastructure.channels.meta.FacebookSession"),
            patch("luana_core_connections.infrastructure.channels.meta.FacebookAdsApi"),
        ):
            mock_settings.META_APP_ID = "app123"
            mock_settings.META_APP_SECRET = "secret"
            mock_settings.META_CONFIG_ID = None
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(side_effect=fake_get)

            adapter = MetaAdapter(app_id="app123", app_secret="secret", access_token="user_tok")
            result = await adapter.get_business_assets()

        assert "pages" in result
        assert "instagram_accounts" in result
        assert "ads_accounts" in result
        assert "pixels" in result
        assert "whatsapp_accounts" in result


class TestMetaAdapterParsePages:
    @pytest.mark.asyncio
    async def test_returns_empty_on_failed_pages_response(self):
        fail = _fail_resp(401)
        with (
            patch("luana_core_connections.infrastructure.channels.meta.settings") as mock_settings,
            patch("luana_core_connections.infrastructure.channels.meta.FacebookSession"),
            patch("luana_core_connections.infrastructure.channels.meta.FacebookAdsApi"),
        ):
            mock_settings.META_APP_ID = "app123"
            mock_settings.META_APP_SECRET = "secret"
            mock_settings.META_CONFIG_ID = None
            adapter = MetaAdapter(app_id="app123", app_secret="secret", access_token="tok")
            pages, ig = await adapter._parse_pages_and_ig(fail, "tok", "https://graph.facebook.com/v24.0")

        assert pages == []
        assert ig == []
