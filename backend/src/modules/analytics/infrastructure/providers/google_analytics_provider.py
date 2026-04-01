"""GoogleAnalyticsProvider — extracts GA4 search traffic metrics.

Segments GA4 sessions by source/medium into three channel slugs:
- google-organic: source=google, medium=organic
- direct: source=(direct), medium=(none)
- ai-search-organic: source in AI_REFERRER_DOMAINS

Also extracts site-wide aggregate metrics (website-total), top pages,
traffic sources, and device split for the Website Visits feature.

Uses existing GoogleAnalyticsAdapter.run_report() wrapped in
asyncio.to_thread() (sync Google SDK).
"""

import logging
from datetime import date

import sentry_sdk
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

# GA4 metric names → (our metric_name, unit) for website-total aggregate
_WEBSITE_METRIC_MAP = {
    "sessions": ("sessions", "count"),
    "totalUsers": ("users", "count"),
    "newUsers": ("newUsers", "count"),
    "bounceRate": ("bounceRate", "percentage"),
    "engagedSessions": ("engagedSessions", "count"),
    "screenPageViews": ("screenPageViews", "count"),
    "averageSessionDuration": ("averageSessionDuration", "count"),
    "conversions": ("conversions", "count"),
    "activeUsers": ("activeUsers", "count"),
    "engagementRate": ("engagementRate", "percentage"),
}

# Ordered list of GA4 metric names for website-total requests
_WEBSITE_GA4_METRICS = list(_WEBSITE_METRIC_MAP.keys())


