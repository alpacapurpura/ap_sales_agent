"""SearchConsoleProvider — extracts Google Search Console metrics.

Channel slug: search-console
Metrics: impressions, clicks, ctr, avg_position, top_queries

Uses SearchConsoleAdapter.query_analytics() wrapped in asyncio.to_thread()
(sync Google SDK).
"""
import logging
from datetime import date

import sentry_sdk
from typing import List
from uuid import UUID

from src.modules.analytics.infrastructure.providers.base import (
    BaseMetricsProvider,
    ExtractedMetric,
)
from src.modules.connections.infrastructure.channels.search_console import (
    SearchConsoleAdapter,
)

logger = logging.getLogger(__name__)


class SearchConsoleProvider(BaseMetricsProvider):
    """Extracts Google Search Console organic search metrics."""

    def provider_name(self) -> str:
        return "search_console"

    def rate_limit_config(self) -> dict:
        return {"requests_per_minute": 20, "burst_size": 10}

    async def extract_metrics(
        self,
        tenant_id: UUID,
        credentials: dict,
        start_date: date,
        end_date: date,
        stage: str = "attraction",
    ) -> List[ExtractedMetric]:
        if stage != "attraction":
            return []

        site_url = credentials.get("site_url")
        if not site_url:
            logger.warning(
                "search_console_provider_no_site_url tenant=%s", tenant_id
            )
            return []

        try:
            adapter = SearchConsoleAdapter(credentials_data=credentials)
            metrics: List[ExtractedMetric] = []

            # Aggregate totals (no dimensions)
            rows = await adapter.query_analytics(
                site_url=site_url,
                start_date=start_date,
                end_date=end_date,
            )
            if rows:
                row = rows[0]
                metrics.extend([
                    ExtractedMetric(
                        provider="search_console",
                        channel_slug="search-console",
                        metric_name="impressions",
                        value=float(row.get("impressions", 0)),
                        unit="count",
                        date=end_date,
                    ),
                    ExtractedMetric(
                        provider="search_console",
                        channel_slug="search-console",
                        metric_name="clicks",
                        value=float(row.get("clicks", 0)),
                        unit="count",
                        date=end_date,
                    ),
                    ExtractedMetric(
                        provider="search_console",
                        channel_slug="search-console",
                        metric_name="ctr",
                        value=float(row.get("ctr", 0)) * 100,
                        unit="percentage",
                        date=end_date,
                    ),
                    ExtractedMetric(
                        provider="search_console",
                        channel_slug="search-console",
                        metric_name="avg_position",
                        value=float(row.get("position", 0)),
                        unit="count",
                        date=end_date,
                    ),
                ])

            # Top queries (dimension: query)
            query_rows = await adapter.query_analytics(
                site_url=site_url,
                start_date=start_date,
                end_date=end_date,
                dimensions=["query"],
                row_limit=20,
            )
            if query_rows:
                terms = [
                    {
                        "query": r["keys"][0],
                        "clicks": int(r.get("clicks", 0)),
                        "impressions": int(r.get("impressions", 0)),
                        "ctr": round(float(r.get("ctr", 0)) * 100, 2),
                        "position": round(float(r.get("position", 0)), 1),
                    }
                    for r in query_rows
                ]
                metrics.append(
                    ExtractedMetric(
                        provider="search_console",
                        channel_slug="search-console",
                        metric_name="top_queries",
                        value=0.0,
                        unit="json",
                        date=end_date,
                        extra={"queries": terms},
                    )
                )

            return metrics
        except Exception:
            sentry_sdk.capture_exception()
            logger.exception(
                "search_console_provider_extract_failed tenant=%s", tenant_id
            )
            return []
