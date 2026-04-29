"""Tests for channel_info API route."""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from src.modules.connections.api.channel_info import (
    _build_details,
    _get_meta_children,
    get_channel_info,
)
from src.modules.connections.domain.enums import ChannelType

TENANT_ID = uuid.uuid4()


def _user(tenant_id=None):
    u = MagicMock()
    u.tenant_id = tenant_id or TENANT_ID
    return u


def _repo():
    return MagicMock()


def _conn(config=None, credentials=None, channel_type=ChannelType.GOOGLE_ANALYTICS):
    c = MagicMock()
    c.config = {} if config is None else config
    c.credentials = {} if credentials is None else credentials
    c.channel_type = channel_type
    c.is_active = True
    return c


# ---------------------------------------------------------------------------
# _build_details
# ---------------------------------------------------------------------------


class TestBuildDetails:
    def test_google_analytics(self):
        config = {"property_id": "123", "property_display_name": "My GA", "account_name": "Corp"}
        result = _build_details("google_analytics", config, {})
        assert result["property_id"] == "123"
        assert result["property_display_name"] == "My GA"

    def test_youtube(self):
        config = {
            "channel_id": "UCxxx",
            "channel_title": "My Channel",
            "customUrl": "@me",
            "statistics": {"viewCount": 1000},
        }
        result = _build_details("youtube", config, {})
        assert result["channel_id"] == "UCxxx"
        assert result["statistics"]["viewCount"] == 1000

    def test_meta(self):
        config = {
            "name": "Page Name",
            "user_id": "u1",
            "tracked_page_name": "Pg",
            "tracked_ig_username": "@ig",
            "tracked_ad_account_name": "AdAcc",
            "granted_permissions": ["pages_read_engagement"],
        }
        result = _build_details("meta", config, {})
        assert result["name"] == "Page Name"
        assert "pages_read_engagement" in result["granted_permissions"]

    def test_google_ads(self):
        config = {"property_id": "456", "property_display_name": "Ads"}
        creds = {"developer_token": "dt123"}
        result = _build_details("google_ads", config, creds)
        assert result["developer_token_configured"] is True

    def test_google_ads_no_developer_token(self):
        result = _build_details("google_ads", {}, {})
        assert result["developer_token_configured"] is False

    def test_shopify(self):
        config = {"shop_url": "https://x.myshopify.com", "shop_info": {"name": "Store"}}
        result = _build_details("shopify", config, {})
        assert result["shop_url"] == "https://x.myshopify.com"
        assert result["shop_name"] == "Store"

    def test_meta_pixel(self):
        config = {"asset_id": "px1", "pixel_name": "My Pixel", "linked_ad_account_id": "act_123"}
        result = _build_details("meta_pixel", config, {})
        assert result["pixel_id"] == "px1"

    def test_unknown_provider_returns_empty(self):
        result = _build_details("tiktok", {"foo": "bar"}, {})
        assert result == {}


# ---------------------------------------------------------------------------
# _get_meta_children
# ---------------------------------------------------------------------------


class TestGetMetaChildren:
    def test_returns_children_list(self):
        repo = _repo()
        fb_page = MagicMock()
        fb_page.channel_type = ChannelType.FACEBOOK_PAGE
        fb_page.config = {"asset_id": "pg1", "page_name": "My Page"}
        fb_page.is_active = True

        ig = MagicMock()
        ig.channel_type = ChannelType.INSTAGRAM_ACCOUNT
        ig.config = {"asset_id": "ig1", "ig_username": "myig"}
        ig.is_active = True

        repo.get_all_by_tenant_and_types.return_value = [fb_page, ig]
        result = _get_meta_children(repo, TENANT_ID)
        assert len(result) == 2
        assert result[0]["name"] == "My Page"
        assert result[1]["name"] == "myig"

    def test_returns_empty_when_no_children(self):
        repo = _repo()
        repo.get_all_by_tenant_and_types.return_value = []
        result = _get_meta_children(repo, TENANT_ID)
        assert result == []

    def test_excludes_parent_connection_id_from_details(self):
        repo = _repo()
        child = MagicMock()
        child.channel_type = ChannelType.META_ADS_ACCOUNT
        child.config = {"asset_id": "ac1", "ad_account_name": "Ads", "parent_connection_id": "par1"}
        child.is_active = True
        repo.get_all_by_tenant_and_types.return_value = [child]
        result = _get_meta_children(repo, TENANT_ID)
        assert "parent_connection_id" not in result[0]["details"]


# ---------------------------------------------------------------------------
# get_channel_info
# ---------------------------------------------------------------------------


