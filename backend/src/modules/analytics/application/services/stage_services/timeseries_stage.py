"""Time series stage service — extracted from MetricsService.

Handles get_stage_timeseries() logic: daily/weekly chart data
for any funnel stage, grouped by channel.
"""

from collections import OrderedDict
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.analytics.application.dto.timeseries_dto import (
    ChannelInfoDTO,
    StageTimeSeriesDTO,
    TimeSeriesPointDTO,
)
from src.modules.analytics.domain.ports import ConnectionPort
from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache

# Suggested hex colors per channel slug (frontend may override)
_CHANNEL_COLORS: dict[str, str] = {
    "meta-ads": "#1877F2",
    "ig-organic": "#E4405F",
    "fb-organic": "#1877F2",
    "google-ads": "#EA4335",
    "google-organic": "#34A853",
    "yt-organic": "#FF0000",
    "yt-ads": "#FF0000",
    "tiktok-organic": "#00F2EA",
    "tiktok-ads": "#00F2EA",
    "direct": "#6B7280",
    "ai-search-organic": "#8B5CF6",
    "manychat-comments": "#0084FF",
    "linkedin-organic": "#0A66C2",
    "email-capture": "#F59E0B",
    "cold-contact": "#6B7280",
}


def _build_date_map(rows: list) -> tuple[OrderedDict, set]:
    """Build date→channel→value map and set of seen channels from query rows."""
    date_map: OrderedDict = OrderedDict()
    channels_seen: set = set()
    for row in rows:
        d = row.metric_date
        channels_seen.add(row.channel_slug)
        if d not in date_map:
            date_map[d] = {}
        date_map[d][row.channel_slug] = date_map[d].get(row.channel_slug, 0) + float(
            row.total,
        )
    return date_map, channels_seen


def _compute_period_totals(date_map: OrderedDict) -> dict[str, float]:
    """Sum values per channel across all dates."""
    totals: dict[str, float] = {}
    for ch_vals in date_map.values():
        for slug, val in ch_vals.items():
            totals[slug] = totals.get(slug, 0) + val
    return totals


