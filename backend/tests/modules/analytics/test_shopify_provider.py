"""Tests for ShopifyProvider ETL — mocked Shopify Admin API responses."""

import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.modules.analytics.infrastructure.providers.shopify_provider import (
    ShopifyProvider,
)


@pytest.fixture
def provider():
    return ShopifyProvider()


@pytest.fixture
def credentials():
    return {
        "access_token": "shpat_test_token",
        "shop_domain": "testshop.myshopify.com",
    }


TENANT_ID = uuid.uuid4()


def _make_order(order_id, created_at, total_price, currency="USD", line_items=None, financial_status="paid"):
    return {
        "id": order_id,
        "created_at": created_at,
        "total_price": str(total_price),
        "currency": currency,
        "financial_status": financial_status,
        "checkout_token": f"token_{order_id}",
        "line_items": line_items or [{"quantity": 1, "price": str(total_price)}],
    }


def _make_checkout(token, created_at, total_price):
    return {
        "token": token,
        "created_at": created_at,
        "total_price": str(total_price),
    }


def _mock_response(data, status_code=200, link_header=""):
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = data
    resp.text = ""
    resp.headers = {"Link": link_header} if link_header else {}
    return resp


class TestShopifyProviderBasics:
    def test_provider_name(self, provider):
        assert provider.provider_name() == "shopify"

    def test_rate_limit_config(self, provider):
        cfg = provider.rate_limit_config()
        assert cfg["requests_per_minute"] == 40

    @pytest.mark.asyncio
    async def test_missing_credentials_returns_empty(self, provider):
        result = await provider.extract_metrics(
            TENANT_ID, {}, date(2026, 3, 1), date(2026, 3, 10)
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_unsupported_stage_returns_empty(self, provider, credentials):
        result = await provider.extract_metrics(
            TENANT_ID, credentials, date(2026, 3, 1), date(2026, 3, 10),
            stage="attraction",
        )
        assert result == []


class TestSalesStage:
    @pytest.mark.asyncio
    async def test_sales_metrics(self, provider, credentials):
        orders = [
            _make_order(1, "2026-03-01T10:00:00Z", 100.0, line_items=[
                {"quantity": 2, "price": "50.00"},
            ]),
            _make_order(2, "2026-03-01T15:00:00Z", 200.0, line_items=[
                {"quantity": 1, "price": "200.00"},
            ]),
            _make_order(3, "2026-03-02T10:00:00Z", 50.0),
        ]

        async def mock_get(url, **kwargs):
            return _mock_response({"orders": orders})

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = mock_get
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await provider.extract_metrics(
                TENANT_ID, credentials,
                date(2026, 3, 1), date(2026, 3, 2),
                stage="sales",
            )

        assert len(result) > 0

        # Check March 1 metrics
        mar1_revenue = [m for m in result if m.date == date(2026, 3, 1) and m.metric_name == "revenue"]
        assert len(mar1_revenue) == 1
        assert mar1_revenue[0].value == 300.0  # 100 + 200

        mar1_orders = [m for m in result if m.date == date(2026, 3, 1) and m.metric_name == "order_count"]
        assert mar1_orders[0].value == 2.0

        mar1_units = [m for m in result if m.date == date(2026, 3, 1) and m.metric_name == "units_sold"]
        assert mar1_units[0].value == 3.0  # 2 + 1

    @pytest.mark.asyncio
    async def test_voided_orders_excluded(self, provider, credentials):
        orders = [
            _make_order(1, "2026-03-01T10:00:00Z", 100.0),
            _make_order(2, "2026-03-01T15:00:00Z", 200.0, financial_status="refunded"),
        ]

        async def mock_get(url, **kwargs):
            return _mock_response({"orders": orders})

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = mock_get
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await provider.extract_metrics(
                TENANT_ID, credentials,
                date(2026, 3, 1), date(2026, 3, 1),
                stage="sales",
            )

        revenue = [m for m in result if m.metric_name == "revenue"]
        assert revenue[0].value == 100.0  # Only non-refunded


class TestOpportunityStage:
    @pytest.mark.asyncio
    async def test_opportunity_metrics(self, provider, credentials):
        orders = [
            _make_order(1, "2026-03-01T12:00:00Z", 100.0),
        ]
        checkouts = [
            _make_checkout("token_1", "2026-03-01T10:00:00Z", 100.0),
            _make_checkout("abandoned_1", "2026-03-01T11:00:00Z", 80.0),
            _make_checkout("abandoned_2", "2026-03-01T14:00:00Z", 60.0),
        ]

        call_count = 0

        async def mock_get(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if "orders" in url:
                return _mock_response({"orders": orders})
            return _mock_response({"checkouts": checkouts})

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = mock_get
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await provider.extract_metrics(
                TENANT_ID, credentials,
                date(2026, 3, 1), date(2026, 3, 1),
                stage="opportunity",
            )

        checkout_count = [m for m in result if m.channel_slug == "checkout-init" and m.metric_name == "count"]
        assert checkout_count[0].value == 3.0

        abandoned_count = [m for m in result if m.channel_slug == "abandoned-cart" and m.metric_name == "count"]
        assert abandoned_count[0].value == 2.0  # 2 not completed

        abandonment = [m for m in result if m.metric_name == "abandonment_rate"]
        assert abandonment[0].value == pytest.approx(66.67, rel=0.1)


class TestPagination:
    @pytest.mark.asyncio
    async def test_follows_link_header(self, provider, credentials):
        page1_orders = [_make_order(i, "2026-03-01T10:00:00Z", 10.0) for i in range(250)]
        page2_orders = [_make_order(250 + i, "2026-03-01T10:00:00Z", 10.0) for i in range(50)]

        call_count = 0

        async def mock_get(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return _mock_response(
                    {"orders": page1_orders},
                    link_header='<https://testshop.myshopify.com/admin/api/2026-01/orders.json?page_info=abc>; rel="next"',
                )
            return _mock_response({"orders": page2_orders})

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = mock_get
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await provider.extract_metrics(
                TENANT_ID, credentials,
                date(2026, 3, 1), date(2026, 3, 1),
                stage="sales",
            )

        # 300 orders → revenue should be 3000
        revenue = [m for m in result if m.metric_name == "revenue"]
        assert revenue[0].value == 3000.0
        assert call_count == 2


class TestDailyExtraction:
    @pytest.mark.asyncio
    async def test_daily_groups_by_date(self, provider, credentials):
        orders = [
            _make_order(1, "2026-03-01T10:00:00Z", 100.0),
            _make_order(2, "2026-03-02T10:00:00Z", 200.0),
            _make_order(3, "2026-03-02T15:00:00Z", 150.0),
        ]

        async def mock_get(url, **kwargs):
            return _mock_response({"orders": orders})

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = mock_get
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await provider.extract_metrics_daily(
                TENANT_ID, credentials,
                date(2026, 3, 1), date(2026, 3, 2),
                stage="sales",
            )

        mar1 = [m for m in result if m.date == date(2026, 3, 1) and m.metric_name == "revenue"]
        mar2 = [m for m in result if m.date == date(2026, 3, 2) and m.metric_name == "revenue"]
        assert mar1[0].value == 100.0
        assert mar2[0].value == 350.0


class TestCleanDomain:
    def test_strips_protocol(self, provider):
        assert provider._clean_domain("https://shop.myshopify.com") == "shop.myshopify.com"

    def test_adds_myshopify(self, provider):
        assert provider._clean_domain("mystore") == "mystore.myshopify.com"

    def test_keeps_custom_domain(self, provider):
        assert provider._clean_domain("shop.example.com") == "shop.example.com"
