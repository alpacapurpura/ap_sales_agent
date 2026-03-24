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
        stage: str = "attraction",
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
                metrics=[
                    "sessions", "totalUsers", "bounceRate",
                    "engagedSessions", "newUsers", "screenPageViews",
                ],
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
        _EMPTY_CHANNEL = {
            "sessions": 0.0, "users": 0.0, "bounceRate": 0.0,
            "engagedSessions": 0.0, "newUsers": 0.0, "screenPageViews": 0.0,
        }
        channel_data: Dict[str, Dict[str, float]] = {
            "google-organic": {**_EMPTY_CHANNEL},
            "direct": {**_EMPTY_CHANNEL},
            "ai-search-organic": {**_EMPTY_CHANNEL},
        }
        # Track session counts for weighted bounceRate averaging
        _session_counts: Dict[str, float] = {
            "google-organic": 0.0, "direct": 0.0, "ai-search-organic": 0.0,
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
            bounce_rate = float(mets[2]) if len(mets) > 2 else 0.0
            engaged_sessions = float(mets[3]) if len(mets) > 3 else 0.0
            new_users = float(mets[4]) if len(mets) > 4 else 0.0
            page_views = float(mets[5]) if len(mets) > 5 else 0.0

            if source in AI_REFERRER_DOMAINS:
                slug = "ai-search-organic"
            elif source == "google" and medium == "organic":
                slug = "google-organic"
            elif source == "(direct)" and medium == "(none)":
                slug = "direct"
            else:
                continue

            channel_data[slug]["sessions"] += sessions
            channel_data[slug]["users"] += users
            # bounceRate: weighted sum (multiply by sessions, divide later)
            channel_data[slug]["bounceRate"] += bounce_rate * sessions
            _session_counts[slug] += sessions
            channel_data[slug]["engagedSessions"] += engaged_sessions
            channel_data[slug]["newUsers"] += new_users
            channel_data[slug]["screenPageViews"] += page_views

        # Finalize weighted bounceRate
        for slug in channel_data:
            total_sess = _session_counts[slug]
            if total_sess > 0:
                channel_data[slug]["bounceRate"] /= total_sess
            else:
                channel_data[slug]["bounceRate"] = 0.0

        # Convert to ExtractedMetric objects (skip channels with zero data)
        metrics: List[ExtractedMetric] = []
        for slug, data in channel_data.items():
            if data["sessions"] == 0.0 and data["users"] == 0.0:
                continue
            for metric_name, value in data.items():
                unit = "percentage" if metric_name == "bounceRate" else "count"
                metrics.append(
                    ExtractedMetric(
                        provider="google_analytics",
                        channel_slug=slug,
                        metric_name=metric_name,
                        value=value,
                        unit=unit,
                        date=metric_date,
                    )
                )

        return metrics

    async def extract_metrics_daily(
        self,
        tenant_id: UUID,
        credentials: dict,
        start_date: date,
        end_date: date,
        stage: str = "attraction",
    ) -> List[ExtractedMetric]:
        """Optimized daily extraction — single GA4 API call with date dimension."""
        property_id = credentials.get("property_id")
        if not property_id:
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
                dimensions=["sessionSource", "sessionMedium", "date"],
                metrics=[
                    "sessions", "totalUsers", "bounceRate",
                    "engagedSessions", "newUsers", "screenPageViews",
                ],
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            )

            return self._segment_report_daily(report)
        except Exception:
            logger.exception(
                "ga_provider_extract_daily_failed tenant=%s", tenant_id
            )
            return []

    def _segment_report_daily(
        self, report: dict
    ) -> List[ExtractedMetric]:
        """Segment GA4 report rows with date dimension into per-day metrics."""
        from datetime import datetime as dt

        _METRIC_NAMES = [
            "sessions", "users", "bounceRate",
            "engagedSessions", "newUsers", "screenPageViews",
        ]

        # Accumulate: (slug, date_str) -> {metric: value}
        day_data: Dict[tuple, Dict[str, float]] = {}
        day_sessions: Dict[tuple, float] = {}

        for row in report.get("rows", []):
            dims = row.get("dimensions", [])
            mets = row.get("metrics", [])
            if len(dims) < 3 or len(mets) < 2:
                continue

            source = dims[0].lower()
            medium = dims[1].lower()
            date_str = dims[2]  # YYYYMMDD format from GA4

            if source in AI_REFERRER_DOMAINS:
                slug = "ai-search-organic"
            elif source == "google" and medium == "organic":
                slug = "google-organic"
            elif source == "(direct)" and medium == "(none)":
                slug = "direct"
            else:
                continue

            sessions = float(mets[0])
            users = float(mets[1])
            bounce_rate = float(mets[2]) if len(mets) > 2 else 0.0
            engaged_sessions = float(mets[3]) if len(mets) > 3 else 0.0
            new_users = float(mets[4]) if len(mets) > 4 else 0.0
            page_views = float(mets[5]) if len(mets) > 5 else 0.0

            key = (slug, date_str)
            if key not in day_data:
                day_data[key] = {m: 0.0 for m in _METRIC_NAMES}
                day_sessions[key] = 0.0

            day_data[key]["sessions"] += sessions
            day_data[key]["users"] += users
            day_data[key]["bounceRate"] += bounce_rate * sessions
            day_sessions[key] += sessions
            day_data[key]["engagedSessions"] += engaged_sessions
            day_data[key]["newUsers"] += new_users
            day_data[key]["screenPageViews"] += page_views

        metrics: List[ExtractedMetric] = []
        for (slug, date_str), data in day_data.items():
            # Parse GA4 date (YYYYMMDD)
            try:
                metric_date = dt.strptime(date_str, "%Y%m%d").date()
            except ValueError:
                continue

            # Finalize weighted bounceRate
            total_sess = day_sessions[(slug, date_str)]
            if total_sess > 0:
                data["bounceRate"] /= total_sess
            else:
                data["bounceRate"] = 0.0

            if data["sessions"] == 0.0 and data["users"] == 0.0:
                continue

            for metric_name, value in data.items():
                unit = "percentage" if metric_name == "bounceRate" else "count"
                metrics.append(
                    ExtractedMetric(
                        provider="google_analytics",
                        channel_slug=slug,
                        metric_name=metric_name,
                        value=value,
                        unit=unit,
                        date=metric_date,
                    )
                )

        return metrics