class TimeseriesStageService:
    """Provides time-series data for funnel stages."""

    def __init__(
        self,
        db: Session,
        cache: MetricsCache | None = None,
        connection_port: ConnectionPort | None = None,
    ):
        self.db = db
        self.cache = cache
        self.connection_port = connection_port

    @staticmethod
    def _resolve_metric_aliases(metric_name: str) -> list[str]:
        """Map frontend metric names to possible DB column names."""
        aliases: dict[str, list[str]] = {
            "visitors": ["sessions", "users", "visitors"],
            "leads": ["leads", "new_subscribers"],
        }
        return aliases.get(metric_name, [metric_name])

    @staticmethod
    def _aggregate_weekly(
        date_map: "OrderedDict",
    ) -> "OrderedDict":
        """Collapse daily data points into ISO-week buckets."""
        from datetime import timedelta

        weekly_map: OrderedDict = OrderedDict()
        for d, ch_vals in date_map.items():
            week_start = d - timedelta(days=d.weekday())
            if week_start not in weekly_map:
                weekly_map[week_start] = {}
            for slug, val in ch_vals.items():
                weekly_map[week_start][slug] = weekly_map[week_start].get(slug, 0) + val
        return weekly_map

    def _query_current_period(
        self,
        tenant_id: UUID,
        channel_slugs: list[str],
        db_metric_names: list[str],
        start_date,
        now,
    ) -> list:
        """Query official_metrics for the current period."""
        from sqlalchemy import func as sa_f
        from sqlalchemy import select as sa_select

        from src.modules.analytics.infrastructure.models.official_metrics_model import (
            OfficialMetricModel,
        )

        m = OfficialMetricModel
        stmt = (
            sa_select(m.metric_date, m.channel_slug, sa_f.sum(m.value).label("total"))
            .where(
                m.tenant_id == tenant_id,
                m.channel_slug.in_(channel_slugs),
                m.metric_name.in_(db_metric_names),
                m.metric_date >= start_date,
                m.metric_date <= now,
            )
            .group_by(m.metric_date, m.channel_slug)
            .order_by(m.metric_date)
        )
        return self.db.execute(stmt).all()

    def _query_previous_period(
        self,
        tenant_id: UUID,
        channel_slugs: list[str],
        db_metric_names: list[str],
        prev_start,
        start_date,
    ) -> dict[str, float] | None:
        """Query previous period totals for delta% calculation."""
        from sqlalchemy import func as sa_f
        from sqlalchemy import select as sa_select

        from src.modules.analytics.infrastructure.models.official_metrics_model import (
            OfficialMetricModel,
        )

        m = OfficialMetricModel
        prev_stmt = (
            sa_select(m.channel_slug, sa_f.sum(m.value).label("total"))
            .where(
                m.tenant_id == tenant_id,
                m.channel_slug.in_(channel_slugs),
                m.metric_name.in_(db_metric_names),
                m.metric_date >= prev_start,
                m.metric_date < start_date,
            )
            .group_by(m.channel_slug)
        )
        prev_rows = self.db.execute(prev_stmt).all()
        return (
            {row.channel_slug: float(row.total) for row in prev_rows}
            if prev_rows
            else None
        )

    async def get_timeseries(
        self,
        tenant_id: UUID,
        stage: str,
        metric_name: str = "visitors",
        range_days: int = 30,
        granularity: str = "daily",
    ) -> StageTimeSeriesDTO:
        """Return time-series data for a funnel stage, grouped by channel and date."""
        from src.modules.analytics.application.services.channel_registry import (
            get_stage_channels,
        )

        tid = str(tenant_id)

        # 1. Check cache
        cache_period = f"ts:{metric_name}:{range_days}:{granularity}"
        if self.cache is not None:
            cached = await self.cache.get(tid, stage, cache_period)
            if cached is not None:
                return StageTimeSeriesDTO(**cached)

        # 2. Get channel slugs for this stage
        stage_channels = get_stage_channels(stage)
        slug_to_info = {ch["slug"]: ch for ch in stage_channels}
        channel_slugs = list(slug_to_info.keys())

        if not channel_slugs:
            return StageTimeSeriesDTO(
                stage=stage,
                metric_name=metric_name,
                granularity=granularity,
                range_days=range_days,
                data_points=[],
                channels_present=[],
                period_totals={},
                previous_period_totals=None,
            )

        # 3. Date ranges
        from datetime import timedelta

        now = datetime.now(UTC).date()
        start_date = now - timedelta(days=range_days)
        prev_start = start_date - timedelta(days=range_days)
        db_metric_names = self._resolve_metric_aliases(metric_name)

        # 4. Query & build data points
        rows = self._query_current_period(
            tenant_id,
            channel_slugs,
            db_metric_names,
            start_date,
            now,
        )
        date_map, channels_seen = _build_date_map(rows)

        if granularity == "weekly" and date_map:
            date_map = self._aggregate_weekly(date_map)

        data_points = [
            TimeSeriesPointDTO(date=d.isoformat(), channels=ch_vals)
            for d, ch_vals in date_map.items()
        ]

        # 5. Totals
        period_totals = _compute_period_totals(date_map)
        previous_period_totals = self._query_previous_period(
            tenant_id,
            channel_slugs,
            db_metric_names,
            prev_start,
            start_date,
        )

        # 6. Build channels_present
        channels_present = [
            ChannelInfoDTO(
                slug=slug,
                name=slug_to_info.get(slug, {}).get("name", slug),
                color=_CHANNEL_COLORS.get(slug, "#6B7280"),
            )
            for slug in sorted(channels_seen)
        ]

        result = StageTimeSeriesDTO(
            stage=stage,
            metric_name=metric_name,
            granularity=granularity,
            range_days=range_days,
            data_points=data_points,
            channels_present=channels_present,
            period_totals=period_totals,
            previous_period_totals=previous_period_totals,
        )

        if self.cache is not None:
            await self.cache.set(tid, stage, cache_period, result.model_dump())

        return result
