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
from uuid import UUID

import httpx

from src.modules.analytics.domain.extraction_result import ExtractionResult
from src.modules.analytics.infrastructure.providers.base import (
    BaseMetricsProvider,
    ExtractedMetric,
)

logger = logging.getLogger(__name__)

API_VERSION = "2026-01"


class ShopifyProvider(BaseMetricsProvider):
    """Extracts metrics from Shopify Admin API for opportunity and sales stages."""

    def __init__(self) -> None:
        """Initialize shopify provider."""
        self._last_orders: list[dict] = []
        self._last_checkouts: list[dict] = []

    def get_last_extracted_orders(self) -> list[dict]:
        """Return raw orders cached during the last sales-stage extraction."""
        return self._last_orders

    def get_last_extracted_checkouts(self) -> list[dict]:
        """Return raw checkouts cached during the last opportunity-stage extraction."""
        return self._last_checkouts

    def provider_name(self) -> str:
        """Execute provider name operation."""
        return "shopify"

    def has_period_extraction(self) -> bool:
        """Check if  period extraction."""
        return True

    async def extract_period_metrics(
        self,
        tenant_id: UUID,
        credentials: dict,
        period_type: str,
        period_start: date,
        period_end: date,
        metric_names: list[str],
        stage: str = "attraction",
    ) -> ExtractionResult:
        """Extract repeat_customers by querying Shopify orders in the period.

        No external API call needed — counts customers with >1 order
        from cached/stored order data.
        """
        if "repeat_customers" not in metric_names:
            return ExtractionResult()

        access_token = credentials.get("access_token")
        shop_domain = credentials.get("shop_domain")
        if not access_token or not shop_domain:
            return ExtractionResult()

        # Fetch orders for the period
        import httpx

        all_orders = []
        url = f"https://{shop_domain}/admin/api/2024-01/orders.json"
        params = {
            "status": "any",
            "created_at_min": f"{period_start}T00:00:00Z",
            "created_at_max": f"{period_end}T23:59:59Z",
            "limit": 250,
            "fields": "id,customer",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            headers = {"X-Shopify-Access-Token": access_token}
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            all_orders = resp.json().get("orders", [])

        # Count customers with >1 order in the period
        from collections import Counter

        customer_ids = [o.get("customer", {}).get("id") for o in all_orders if o.get("customer", {}).get("id")]
        customer_counts = Counter(customer_ids)
        repeat_count = sum(1 for c in customer_counts.values() if c > 1)

        from src.modules.analytics.infrastructure.providers.base import ExtractedMetric

        metrics = [
            ExtractedMetric(
                provider="shopify",
                channel_slug="shopify",
                metric_name="repeat_customers",
                value=float(repeat_count),
                unit="count",
                date=period_start,
                extra={
                    "period_type": period_type,
                    "total_customers": len(customer_counts),
                },
            ),
        ]

        return ExtractionResult(metrics=metrics)

    def rate_limit_config(self) -> dict:
        """Execute rate limit config operation."""
        return {"requests_per_minute": 40, "burst_size": 10}

    async def extract_metrics(
        self,
        tenant_id: UUID,
        credentials: dict,
        start_date: date,
        end_date: date,
        stage: str = "attraction",
    ) -> ExtractionResult:
        """Extract metrics."""
        access_token = credentials.get("access_token")
        shop_domain = credentials.get("shop_domain") or credentials.get("shop_url", "")

        if not access_token or not shop_domain:
            logger.warning(
                "shopify_provider_missing_credentials tenant=%s access_token=%s shop_domain=%s",
                tenant_id,
                bool(access_token),
                bool(shop_domain),
            )
            return ExtractionResult()

        shop_domain = self._clean_domain(shop_domain)
        shop_currency = credentials.get("shop_currency", "USD")

        metrics: list = []
        failures = []

        if stage == "opportunity":
            m, fail = await self._safe_extract(
                self._extract_opportunity_metrics,
                shop_domain,
                access_token,
                start_date,
                end_date,
                shop_currency,
                extractor_name="shopify_opportunity",
            )
            metrics.extend(m)
            if fail:
                failures.append(fail)
        elif stage == "sales":
            m, fail = await self._safe_extract(
                self._extract_sales_metrics,
                shop_domain,
                access_token,
                start_date,
                end_date,
                extractor_name="shopify_sales",
            )
            metrics.extend(m)
            if fail:
                failures.append(fail)

        return ExtractionResult(metrics=metrics, failures=failures)

    async def extract_metrics_daily(
        self,
        tenant_id: UUID,
        credentials: dict,
        start_date: date,
        end_date: date,
        stage: str = "attraction",
    ) -> ExtractionResult:
        """Optimized: single paginated call, then group by date."""
        access_token = credentials.get("access_token")
        shop_domain = credentials.get("shop_domain") or credentials.get("shop_url", "")

        if not access_token or not shop_domain:
            return ExtractionResult()

        shop_domain = self._clean_domain(shop_domain)
        shop_currency = credentials.get("shop_currency", "USD")

        metrics: list = []
        failures = []

        if stage == "opportunity":
            m, fail = await self._safe_extract(
                self._extract_opportunity_metrics,
                shop_domain,
                access_token,
                start_date,
                end_date,
                shop_currency,
                extractor_name="shopify_opportunity",
            )
            metrics.extend(m)
            if fail:
                failures.append(fail)
        elif stage == "sales":
            m, fail = await self._safe_extract(
                self._extract_sales_metrics,
                shop_domain,
                access_token,
                start_date,
                end_date,
                extractor_name="shopify_sales",
            )
            metrics.extend(m)
            if fail:
                failures.append(fail)

        return ExtractionResult(metrics=metrics, failures=failures)

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
    ) -> list[dict]:
        """Fetch all pages via Shopify Link header pagination."""
        headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json",
        }
        url = f"https://{shop_domain}/admin/api/{API_VERSION}/{endpoint}"
        all_items: list[dict] = []

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
    def _parse_next_link(link_header: str) -> str | None:
        """Parse Shopify Link header to extract the next page URL."""
        if not link_header:
            return None
        for part in link_header.split(","):
            segment = part.strip()
            if 'rel="next"' in segment:
                url = segment.split(";")[0].strip().strip("<>")
                return url
        return None

    async def _extract_opportunity_metrics(
        self,
        shop_domain: str,
        access_token: str,
        start_date: date,
        end_date: date,
        shop_currency: str = "USD",
    ) -> list[ExtractedMetric]:
        """Extract checkout/abandoned cart metrics for opportunity stage."""
        # Get orders to calculate completed checkouts
        orders = await self._paginated_get(
            shop_domain,
            access_token,
            "orders.json",
            {
                "status": "any",
                "processed_at_min": f"{start_date}T00:00:00Z",
                "processed_at_max": f"{end_date}T23:59:59Z",
                "limit": 250,
                "fields": "id,created_at,processed_at,total_price,checkout_token,financial_status,line_items",
            },
        )

        # Cache orders for CRM record creation in ETL
        self._last_checkouts = []  # Reset; will be populated below

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

        # Cache checkouts for CRM record creation in ETL
        self._last_checkouts = checkouts

        # Group by date
        by_date: dict[date, dict] = defaultdict(
            lambda: {
                "checkout_count": 0,
                "checkout_value": 0.0,
                "order_count": 0,
                "abandoned_count": 0,
                "abandoned_value": 0.0,
            },
        )

        completed_tokens = set()
        for order in orders:
            d = self._parse_date(
                order.get("processed_at") or order.get("created_at", ""),
            )
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
                by_date[d]["abandoned_value"] += float(checkout.get("total_price", 0))

        metrics: list[ExtractedMetric] = []
        for metric_date, data in by_date.items():
            checkout_count = data["checkout_count"]
            abandoned_count = data["abandoned_count"]
            abandonment_rate = (abandoned_count / checkout_count * 100) if checkout_count > 0 else 0.0

            metric_tuples = [
                ("checkout-init", "count", float(checkout_count), "count", None),
                (
                    "checkout-init",
                    "value",
                    data["checkout_value"],
                    "currency",
                    shop_currency,
                ),
                ("abandoned-cart", "count", float(abandoned_count), "count", None),
                (
                    "abandoned-cart",
                    "value",
                    data["abandoned_value"],
                    "currency",
                    shop_currency,
                ),
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
                    ),
                )

        return metrics

    async def _extract_sales_metrics(
        self,
        shop_domain: str,
        access_token: str,
        start_date: date,
        end_date: date,
    ) -> list[ExtractedMetric]:
        """Extract order/revenue metrics for sales stage.

        Extracts 12 metrics per day:
        - revenue, order_count, avg_order_value, units_sold (original 4)
        - total_discounts, total_tax, net_sales, refund_amount,
          refund_count, shipping_revenue, repeat_customers,
          discount_usage_count (new 8)
        """
        orders = await self._paginated_get(
            shop_domain,
            access_token,
            "orders.json",
            {
                "status": "any",
                "processed_at_min": f"{start_date}T00:00:00Z",
                "processed_at_max": f"{end_date}T23:59:59Z",
                "limit": 250,
                "fields": (
                    "id,email,created_at,processed_at,total_price,current_total_price,"
                    "currency,checkout_token,line_items,financial_status,total_discounts,"
                    "total_tax,subtotal_price,shipping_lines,discount_codes,customer,"
                    "billing_address"
                ),
            },
        )

        # Cache orders for CRM record creation in ETL
        self._last_orders = orders

        # Group by date
        by_date: dict[date, dict] = defaultdict(
            lambda: {
                "revenue": 0.0,
                "order_count": 0,
                "units_sold": 0,
                "currency": "USD",
                "total_discounts": 0.0,
                "total_tax": 0.0,
                "refund_amount": 0.0,
                "refund_count": 0,
                "shipping_revenue": 0.0,
                "discount_usage_count": 0,
                "repeat_customer_ids": set(),
            },
        )

        for order in orders:
            self._accumulate_order(order, by_date)

        metrics: list[ExtractedMetric] = []
        for metric_date, data in by_date.items():
            order_count = data["order_count"]
            revenue = data["revenue"]
            avg_order = revenue / order_count if order_count > 0 else 0.0
            currency = data["currency"]

            # Net sales = revenue - discounts - refunds
            net_sales = revenue - data["total_discounts"] - data["refund_amount"]

            metric_tuples = [
                ("revenue", revenue, "currency", currency),
                ("order_count", float(order_count), "count", None),
                ("avg_order_value", avg_order, "currency", currency),
                ("units_sold", float(data["units_sold"]), "count", None),
                ("total_discounts", data["total_discounts"], "currency", currency),
                ("total_tax", data["total_tax"], "currency", currency),
                ("net_sales", net_sales, "currency", currency),
                ("refund_amount", data["refund_amount"], "currency", currency),
                ("refund_count", float(data["refund_count"]), "count", None),
                ("shipping_revenue", data["shipping_revenue"], "currency", currency),
                (
                    "repeat_customers",
                    float(len(data["repeat_customer_ids"])),
                    "count",
                    None,
                ),
                (
                    "discount_usage_count",
                    float(data["discount_usage_count"]),
                    "count",
                    None,
                ),
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
                    ),
                )

        return metrics

    def _accumulate_order(self, order: dict, by_date: dict[date, dict]) -> None:
        """Accumulate a single Shopify order into the by-date buckets."""
        fin_status = order.get("financial_status", "")
        if fin_status == "voided":
            return

        d = self._parse_date(order.get("processed_at") or order.get("created_at", ""))
        if not d:
            return

        total_price = float(order.get("total_price", 0))
        current_total_price = float(order.get("current_total_price", 0) or 0)

        # Fully refunded orders: don't count revenue but track refund
        if fin_status == "refunded":
            by_date[d]["refund_amount"] += total_price
            by_date[d]["refund_count"] += 1
            by_date[d]["currency"] = order.get("currency", "USD")
            return

        by_date[d]["revenue"] += total_price
        by_date[d]["order_count"] += 1
        by_date[d]["currency"] = order.get("currency", "USD")

        # Discounts
        by_date[d]["total_discounts"] += float(order.get("total_discounts", 0))

        # Tax
        by_date[d]["total_tax"] += float(order.get("total_tax", 0))

        # Shipping revenue
        for sl in order.get("shipping_lines", []):
            by_date[d]["shipping_revenue"] += float(sl.get("price", 0))

        # Discount usage
        if order.get("discount_codes"):
            by_date[d]["discount_usage_count"] += 1

        # Partial refunds (order still active but partially refunded)
        if fin_status == "partially_refunded":
            refund_diff = total_price - current_total_price
            if refund_diff > 0:
                by_date[d]["refund_amount"] += refund_diff
                by_date[d]["refund_count"] += 1

        # Repeat customers
        customer = order.get("customer")
        if customer:
            cust_id = customer.get("id")
            orders_count = customer.get("orders_count", 1)
            if cust_id and orders_count and int(orders_count) > 1:
                by_date[d]["repeat_customer_ids"].add(cust_id)

        # Units sold
        for item in order.get("line_items", []):
            by_date[d]["units_sold"] += int(item.get("quantity", 1))

    @staticmethod
    def _parse_date(iso_str: str) -> date | None:
        if not iso_str:
            return None
        try:
            return datetime.fromisoformat(iso_str).date()
        except (ValueError, AttributeError):
            return None