class TestGetChannelInfo:
    @pytest.mark.asyncio
    async def test_raises_400_for_unknown_provider(self):
        from fastapi import HTTPException

        repo = _repo()
        db = MagicMock()
        with pytest.raises(HTTPException) as exc_info:
            await get_channel_info("tiktok", _user(), repo, db)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_returns_not_connected_when_no_active_connection(self):
        repo = _repo()
        repo.get_active.return_value = None
        db = MagicMock()
        result = await get_channel_info("shopify", _user(), repo, db)
        assert result.is_connected is False
        assert result.provider == "shopify"

    @pytest.mark.asyncio
    async def test_returns_connected_for_shopify(self):
        repo = _repo()
        db = MagicMock()
        conn = _conn(
            config={"shop_url": "https://s.myshopify.com", "shop_info": {"name": "Store"}},
            channel_type=ChannelType.SHOPIFY,
        )
        repo.get_active.return_value = conn

        with (
            patch(
                "src.modules.connections.api.channel_info.get_latest_extraction_run_info", return_value={"status": "ok"}
            ),
            patch(
                "src.modules.connections.api.channel_info.get_provider_data_range", return_value={"min": "2024-01-01"}
            ),
        ):
            result = await get_channel_info("shopify", _user(), repo, db)

        assert result.is_connected is True
        assert result.is_configured is True
        assert result.last_extraction == {"status": "ok"}
        assert result.data_range == {"min": "2024-01-01"}

    @pytest.mark.asyncio
    async def test_is_configured_false_when_missing_required_key(self):
        repo = _repo()
        db = MagicMock()
        conn = _conn(config={}, channel_type=ChannelType.GOOGLE_ANALYTICS)
        repo.get_active.return_value = conn

        with (
            patch("src.modules.connections.api.channel_info.get_latest_extraction_run_info", return_value=None),
            patch("src.modules.connections.api.channel_info.get_provider_data_range", return_value=None),
        ):
            result = await get_channel_info("google_analytics", _user(), repo, db)

        assert result.is_connected is True
        assert result.is_configured is False

    @pytest.mark.asyncio
    async def test_meta_fetches_children(self):
        repo = _repo()
        db = MagicMock()
        conn = _conn(
            config={"name": "Meta User", "granted_permissions": []},
            channel_type=ChannelType.META,
        )
        repo.get_active.return_value = conn
        repo.get_all_by_tenant_and_types.return_value = []

        with (
            patch("src.modules.connections.api.channel_info.get_latest_extraction_run_info", return_value=None),
            patch("src.modules.connections.api.channel_info.get_provider_data_range", return_value=None),
        ):
            result = await get_channel_info("meta", _user(), repo, db)

        assert result.is_connected is True
        repo.get_all_by_tenant_and_types.assert_called_once()

    @pytest.mark.asyncio
    async def test_non_meta_provider_does_not_fetch_children(self):
        repo = _repo()
        db = MagicMock()
        conn = _conn(
            config={"channel_id": "UCxx", "channel_title": "My Channel"},
            channel_type=ChannelType.YOUTUBE,
        )
        repo.get_active.return_value = conn

        with (
            patch("src.modules.connections.api.channel_info.get_latest_extraction_run_info", return_value=None),
            patch("src.modules.connections.api.channel_info.get_provider_data_range", return_value=None),
        ):
            result = await get_channel_info("youtube", _user(), repo, db)

        repo.get_all_by_tenant_and_types.assert_not_called()
        assert result.children == []

    @pytest.mark.asyncio
    async def test_handles_extraction_run_exception_gracefully(self):
        repo = _repo()
        db = MagicMock()
        conn = _conn(
            config={"shop_url": "https://s.myshopify.com"},
            channel_type=ChannelType.SHOPIFY,
        )
        repo.get_active.return_value = conn

        with (
            patch(
                "src.modules.connections.api.channel_info.get_latest_extraction_run_info",
                side_effect=Exception("DB error"),
            ),
            patch("src.modules.connections.api.channel_info.get_provider_data_range", return_value=None),
        ):
            result = await get_channel_info("shopify", _user(), repo, db)

        assert result.is_connected is True
        assert result.last_extraction is None

    @pytest.mark.asyncio
    async def test_handles_data_range_exception_gracefully(self):
        repo = _repo()
        db = MagicMock()
        conn = _conn(
            config={"shop_url": "https://s.myshopify.com"},
            channel_type=ChannelType.SHOPIFY,
        )
        repo.get_active.return_value = conn

        with (
            patch("src.modules.connections.api.channel_info.get_latest_extraction_run_info", return_value=None),
            patch(
                "src.modules.connections.api.channel_info.get_provider_data_range",
                side_effect=Exception("network error"),
            ),
        ):
            result = await get_channel_info("shopify", _user(), repo, db)

        assert result.is_connected is True
        assert result.data_range is None

    @pytest.mark.asyncio
    async def test_display_name_and_account_name_extracted(self):
        repo = _repo()
        db = MagicMock()
        conn = _conn(
            config={
                "channel_id": "UCxx",
                "channel_title": "My Channel Title",
                "customUrl": "@mychannel",
            },
            channel_type=ChannelType.YOUTUBE,
        )
        repo.get_active.return_value = conn

        with (
            patch("src.modules.connections.api.channel_info.get_latest_extraction_run_info", return_value=None),
            patch("src.modules.connections.api.channel_info.get_provider_data_range", return_value=None),
        ):
            result = await get_channel_info("youtube", _user(), repo, db)

        assert result.display_name == "My Channel Title"
        assert result.account_name == "@mychannel"
