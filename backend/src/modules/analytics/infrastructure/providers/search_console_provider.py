"""SearchConsoleProvider — extracts Google Search Console metrics.

Channel slug: search-console
Metrics: impressions, clicks, ctr, avg_position, top_queries

Uses SearchConsoleAdapter.query_analytics() wrapped in asyncio.to_thread()
(sync Google SDK).
"""

from datetime import date
from uuid import UUID

import structlog
from google.auth.exceptions import RefreshError, TransportError

from src.modules.analytics.domain.exceptions import ConnectionRevokedError
from src.modules.analytics.domain.extraction_result import ExtractionResult
from src.modules.analytics.infrastructure.providers.base import (
    BaseMetricsProvider,
    ExtractedMetric,
)
from src.modules.connections.infrastructure.channels.search_console import (
    SearchConsoleAdapter,
)

logger = structlog.get_logger(__name__)


class SearchConsoleProvider(BaseMetricsProvider):
    """Extracts Google Search Console organic search metrics."""

    def provider_name(self) -> str:
        return "search_console"

    def rate_limit_config(self) -> dict:
        return {"requests_per_minute": 20, "burst_size": 10}

    async def extract_metrics_daily(
        self,
        tenant_id: UUID,
        credentials: dict,
        start_date: date,
        end_date: date,
        stage: str = "attraction",
    ) -> ExtractionResult:
        """Override: validate site_url once before delegating to per-day loop.

        Avoids logging 30+ warnings per sync when site_url is not configured.
        """
        site_url = credentials.get("site_url")
        if not site_url:
            logger.warning(
                "search_console_provider_no_site_url",
                tenant_id=str(tenant_id),
            )
            return ExtractionResult()
        return await super().extract_metrics_daily(
            tenant_id, credentials, start_date, end_date, stage=stage
        )

    async def extract_metrics(
        self,
        tenant_id: UUID,
        credentials: dict,
        start_date: date,
        end_date: date,
        stage: str = "attraction",
    ) -> ExtractionResult:
        if stage != "attraction":
            return ExtractionResult()

        site_url = credentials.get("site_url")
        if not site_url:
            # Warning is logged once in extract_metrics_daily — skip here
            return ExtractionResult()

        adapter = SearchConsoleAdapter(credentials_data=credentials)
        metrics: list[ExtractedMetric] = []

        try:
            # Aggregate totals (no dimensions)
            rows = await adapter.query_analytics(
                site_url=site_url,
                start_date=start_date,
                end_date=end_date,
            )
            if rows:
                row = rows[0]
                metrics.extend(
                    [
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
                    ]
                )

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
        except (RefreshError, TransportError) as exc:
            logger.warning(
                "search_console_extract_metrics_auth_failure",
                tenant_id=str(tenant_id),
                error=str(exc),
            )
            msg = f"Search Console OAuth token revoked/expired: {exc}"
            raise ConnectionRevokedError(
                msg,
                channel_type="search_console",
            ) from exc

        return ExtractionResult(metrics=metrics)