class GoogleAnalyticsProvider(BaseMetricsProvider):
    """Extracts GA4 search traffic segmented into organic, direct,
    and AI-search channels, plus site-wide website-total metrics."""

    def provider_name(self) -> str:
        return "google_analytics"

    def rate_limit_config(self) -> dict:
        return {"requests_per_minute": 20, "burst_size": 10}

    def _build_adapter(self, credentials: dict) -> GoogleAnalyticsAdapter:
        """Build a GoogleAnalyticsAdapter from credentials."""
        client_config = {
            "client_id": credentials.get("client_id", ""),
            "client_secret": credentials.get("client_secret", ""),
        }
        return GoogleAnalyticsAdapter(
            client_config=client_config,
            credentials_data=credentials,
        )

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
            adapter = self._build_adapter(credentials)

            report = await adapter.run_report(
                property_id=property_id,
                dimensions=["sessionSource", "sessionMedium"],
                metrics=[
                    "sessions", "totalUsers", "bounceRate",
                    "engagedSessions", "newUsers", "screenPageViews",
                    "activeUsers", "engagementRate",
                ],
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            )

            results = self._segment_report(report, end_date)

            # Website-total aggregate + enrichment metrics
            results.extend(
                await self._extract_website_aggregate(
                    adapter, property_id, start_date, end_date
                )
            )
            results.extend(
                await self._extract_top_pages(
                    adapter, property_id, start_date, end_date
                )
            )
            results.extend(
                await self._extract_traffic_sources(
                    adapter, property_id, start_date, end_date
                )
            )
            results.extend(
                await self._extract_device_split(
                    adapter, property_id, start_date, end_date
                )
            )

            return results
        except Exception:
            sentry_sdk.capture_exception()
            logger.exception(
                "ga_provider_extract_failed tenant=%s", tenant_id
            )
            return []

    # ── Website-total helpers ─────────────────────────────────────────

    async def _extract_website_aggregate(
        self,
        adapter: GoogleAnalyticsAdapter,
        property_id: str,
        start_date: date,
        end_date: date,
    ) -> List[ExtractedMetric]:
        """Site-wide totals with NO dimensions (aggregate across all traffic)."""
        try:
            report = await adapter.run_report(
                property_id=property_id,
                dimensions=[],
                metrics=_WEBSITE_GA4_METRICS,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            )

            metrics: List[ExtractedMetric] = []
            for row in report.get("rows", []):
                mets = row.get("metrics", [])
                for i, ga4_name in enumerate(_WEBSITE_GA4_METRICS):
                    if i >= len(mets):
                        break
                    metric_name, unit = _WEBSITE_METRIC_MAP[ga4_name]
                    metrics.append(
                        ExtractedMetric(
                            provider="google_analytics",
                            channel_slug="website-total",
                            metric_name=metric_name,
                            value=float(mets[i]),
                            unit=unit,
                            date=end_date,
                        )
                    )
            return metrics
        except Exception:
            sentry_sdk.capture_exception()
            logger.exception("ga_website_aggregate_failed")
            return []

    async def _extract_top_pages(
        self,
        adapter: GoogleAnalyticsAdapter,
        property_id: str,
        start_date: date,
        end_date: date,
    ) -> List[ExtractedMetric]:
        """Top 10 pages by screenPageViews."""
        try:
            report = await adapter.run_report(
                property_id=property_id,
                dimensions=["pagePath"],
                metrics=["screenPageViews"],
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            )

            pages: List[Dict] = []
            for row in report.get("rows", []):
                dims = row.get("dimensions", [])
                mets = row.get("metrics", [])
                if dims and mets:
                    pages.append({
                        "path": dims[0],
                        "views": int(float(mets[0])),
                    })

            # Sort descending by views, take top 10
            pages.sort(key=lambda p: p["views"], reverse=True)
            pages = pages[:10]

            if not pages:
                return []

            return [
                ExtractedMetric(
                    provider="google_analytics",
                    channel_slug="website-total",
                    metric_name="top_pages",
                    value=0.0,
                    unit="json",
                    date=end_date,
                    extra={"pages": pages},
                )
            ]
        except Exception:
            sentry_sdk.capture_exception()
            logger.exception("ga_top_pages_failed")
            return []

    async def _extract_traffic_sources(
        self,
        adapter: GoogleAnalyticsAdapter,
        property_id: str,
        start_date: date,
        end_date: date,
    ) -> List[ExtractedMetric]:
        """Traffic sources by sessionDefaultChannelGroup."""
        try:
            report = await adapter.run_report(
                property_id=property_id,
                dimensions=["sessionDefaultChannelGroup"],
                metrics=["sessions"],
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            )

            sources: List[Dict] = []
            for row in report.get("rows", []):
                dims = row.get("dimensions", [])
                mets = row.get("metrics", [])
                if dims and mets:
                    sources.append({
                        "channel": dims[0],
                        "sessions": int(float(mets[0])),
                    })

            # Sort descending by sessions
            sources.sort(key=lambda s: s["sessions"], reverse=True)

            if not sources:
                return []

            return [
                ExtractedMetric(
                    provider="google_analytics",
                    channel_slug="website-total",
                    metric_name="traffic_sources",
                    value=0.0,
                    unit="json",
                    date=end_date,
                    extra={"sources": sources},
                )
            ]
        except Exception:
            sentry_sdk.capture_exception()
            logger.exception("ga_traffic_sources_failed")
            return []

    async def _extract_device_split(
        self,
        adapter: GoogleAnalyticsAdapter,
        property_id: str,
        start_date: date,
        end_date: date,
    ) -> List[ExtractedMetric]:
        """Device category split as percentages (mobile/desktop/tablet)."""
        try:
            report = await adapter.run_report(
                property_id=property_id,
                dimensions=["deviceCategory"],
                metrics=["sessions"],
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            )

            device_counts: Dict[str, float] = {}
            total = 0.0
            for row in report.get("rows", []):
                dims = row.get("dimensions", [])
                mets = row.get("metrics", [])
                if dims and mets:
                    count = float(mets[0])
                    device_counts[dims[0].lower()] = count
                    total += count

            if total == 0:
                return []

            split = {
                "mobile": round(device_counts.get("mobile", 0) / total * 100, 1),
                "desktop": round(device_counts.get("desktop", 0) / total * 100, 1),
                "tablet": round(device_counts.get("tablet", 0) / total * 100, 1),
            }

            return [
                ExtractedMetric(
                    provider="google_analytics",
                    channel_slug="website-total",
                    metric_name="device_split",
                    value=0.0,
                    unit="json",
                    date=end_date,
                    extra=split,
                )
            ]
        except Exception:
            sentry_sdk.capture_exception()
            logger.exception("ga_device_split_failed")
            return []

    def _segment_report(
        self, report: dict, metric_date: date
    ) -> List[ExtractedMetric]:
        """Segment GA4 report rows into channel slugs."""
        _EMPTY_CHANNEL = {
            "sessions": 0.0, "users": 0.0, "bounceRate": 0.0,
            "engagedSessions": 0.0, "newUsers": 0.0, "screenPageViews": 0.0,
            "activeUsers": 0.0, "engagementRate": 0.0,
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
            active_users = float(mets[6]) if len(mets) > 6 else 0.0
            engagement_rate = float(mets[7]) if len(mets) > 7 else 0.0

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
            channel_data[slug]["activeUsers"] += active_users
            # engagementRate: weighted sum (multiply by sessions, divide later)
            channel_data[slug]["engagementRate"] += engagement_rate * sessions

        # Finalize weighted bounceRate and engagementRate
        for slug in channel_data:
            total_sess = _session_counts[slug]
            if total_sess > 0:
                channel_data[slug]["bounceRate"] /= total_sess
                channel_data[slug]["engagementRate"] /= total_sess
            else:
                channel_data[slug]["bounceRate"] = 0.0
                channel_data[slug]["engagementRate"] = 0.0

        # Convert to ExtractedMetric objects (skip channels with zero data)
        metrics: List[ExtractedMetric] = []
        for slug, data in channel_data.items():
            if data["sessions"] == 0.0 and data["users"] == 0.0:
                continue
            for metric_name, value in data.items():
                unit = "percentage" if metric_name in ("bounceRate", "engagementRate") else "count"
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
        """Optimized daily extraction — GA4 API calls with date dimension."""
        property_id = credentials.get("property_id")
        if not property_id:
            return []

        try:
            adapter = self._build_adapter(credentials)

            # Segmented report (source/medium + date)
            report = await adapter.run_report(
                property_id=property_id,
                dimensions=["sessionSource", "sessionMedium", "date"],
                metrics=[
                    "sessions", "totalUsers", "bounceRate",
                    "engagedSessions", "newUsers", "screenPageViews",
                    "activeUsers", "engagementRate",
                ],
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            )

            results = self._segment_report_daily(report)

            # Website-total daily (date only, no source/medium)
            results.extend(
                await self._extract_website_daily(
                    adapter, property_id, start_date, end_date
                )
            )

            return results
        except Exception:
            sentry_sdk.capture_exception()
            logger.exception(
                "ga_provider_extract_daily_failed tenant=%s", tenant_id
            )
            return []

    async def _extract_website_daily(
        self,
        adapter: GoogleAnalyticsAdapter,
        property_id: str,
        start_date: date,
        end_date: date,
    ) -> List[ExtractedMetric]:
        """Website-total metrics per day — date dimension only, no source/medium."""
        from datetime import datetime as dt

        try:
            report = await adapter.run_report(
                property_id=property_id,
                dimensions=["date"],
                metrics=_WEBSITE_GA4_METRICS,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            )

            metrics: List[ExtractedMetric] = []
            for row in report.get("rows", []):
                dims = row.get("dimensions", [])
                mets = row.get("metrics", [])
                if not dims or len(mets) < 2:
                    continue

                try:
                    metric_date = dt.strptime(dims[0], "%Y%m%d").date()
                except ValueError:
                    continue

                for i, ga4_name in enumerate(_WEBSITE_GA4_METRICS):
                    if i >= len(mets):
                        break
                    metric_name, unit = _WEBSITE_METRIC_MAP[ga4_name]
                    metrics.append(
                        ExtractedMetric(
                            provider="google_analytics",
                            channel_slug="website-total",
                            metric_name=metric_name,
                            value=float(mets[i]),
                            unit=unit,
                            date=metric_date,
                        )
                    )
            return metrics
        except Exception:
            sentry_sdk.capture_exception()
            logger.exception("ga_website_daily_failed")
            return []

    def _segment_report_daily(
        self, report: dict
    ) -> List[ExtractedMetric]:
        """Segment GA4 report rows with date dimension into per-day metrics."""
        from datetime import datetime as dt

        _METRIC_NAMES = [
            "sessions", "users", "bounceRate",
            "engagedSessions", "newUsers", "screenPageViews",
            "activeUsers", "engagementRate",
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
            active_users = float(mets[6]) if len(mets) > 6 else 0.0
            engagement_rate = float(mets[7]) if len(mets) > 7 else 0.0

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
            day_data[key]["activeUsers"] += active_users
            # engagementRate: weighted sum (multiply by sessions, divide later)
            day_data[key]["engagementRate"] += engagement_rate * sessions

        metrics: List[ExtractedMetric] = []
        for (slug, date_str), data in day_data.items():
            # Parse GA4 date (YYYYMMDD)
            try:
                metric_date = dt.strptime(date_str, "%Y%m%d").date()
            except ValueError:
                continue

            # Finalize weighted bounceRate and engagementRate
            total_sess = day_sessions[(slug, date_str)]
            if total_sess > 0:
                data["bounceRate"] /= total_sess
                data["engagementRate"] /= total_sess
            else:
                data["bounceRate"] = 0.0
                data["engagementRate"] = 0.0

            if data["sessions"] == 0.0 and data["users"] == 0.0:
                continue

            for metric_name, value in data.items():
                unit = "percentage" if metric_name in ("bounceRate", "engagementRate") else "count"
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
