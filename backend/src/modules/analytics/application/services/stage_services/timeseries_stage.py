"""Time series stage service — extracted from MetricsService.

Handles get_stage_timeseries() logic: daily/weekly chart data
for any funnel stage, grouped by channel.
"""

from collections import OrderedDict
from datetime import datetime
from typing import Dict, Optional
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
_CHANNEL_COLORS: Dict[str, str] = {
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


class TimeseriesStageService:
    """Provides time-series data for funnel stages."""

    def __init__(
        self,
        db: Session,
        cache: Optional[MetricsCache] = None,
        connection_port: Optional[ConnectionPort] = None,
    ):
        self.db = db
        self.cache = cache
        self.connection_port = connection_port

    async def get_timeseries(
        self,
        tenant_id: UUID,
        stage: str,
        metric_name: str = "visitors",
        range_days: int = 30,
        granularity: str = "daily",
    ) -> StageTimeSeriesDTO:
        """Return time-series data for a funnel stage, grouped by channel and date.

        Queries official_metrics WHERE tenant_id AND channel_slug IN (stage channels)
        AND metric_name = X, GROUP BY metric_date, channel_slug.
        Includes previous-period totals for delta% calculation.
        """
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
        slug_to_info = {
            ch["slug"]: ch for ch in stage_channels
        }
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

        # 3. Query current period
        from datetime import date as date_type, timedelta, timezone as tz

        now = datetime.now(tz.utc).date()
        start_date = now - timedelta(days=range_days)
        prev_start = start_date - timedelta(days=range_days)

        # Map metric aliases: frontend sends "visitors" but DB may have "sessions"
        db_metric_names = [metric_name]
        if metric_name == "visitors":
            db_metric_names = ["sessions", "users", "visitors"]
        elif metric_name == "leads":
            db_metric_names = ["leads", "new_subscribers"]

        from sqlalchemy import select as sa_select, func as sa_f
        from src.modules.analytics.infrastructure.models.official_metrics_model import (
            OfficialMetricModel,
        )

        M = OfficialMetricModel

        # Current period: group by date, channel_slug
        stmt = (
            sa_select(
                M.metric_date,
                M.channel_slug,
                sa_f.sum(M.value).label("total"),
            )
            .where(
                M.tenant_id == tenant_id,
                M.channel_slug.in_(channel_slugs),
                M.metric_name.in_(db_metric_names),
                M.metric_date >= start_date,
                M.metric_date <= now,
            )
            .group_by(M.metric_date, M.channel_slug)
            .order_by(M.metric_date)
        )
        rows = self.db.execute(stmt).all()

        # 4. Build data points
        date_map: Dict[date_type, Dict[str, float]] = OrderedDict()
        channels_seen: set = set()

        for row in rows:
            d = row.metric_date
            slug = row.channel_slug
            val = float(row.total)
            channels_seen.add(slug)
            if d not in date_map:
                date_map[d] = {}
            date_map[d][slug] = date_map[d].get(slug, 0) + val

        # Weekly aggregation if requested
        if granularity == "weekly" and date_map:
            weekly_map: Dict[date_type, Dict[str, float]] = OrderedDict()
            for d, ch_vals in date_map.items():
                # ISO week start (Monday)
                week_start = d - timedelta(days=d.weekday())
                if week_start not in weekly_map:
                    weekly_map[week_start] = {}
                for slug, val in ch_vals.items():
                    weekly_map[week_start][slug] = (
                        weekly_map[week_start].get(slug, 0) + val
                    )
            date_map = weekly_map

        data_points = [
            TimeSeriesPointDTO(
                date=d.isoformat(),
                channels=ch_vals,
            )
            for d, ch_vals in date_map.items()
        ]

        # 5. Period totals
        period_totals: Dict[str, float] = {}
        for ch_vals in date_map.values():
            for slug, val in ch_vals.items():
                period_totals[slug] = period_totals.get(slug, 0) + val

        # 6. Previous period totals
        prev_stmt = (
            sa_select(
                M.channel_slug,
                sa_f.sum(M.value).label("total"),
            )
            .where(
                M.tenant_id == tenant_id,
                M.channel_slug.in_(channel_slugs),
                M.metric_name.in_(db_metric_names),
                M.metric_date >= prev_start,
                M.metric_date < start_date,
            )
            .group_by(M.channel_slug)
        )
        prev_rows = self.db.execute(prev_stmt).all()
        previous_period_totals = {
            row.channel_slug: float(row.total) for row in prev_rows
        } if prev_rows else None

        # 7. Build channels_present
        channels_present = []
        for slug in sorted(channels_seen):
            info = slug_to_info.get(slug, {})
            channels_present.append(ChannelInfoDTO(
                slug=slug,
                name=info.get("name", slug),
                color=_CHANNEL_COLORS.get(slug, "#6B7280"),
            ))

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

        # 8. Cache (5 min)
        if self.cache is not None:
            await self.cache.set(tid, stage, cache_period, result.model_dump())

        return result
