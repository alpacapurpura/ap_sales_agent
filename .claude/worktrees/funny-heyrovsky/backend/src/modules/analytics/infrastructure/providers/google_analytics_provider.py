"""GoogleAnalyticsProvider — extracts GA4 search traffic metrics.

Segments GA4 sessions by source/medium into three channel slugs:
- google-organic: source=google, medium=organic
- direct: source=(direct), medium=(none)
- ai-search-organic: source in AI_REFERRER_DOMAINS

Uses existing GoogleAnalyticsAdapter.run_report() wrapped in
asyncio.to_thread() (sync Google SDK).
"""

import logging
from datetime import date
from typing import Dict, List
from uuid import UUID

from src.modules.analytics.infrastructure.providers.base import (
    BaseMetricsProvider,
    ExtractedMetric,
)
from src.modules.connections.infrastructure.channels.google_analytics import (
    GoogleAnalyticsAdapter,
)

logger = logging.getLogger(__name__)

# AI search referrer domains — configurable list for future expansion
AI_REFERRER_DOMAINS = {
    "perplexity.ai",
    "chatgpt.com",
    "claude.ai",
    "copilot.microsoft.com",
    "gemini.google.com",
    "you.com",
    "phind.com",
}


class GoogleAnalyticsProvider(BaseMetricsProvider):
    """Extracts GA4 search traffic segmented into organic, direct,
    and AI-search channels."""

    def provider_name(self) -> str:
        return "google_analytics"

    def rate_limit_config(self) -> dict:
        return {"requests_per_minute": 10, "burst_size": 5}

    async def extract_metrics(
        self,
        tenant_id: UUID,
        credentials: dict,
        start_date: date,
        end_date: date,
    ) -> List[ExtractedMetric]:
        property_id = credentials.get("property_id")
        if not property_id:
            logger.warning(
                "ga_provider_no_property_id tenant=%s", tenant_id
            )
            return []

        try:
            client_config = {
                "client_id": credentials.get("client_id", ""),
                "client_secret": credentials.get("client_secret", ""),
            }
            adapter = GoogleAnalyticsAdapter(
                client_config=client_config,
                credentials_data=credentials,
            )

            report = await adapter.run_report(
                property_id=property_id,
                dimensions=["sessionSource", "sessionMedium"],
                metrics=["sessions", "totalUsers"],
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            )

            return self._segment_report(report, end_date)
        except Exception:
            logger.exception(
                "ga_provider_extract_failed tenant=%s", tenant_id
            )
            return []

    def _segment_report(
        self, report: dict, metric_date: date
    ) -> List[ExtractedMetric]:
        """Segment GA4 report rows into channel slugs."""
        channel_data: Dict[str, Dict[str, float]] = {
            "google-organic": {"sessions": 0.0, "users": 0.0},
            "direct": {"sessions": 0.0, "users": 0.0},
            "ai-search-organic": {"sessions": 0.0, "users": 0.0},
        }

        for row in report.get("rows", []):
            dims = row.get("dimensions", [])
            mets = row.get("metrics", [])
            if len(dims) < 2 or len(mets) < 2:
                continue

            source = dims[0].lower()
            medium = dims[1].lower()
            sessions = float(mets[0])
            users = float(mets[1])

            if source in AI_REFERRER_DOMAINS:
                channel_data["ai-search-organic"]["sessions"] += sessions
                channel_data["ai-search-organic"]["users"] += users
            elif source == "google" and medium == "organic":
                channel_data["google-organic"]["sessions"] += sessions
                channel_data["google-organic"]["users"] += users
            elif source == "(direct)" and medium == "(none)":
                channel_data["direct"]["sessions"] += sessions
                channel_data["direct"]["users"] += users

        # Convert to ExtractedMetric objects (skip channels with zero data)
        metrics: List[ExtractedMetric] = []
        for slug, data in channel_data.items():
            if data["sessions"] == 0.0 and data["users"] == 0.0:
                continue
            for metric_name, value in data.items():
                metrics.append(
                    ExtractedMetric(
                        provider="google_analytics",
                        channel_slug=slug,
                        metric_name=metric_name,
                        value=value,
                        unit="count",
                        date=metric_date,
                    )
                )

        return metrics
