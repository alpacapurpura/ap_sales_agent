"""ShopifyProvider — extracts Shopify orders and checkout metrics.

Stage-aware extraction:
- opportunity: checkouts (abandoned carts) from GET /checkouts.json
- sales: orders from GET /orders.json
- other stages: return []

Uses Shopify Admin REST API with Link-header pagination (max 250/page).
Credentials: access_token + shop_domain from connection config.
"""

import logging
from collections import defaultdict
from datetime import date, datetime
from typing import Dict, List, Optional
from uuid import UUID

import httpx

from src.modules.analytics.infrastructure.providers.base import (
    BaseMetricsProvider,
    ExtractedMetric,
)

logger = logging.getLogger(__name__)

API_VERSION = "2026-01"


class ShopifyProvider(BaseMetricsProvider):
    """Extracts metrics from Shopify Admin API for opportunity and sales stages."""

    def provider_name(self) -> str:
        return "shopify"

    def rate_limit_config(self) -> dict:
        return {"requests_per_minute": 40, "burst_size": 10}

    async def extract_metrics(
        self,
        tenant_id: UUID,
        credentials: dict,
        start_date: date,
        end_date: date,
        stage: str = "attraction",
    ) -> List[ExtractedMetric]:
        access_token = credentials.get("access_token")
        shop_domain = credentials.get("shop_domain") or credentials.get("shop_url", "")

        if not access_token or not shop_domain:
            logger.warning(
                "shopify_provider_missing_credentials tenant=%s "
                "access_token=%s shop_domain=%s",
                tenant_id,
                bool(access_token),
                bool(shop_domain),
            )
            return []

        shop_domain = self._clean_domain(shop_domain)

        try:
            if stage == "opportunity":
                return await self._extract_opportunity_metrics(
                    shop_domain, access_token, start_date, end_date
                )
            elif stage == "sales":
                return await self._extract_sales_metrics(
                    shop_domain, access_token, start_date, end_date
                )
            else:
                return []
        except Exception:
            logger.exception(
                "shopify_provider_extract_failed tenant=%s stage=%s",
                tenant_id,
                stage,
            )
            return []

    async def extract_metrics_daily(
        self,
        tenant_id: UUID,
        credentials: dict,
        start_date: date,
        end_date: date,
        stage: str = "attraction",
    ) -> List[ExtractedMetric]:
        """Optimized: single paginated call, then group by date."""
        access_token = credentials.get("access_token")
        shop_domain = credentials.get("shop_domain") or credentials.get("shop_url", "")

        if not access_token or not shop_domain:
            return []

        shop_domain = self._clean_domain(shop_domain)

        try:
            if stage == "opportunity":
                return await self._extract_opportunity_metrics(
                    shop_domain, access_token, start_date, end_date
                )
            elif stage == "sales":
                return await self._extract_sales_metrics(
                    shop_domain, access_token, start_date, end_date
                )
            else:
                return []
        except Exception:
            logger.exception(
                "shopify_provider_extract_daily_failed tenant=%s stage=%s",
                tenant_id,
                stage,
            )
            return []

    @staticmethod
    def _clean_domain(domain: str) -> str:
        domain = domain.replace("https://", "").replace("http://", "").strip("/")
        if not domain.endswith("myshopify.com") and "." not in domain:
            domain = f"{domain}.myshopify.com"
        return domain

    async def _paginated_get(
        self,
        shop_domain: str,
        access_token: str,
        endpoint: str,
        params: dict,
    ) -> List[dict]:
        """Fetch all pages via Shopify Link header pagination."""
        headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json",
        }
        url = f"https://{shop_domain}/admin/api/{API_VERSION}/{endpoint}"
        all_items: List[dict] = []

        # Determine the resource key from endpoint (e.g. "orders.json" -> "orders")
        resource_key = endpoint.replace(".json", "")

        async with httpx.AsyncClient(timeout=30.0) as client:
            while url:
                response = await client.get(url, headers=headers, params=params)
                if response.status_code != 200:
                    logger.error(
                        "shopify_api_error endpoint=%s status=%d body=%s",
                        endpoint,
                        response.status_code,
                        response.text[:200],
                    )
                    break

                data = response.json()
                items = data.get(resource_key, [])
                all_items.extend(items)

                # Follow Link header for next page
                url = self._parse_next_link(response.headers.get("Link", ""))
                params = {}  # Params are embedded in the next URL

        return all_items

    @staticmethod
    def _parse_next_link(link_header: str) -> Optional[str]:
        """Parse Shopify Link header to extract the next page URL."""
        if not link_header:
            return None
        for part in link_header.split(","):
            part = part.strip()
            if 'rel="next"' in part:
                url = part.split(";")[0].strip().strip("<>")
                return url
        return None

    async def _extract_opportunity_metrics(
        self,
        shop_domain: str,
        access_token: str,
        start_date: date,
        end_date: date,
    ) -> List[ExtractedMetric]:
        """Extract checkout/abandoned cart metrics for opportunity stage."""
        # Get orders to calculate completed checkouts
        orders = await self._paginated_get(
            shop_domain,
            access_token,
            "orders.json",
            {
                "status": "any",
                "created_at_min": f"{start_date}T00:00:00Z",
                "created_at_max": f"{end_date}T23:59:59Z",
                "limit": 250,
                "fields": "id,created_at,total_price,checkout_token,financial_status,line_items",
            },
        )

        # Get abandoned checkouts
        checkouts = await self._paginated_get(
            shop_domain,
            access_token,
            "checkouts.json",
            {
                "created_at_min": f"{start_date}T00:00:00Z",
                "created_at_max": f"{end_date}T23:59:59Z",
                "limit": 250,
            },
        )

        # Group by date
        by_date: Dict[date, dict] = defaultdict(
            lambda: {
                "checkout_count": 0,
                "checkout_value": 0.0,
                "order_count": 0,
                "abandoned_count": 0,
                "abandoned_value": 0.0,
            }
        )

        completed_tokens = set()
        for order in orders:
            d = self._parse_date(order.get("created_at", ""))
            if d:
                by_date[d]["order_count"] += 1
                token = order.get("checkout_token")
                if token:
                    completed_tokens.add(token)

        for checkout in checkouts:
            d = self._parse_date(checkout.get("created_at", ""))
            if not d:
                continue
            by_date[d]["checkout_count"] += 1
            by_date[d]["checkout_value"] += float(checkout.get("total_price", 0))

            token = checkout.get("token", "")
            if token and token not in completed_tokens:
                by_date[d]["abandoned_count"] += 1
                by_date[d]["abandoned_value"] += float(
                    checkout.get("total_price", 0)
                )

        metrics: List[ExtractedMetric] = []
        for metric_date, data in by_date.items():
            checkout_count = data["checkout_count"]
            abandoned_count = data["abandoned_count"]
            abandonment_rate = (
                (abandoned_count / checkout_count * 100) if checkout_count > 0 else 0.0
            )

            metric_tuples = [
                ("checkout-init", "count", float(checkout_count), "count", None),
                ("checkout-init", "value", data["checkout_value"], "currency", "USD"),
                ("abandoned-cart", "count", float(abandoned_count), "count", None),
                ("abandoned-cart", "value", data["abandoned_value"], "currency", "USD"),
                (
                    "abandoned-cart",
                    "abandonment_rate",
                    abandonment_rate,
                    "percentage",
                    None,
                ),
            ]

            for slug, name, value, unit, currency in metric_tuples:
                metrics.append(
                    ExtractedMetric(
                        provider="shopify",
                        channel_slug=slug,
                        metric_name=name,
                        value=value,
                        unit=unit,
                        currency=currency,
                        date=metric_date,
                    )
                )

        return metrics

    async def _extract_sales_metrics(
        self,
        shop_domain: str,
        access_token: str,
        start_date: date,
        end_date: date,
    ) -> List[ExtractedMetric]:
        """Extract order/revenue metrics for sales stage."""
        orders = await self._paginated_get(
            shop_domain,
            access_token,
            "orders.json",
            {
                "status": "any",
                "created_at_min": f"{start_date}T00:00:00Z",
                "created_at_max": f"{end_date}T23:59:59Z",
                "limit": 250,
                "fields": "id,created_at,total_price,currency,line_items,financial_status",
            },
        )

        # Group by date
        by_date: Dict[date, dict] = defaultdict(
            lambda: {
                "revenue": 0.0,
                "order_count": 0,
                "units_sold": 0,
                "currency": "USD",
            }
        )

        for order in orders:
            # Skip cancelled/voided orders
            fin_status = order.get("financial_status", "")
            if fin_status in ("voided", "refunded"):
                continue

            d = self._parse_date(order.get("created_at", ""))
            if not d:
                continue

            by_date[d]["revenue"] += float(order.get("total_price", 0))
            by_date[d]["order_count"] += 1
            by_date[d]["currency"] = order.get("currency", "USD")

            for item in order.get("line_items", []):
                by_date[d]["units_sold"] += int(item.get("quantity", 1))

        metrics: List[ExtractedMetric] = []
        for metric_date, data in by_date.items():
            order_count = data["order_count"]
            revenue = data["revenue"]
            avg_order = revenue / order_count if order_count > 0 else 0.0
            currency = data["currency"]

            metric_tuples = [
                ("revenue", revenue, "currency", currency),
                ("order_count", float(order_count), "count", None),
                ("avg_order_value", avg_order, "currency", currency),
                ("units_sold", float(data["units_sold"]), "count", None),
            ]

            for name, value, unit, cur in metric_tuples:
                metrics.append(
                    ExtractedMetric(
                        provider="shopify",
                        channel_slug="shopify",
                        metric_name=name,
                        value=value,
                        unit=unit,
                        currency=cur,
                        date=metric_date,
                    )
                )

        return metrics

    @staticmethod
    def _parse_date(iso_str: str) -> Optional[date]:
        if not iso_str:
            return None
        try:
            return datetime.fromisoformat(iso_str.replace("Z", "+00:00")).date()
        except (ValueError, AttributeError):
            return None
