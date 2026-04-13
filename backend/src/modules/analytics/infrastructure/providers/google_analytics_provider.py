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
from src.modules.connections.infrastructure.channels.google_analytics import (
    GoogleAnalyticsAdapter,
)

logger = structlog.get_logger(__name__)

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

    def has_period_extraction(self) -> bool:
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
        """Extract GA4 users/activeUsers for an exact date range.

        GA4 Data API natively deduplicates users across the entire range,
        so weekly/monthly/quarterly values are exact.
        """
        property_id = credentials.get("property_id")
        if not property_id:
            return ExtractionResult()

        adapter = self._build_adapter(credentials)

        # Map our metric names to GA4 API names
        ga4_metrics = []
        for name in metric_names:
            if name == "users":
                ga4_metrics.append("totalUsers")
            elif name == "activeUsers":
                ga4_metrics.append("activeUsers")

        if not ga4_metrics:
            return ExtractionResult()

        try:
            report = await adapter.run_report(
                property_id=property_id,
                dimensions=[],
                metrics=ga4_metrics,
                start_date=period_start.isoformat(),
                end_date=period_end.isoformat(),
            )
        except (RefreshError, TransportError) as exc:
            msg = f"Google Analytics OAuth token revoked/expired: {exc}"
            raise ConnectionRevokedError(
                msg,
                channel_type="google_analytics",
            ) from exc

        extracted = []
        rows = report.get("rows", [])
        if rows:
            row = rows[0]
            metric_values = row.get("metricValues", [])
            for i, ga4_name in enumerate(ga4_metrics):
                our_name = "users" if ga4_name == "totalUsers" else ga4_name
                val = (
                    float(metric_values[i].get("value", 0))
                    if i < len(metric_values)
                    else 0
                )
                extracted.append(
                    ExtractedMetric(
                        provider="google_analytics",
                        channel_slug="website-total",
                        metric_name=our_name,
                        value=val,
                        unit="count",
                        date=period_start,
                        extra={"period_type": period_type, "period_exact": True},
                    )
                )

        return ExtractionResult(metrics=extracted)

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
    ) -> ExtractionResult:
        property_id = credentials.get("property_id")
        if not property_id:
            logger.warning("ga_provider_no_property_id tenant=%s", tenant_id)
            return ExtractionResult()

        adapter = self._build_adapter(credentials)

        try:
            report = await adapter.run_report(
                property_id=property_id,
                dimensions=["sessionSource", "sessionMedium"],
                metrics=[
                    "sessions",
                    "totalUsers",
                    "bounceRate",
                    "engagedSessions",
                    "newUsers",
                    "screenPageViews",
                    "activeUsers",
                    "engagementRate",
                ],
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            )
        except (RefreshError, TransportError) as exc:
            logger.warning(
                "ga4_extract_metrics_auth_failure",
                tenant_id=str(tenant_id),
                error=str(exc),
            )
            msg = f"Google Analytics OAuth token revoked/expired: {exc}"
            raise ConnectionRevokedError(
                msg,
                channel_type="google_analytics",
            ) from exc

        results = self._segment_report(report, end_date)
        failures = []

        metrics, failure = await self._safe_extract(
            self._extract_website_aggregate,
            adapter,
            property_id,
            start_date,
            end_date,
            extractor_name="website_aggregate",
        )
        results.extend(metrics)
        if failure:
            failures.append(failure)

        metrics, failure = await self._safe_extract(
            self._extract_top_pages,
            adapter,
            property_id,
            start_date,
            end_date,
            extractor_name="top_pages",
        )
        results.extend(metrics)
        if failure:
            failures.append(failure)

        metrics, failure = await self._safe_extract(
            self._extract_traffic_sources,
            adapter,
            property_id,
            start_date,
            end_date,
            extractor_name="traffic_sources",
        )
        results.extend(metrics)
        if failure:
            failures.append(failure)

        metrics, failure = await self._safe_extract(
            self._extract_device_split,
            adapter,
            property_id,
            start_date,
            end_date,
            extractor_name="device_split",
        )
        results.extend(metrics)
        if failure:
            failures.append(failure)

        return ExtractionResult(metrics=results, failures=failures)

    # ── Website-total helpers ─────────────────────────────────────────

    async def _extract_website_aggregate(
        self,
        adapter: GoogleAnalyticsAdapter,
        property_id: str,
        start_date: date,
        end_date: date,
    ) -> list[ExtractedMetric]:
        """Site-wide totals with NO dimensions (aggregate across all traffic)."""
        report = await adapter.run_report(
            property_id=property_id,
            dimensions=[],
            metrics=_WEBSITE_GA4_METRICS,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )

        metrics: list[ExtractedMetric] = []
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

    async def _extract_top_pages(
        self,
        adapter: GoogleAnalyticsAdapter,
        property_id: str,
        start_date: date,
        end_date: date,
    ) -> list[ExtractedMetric]:
        """Top 10 pages by screenPageViews."""
        report = await adapter.run_report(
            property_id=property_id,
            dimensions=["pagePath"],
            metrics=["screenPageViews"],
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )

        pages: list[dict] = []
        for row in report.get("rows", []):
            dims = row.get("dimensions", [])
            mets = row.get("metrics", [])
            if dims and mets:
                pages.append(
                    {
                        "path": dims[0],
                        "views": int(float(mets[0])),
                    }
                )

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

    async def _extract_traffic_sources(
        self,
        adapter: GoogleAnalyticsAdapter,
        property_id: str,
        start_date: date,
        end_date: date,
    ) -> list[ExtractedMetric]:
        """Traffic sources by sessionDefaultChannelGroup."""
        report = await adapter.run_report(
            property_id=property_id,
            dimensions=["sessionDefaultChannelGroup"],
            metrics=["sessions"],
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )

        sources: list[dict] = []
        for row in report.get("rows", []):
            dims = row.get("dimensions", [])
            mets = row.get("metrics", [])
            if dims and mets:
                sources.append(
                    {
                        "channel": dims[0],
                        "sessions": int(float(mets[0])),
                    }
                )

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

    async def _extract_device_split(
        self,
        adapter: GoogleAnalyticsAdapter,
        property_id: str,
        start_date: date,
        end_date: date,
    ) -> list[ExtractedMetric]:
        """Device category split as percentages (mobile/desktop/tablet)."""
        report = await adapter.run_report(
            property_id=property_id,
            dimensions=["deviceCategory"],
            metrics=["sessions"],
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )

        device_counts: dict[str, float] = {}
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

    def _segment_report(self, report: dict, metric_date: date) -> list[ExtractedMetric]:
        """Segment GA4 report rows into channel slugs."""
        _empty_channel = {
            "sessions": 0.0,
            "users": 0.0,
            "bounceRate": 0.0,
            "engagedSessions": 0.0,
            "newUsers": 0.0,
            "screenPageViews": 0.0,
            "activeUsers": 0.0,
            "engagementRate": 0.0,
        }
        channel_data: dict[str, dict[str, float]] = {
            "google-organic": {**_empty_channel},
            "direct": {**_empty_channel},
            "ai-search-organic": {**_empty_channel},
        }
        # Track session counts for weighted bounceRate averaging
        _session_counts: dict[str, float] = {
            "google-organic": 0.0,
            "direct": 0.0,
            "ai-search-organic": 0.0,
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
        for slug, ch_data in channel_data.items():
            total_sess = _session_counts[slug]
            if total_sess > 0:
                ch_data["bounceRate"] /= total_sess
                ch_data["engagementRate"] /= total_sess
            else:
                ch_data["bounceRate"] = 0.0
                ch_data["engagementRate"] = 0.0

        # Convert to ExtractedMetric objects (skip channels with zero data)
        metrics: list[ExtractedMetric] = []
        for slug, data in channel_data.items():
            if data["sessions"] == 0.0 and data["users"] == 0.0:
                continue
            for metric_name, value in data.items():
                unit = (
                    "percentage"
                    if metric_name in ("bounceRate", "engagementRate")
                    else "count"
                )
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
    ) -> ExtractionResult:
        """Optimized daily extraction — GA4 API calls with date dimension."""
        property_id = credentials.get("property_id")
        if not property_id:
            return ExtractionResult()

        adapter = self._build_adapter(credentials)

        # Segmented report (source/medium + date)
        try:
            report = await adapter.run_report(
                property_id=property_id,
                dimensions=["sessionSource", "sessionMedium", "date"],
                metrics=[
                    "sessions",
                    "totalUsers",
                    "bounceRate",
                    "engagedSessions",
                    "newUsers",
                    "screenPageViews",
                    "activeUsers",
                    "engagementRate",
                ],
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
            )
        except (RefreshError, TransportError) as exc:
            logger.warning(
                "ga4_extract_metrics_daily_auth_failure",
                tenant_id=str(tenant_id),
                error=str(exc),
            )
            msg = f"Google Analytics OAuth token revoked/expired: {exc}"
            raise ConnectionRevokedError(
                msg,
                channel_type="google_analytics",
            ) from exc

        results = self._segment_report_daily(report)
        failures = []

        # Website-total daily (date only, no source/medium)
        metrics, failure = await self._safe_extract(
            self._extract_website_daily,
            adapter,
            property_id,
            start_date,
            end_date,
            extractor_name="website_daily",
        )
        results.extend(metrics)
        if failure:
            failures.append(failure)

        return ExtractionResult(metrics=results, failures=failures)

    async def _extract_website_daily(
        self,
        adapter: GoogleAnalyticsAdapter,
        property_id: str,
        start_date: date,
        end_date: date,
    ) -> list[ExtractedMetric]:
        """Website-total metrics per day — date dimension only, no source/medium."""
        from datetime import UTC
        from datetime import datetime as dt

        report = await adapter.run_report(
            property_id=property_id,
            dimensions=["date"],
            metrics=_WEBSITE_GA4_METRICS,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )

        metrics: list[ExtractedMetric] = []
        for row in report.get("rows", []):
            dims = row.get("dimensions", [])
            mets = row.get("metrics", [])
            if not dims or len(mets) < 2:
                continue

            try:
                metric_date = dt.strptime(dims[0], "%Y%m%d").replace(tzinfo=UTC).date()
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

    _GA4_METRIC_NAMES = [
        "sessions",
        "users",
        "bounceRate",
        "engagedSessions",
        "newUsers",
        "screenPageViews",
        "activeUsers",
        "engagementRate",
    ]

    def _segment_report_daily(self, report: dict) -> list[ExtractedMetric]:
        """Segment GA4 report rows with date dimension into per-day metrics."""
        day_data: dict[tuple, dict[str, float]] = {}
        day_sessions: dict[tuple, float] = {}

        for row in report.get("rows", []):
            self._accumulate_ga4_row(row, day_data, day_sessions)

        return self._build_ga4_daily_metrics(day_data, day_sessions)

    def _accumulate_ga4_row(
        self,
        row: dict,
        day_data: dict[tuple, dict[str, float]],
        day_sessions: dict[tuple, float],
    ) -> None:
        """Parse one GA4 report row and accumulate into day_data/day_sessions."""
        dims = row.get("dimensions", [])
        mets = row.get("metrics", [])
        if len(dims) < 3 or len(mets) < 2:
            return

        slug = self._classify_ga4_source(dims[0].lower(), dims[1].lower())
        if slug is None:
            return

        date_str = dims[2]
        key = (slug, date_str)
        if key not in day_data:
            day_data[key] = dict.fromkeys(self._GA4_METRIC_NAMES, 0.0)
            day_sessions[key] = 0.0

        sessions = float(mets[0])
        values = [
            float(mets[i]) if len(mets) > i else 0.0
            for i in range(len(self._GA4_METRIC_NAMES))
        ]

        day_data[key]["sessions"] += values[0]
        day_data[key]["users"] += values[1]
        day_data[key]["bounceRate"] += values[2] * sessions
        day_sessions[key] += sessions
        day_data[key]["engagedSessions"] += values[3]
        day_data[key]["newUsers"] += values[4]
        day_data[key]["screenPageViews"] += values[5]
        day_data[key]["activeUsers"] += values[6]
        day_data[key]["engagementRate"] += values[7] * sessions

    @staticmethod
    def _classify_ga4_source(source: str, medium: str) -> str | None:
        """Map GA4 source/medium to a channel slug, or None to skip."""
        if source in AI_REFERRER_DOMAINS:
            return "ai-search-organic"
        if source == "google" and medium == "organic":
            return "google-organic"
        if source == "(direct)" and medium == "(none)":
            return "direct"
        return None

    def _build_ga4_daily_metrics(
        self,
        day_data: dict[tuple, dict[str, float]],
        day_sessions: dict[tuple, float],
    ) -> list[ExtractedMetric]:
        """Finalize weighted rates and build ExtractedMetric list."""
        from datetime import UTC
        from datetime import datetime as dt

        metrics: list[ExtractedMetric] = []
        for (slug, date_str), data in day_data.items():
            try:
                metric_date = dt.strptime(date_str, "%Y%m%d").replace(tzinfo=UTC).date()
            except ValueError:
                continue

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
                unit = (
                    "percentage"
                    if metric_name in ("bounceRate", "engagementRate")
                    else "count"
                )
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
