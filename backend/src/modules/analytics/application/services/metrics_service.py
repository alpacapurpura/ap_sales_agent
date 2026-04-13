"""MetricsService -- dashboard data for marketing funnel visualization.

get_marketing_sankey_metrics() reads from journey_events (separate migration).
get_bowtie_summary() reads from per-stage Redis caches (lightweight KPIs).
get_stage_timeseries() reads from official_metrics for daily/weekly charts.

Stage-specific `get_*_metrics()` methods have been migrated to individual
stage services under `stage_services/`.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from src.modules.analytics.application.dto.summary_dto import (
    BowtiesSummaryDTO,
    StageSummaryKpiDTO,
)
from src.modules.analytics.application.dto.timeseries_dto import (
    ChannelInfoDTO,
    StageTimeSeriesDTO,
    TimeSeriesPointDTO,
)
from src.modules.connections.infrastructure.repositories.channel_connection_repository import (
    ChannelConnectionRepository,
)
from src.modules.crm.infrastructure.repositories.customer_repository import (
    CustomerRepository,
    JourneyEventRepository,
)
from src.modules.crm.infrastructure.repositories.lead_metrics_repository import (
    LeadRepository,
)
from src.shared.domain.enums import ChannelType, LifecycleStage

if TYPE_CHECKING:
    from collections import OrderedDict
    from uuid import UUID

    from sqlalchemy.orm import Session

    from src.modules.analytics.domain.ports import ConnectionPort, OfferReadPort
    from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache

# Maps our channel slugs to the ChannelType enum for connection lookups (sankey legacy)
_CHANNEL_CONNECTION_MAP: dict[str, ChannelType] = {
    "ig-organic": ChannelType.INSTAGRAM_ACCOUNT,
    "yt-organic": ChannelType.YOUTUBE_ANALYTICS,
    "fb-organic": ChannelType.FACEBOOK_PAGE,
    "meta-ads": ChannelType.META_ADS_ACCOUNT,
    "google-ads": ChannelType.GOOGLE_ANALYTICS,
    "yt-ads": ChannelType.YOUTUBE,
}


def _compute_period_totals(date_map: dict) -> dict[str, float]:
    """Sum values per channel slug across all dates."""
    period_totals: dict[str, float] = {}
    for ch_vals in date_map.values():
        for slug, val in ch_vals.items():
            period_totals[slug] = period_totals.get(slug, 0) + val
    return period_totals


class MetricsService:
    """Provides dashboard metrics for marketing funnel stages.

    Constructor accepts optional cache and connection_port for backward
    compatibility -- the sankey endpoint doesn't need them.
    """

    def __init__(
        self,
        db: Session,
        cache: MetricsCache | None = None,
        connection_port: ConnectionPort | None = None,
        offer_port: OfferReadPort | None = None,
    ) -> None:
        self.db = db
        self.cache = cache
        self.connection_port = connection_port
        self.offer_port = offer_port

        # Legacy repos for sankey (unchanged)
        self.journey_repo = JourneyEventRepository(db)
        self.customer_repo = CustomerRepository(db)
        self.lead_repo = LeadRepository(db)
        self.connection_repo = ChannelConnectionRepository(db)

    def get_marketing_sankey_metrics(self, tenant_id: UUID) -> dict[str, Any]:
        """
        Obtiene metricas para el diagrama de Sankey de marketing (7 nodos).

        Nodos:
        0: Adquisition (Visitors)
        1: Activation (Leads)
        2: Consideration (Qualified Leads)
        3: Decision (Opportunities)
        4: Conversion (Customers)
        5: Retention (Loyal Customers)
        6: Advocacy (Evangelists)
        """

        # 1. Visitors (Adquisition)
        visitors = self.journey_repo.get_unique_visitors(tenant_id)

        # 2. Leads (Activation)
        leads = self.lead_repo.count_total(tenant_id)

        # 3. Qualified (Consideration)
        qualified_leads = self.lead_repo.count_qualified(tenant_id)
        mql_count = self.customer_repo.count_by_stage(tenant_id, LifecycleStage.MQL)
        qualified = max(qualified_leads, mql_count)

        # 4. Opportunities (Decision)
        sql_count = self.customer_repo.count_by_stage(tenant_id, LifecycleStage.SQL)
        opp_count = self.customer_repo.count_by_stage(
            tenant_id,
            LifecycleStage.OPPORTUNITY,
        )
        opportunities = sql_count + opp_count

        # 5. Customers (Conversion)
        customers = self.customer_repo.count_by_stage(
            tenant_id,
            LifecycleStage.CUSTOMER,
        )

        # 6. Loyal Customers (Retention)
        # Placeholder heuristic: 40% of customers are retained/loyal
        retention = int(customers * 0.4)

        # 7. Evangelists (Advocacy)
        evangelists = self.customer_repo.count_by_stage(
            tenant_id,
            LifecycleStage.EVANGELIST,
        )

        nodes = [
            {"name": "Adquisition"},
            {"name": "Activation"},
            {"name": "Consideration"},
            {"name": "Decision"},
            {"name": "Conversion"},
            {"name": "Retention"},
            {"name": "Advocacy"},
        ]

        links = [
            {"source": 0, "target": 1, "value": leads},
            {"source": 1, "target": 2, "value": qualified},
            {"source": 2, "target": 3, "value": opportunities},
            {"source": 3, "target": 4, "value": customers},
            {"source": 4, "target": 5, "value": retention},
            {"source": 5, "target": 6, "value": evangelists},
        ]

        return {
            "nodes": nodes,
            "links": links,
            "raw_metrics": {
                "visitors": visitors,
                "leads": leads,
                "qualified": qualified,
                "opportunities": opportunities,
                "customers": customers,
                "retention": retention,
                "evangelists": evangelists,
            },
        }

    def _is_connected(self, tenant_id: UUID, slug: str) -> bool:
        """Check if a channel has an active connection for this tenant."""
        channel_type = _CHANNEL_CONNECTION_MAP.get(slug)
        if not channel_type:
            return False
        conn = self.connection_repo.get_active(tenant_id, channel_type)
        return conn is not None

    # ------------------------------------------------------------------
    # Bowtie Summary — lightweight endpoint for the funnel row
    # ------------------------------------------------------------------

    async def get_bowtie_summary(self, tenant_id: UUID) -> BowtiesSummaryDTO:
        """Return lightweight KPIs for all 8 stages.

        Strategy: read each stage's existing Redis cache and extract only the
        2-3 KPI fields needed. Falls back to minimal DB queries on cache miss.
        The assembled summary is itself cached with a 60s TTL.
        """
        tid = str(tenant_id)

        # 1. Try summary-level cache first
        if self.cache is not None:
            cached = await self.cache.get(tid, "summary", "last_30_days")
            if cached is not None:
                return BowtiesSummaryDTO(**cached)

        stages: list[StageSummaryKpiDTO] = []
        latest_updated: str | None = None

        # Helper to read a stage cache
        async def _get_stage_cache(stage: str) -> dict | None:
            if self.cache is None:
                return None
            return await self.cache.get(tid, stage, "last_30_days")

        # Build each stage's KPI
        attraction_result = self._build_attraction_kpi(
            tenant_id,
            await _get_stage_cache("attraction"),
        )
        stages.append(attraction_result[0])
        if attraction_result[1]:
            latest_updated = attraction_result[1]

        stages.append(
            self._build_capture_kpi(
                tenant_id,
                await _get_stage_cache("capture"),
            ),
        )
        stages.append(
            self._build_nurture_kpi(
                tenant_id,
                await _get_stage_cache("nurture"),
            ),
        )
        stages.append(
            self._build_opportunity_kpi(
                tenant_id,
                await _get_stage_cache("opportunity"),
            ),
        )
        stages.append(
            self._build_sales_kpi(
                tenant_id,
                await _get_stage_cache("sales"),
            ),
        )
        stages.append(self._build_adoption_kpi(await _get_stage_cache("adoption")))
        stages.append(self._build_expansion_kpi(await _get_stage_cache("expansion")))
        stages.append(
            self._build_evangelization_kpi(
                tenant_id,
                await _get_stage_cache("evangelization"),
            ),
        )

        result = BowtiesSummaryDTO(
            stages=stages,
            period="last_30_days",
            last_updated=latest_updated,
        )

        # Cache the summary with short TTL
        if self.cache is not None:
            await self.cache.set(tid, "summary", "last_30_days", result.model_dump())

        return result

    def _build_attraction_kpi(
        self,
        tenant_id: UUID,
        cache: dict | None,
    ) -> tuple[StageSummaryKpiDTO, str | None]:
        """Build attraction stage KPI. Returns (dto, last_updated)."""
        if cache:
            total_visitors = 0
            for group_key in ("organic_social", "ga4_search", "paid", "outbound"):
                group = cache.get(group_key, {})
                totals = group.get("totals", {})
                total_visitors += totals.get("reach", 0) + totals.get("sessions", 0) + totals.get("contacts", 0)
            connected_count = sum(
                len(cache.get(g, {}).get("channels", [])) for g in ("organic_social", "ga4_search", "paid", "outbound")
            )
            return (
                StageSummaryKpiDTO(
                    stage="attraction",
                    main_kpi=total_visitors,
                    main_label="visitantes",
                    secondary_kpi=connected_count,
                    secondary_label="canales activos",
                ),
                cache.get("last_updated"),
            )

        from sqlalchemy import func as sa_func
        from sqlalchemy import select

        from src.modules.analytics.infrastructure.models.metric_aggregation_model import (
            MetricAggregationModel,
        )

        visitor_stmt = select(
            sa_func.coalesce(sa_func.sum(MetricAggregationModel.value), 0.0),
        ).where(
            MetricAggregationModel.tenant_id == tenant_id,
            MetricAggregationModel.metric_name.in_(("reach", "sessions")),
            MetricAggregationModel.period_type == "last_30_days",
        )
        total_visitors = int(self.db.execute(visitor_stmt).scalar() or 0)
        return (
            StageSummaryKpiDTO(
                stage="attraction",
                main_kpi=total_visitors,
                main_label="visitantes",
                secondary_kpi=0,
                secondary_label="canales activos",
            ),
            None,
        )

    def _build_capture_kpi(
        self,
        tenant_id: UUID,
        cache: dict | None,
    ) -> StageSummaryKpiDTO:
        if cache:
            hk = cache.get("header_kpis", {})
            return StageSummaryKpiDTO(
                stage="capture",
                main_kpi=hk.get("total_leads", 0),
                main_label="leads",
                secondary_kpi=hk.get("conversion_rate", 0),
                secondary_label="tasa conversion",
                secondary_unit="%",
            )
        return StageSummaryKpiDTO(
            stage="capture",
            main_kpi=self.lead_repo.count_total(tenant_id),
            main_label="leads",
            secondary_kpi=0,
            secondary_label="tasa conversion",
            secondary_unit="%",
        )

    def _build_nurture_kpi(
        self,
        tenant_id: UUID,
        cache: dict | None,
    ) -> StageSummaryKpiDTO:
        if cache:
            hk = cache.get("header_kpis", {})
            return StageSummaryKpiDTO(
                stage="nurture",
                main_kpi=hk.get("total_mqls", 0),
                main_label="MQLs",
                secondary_kpi=hk.get("conversion_rate", 0),
                secondary_label="engagement rate",
                secondary_unit="%",
            )
        return StageSummaryKpiDTO(
            stage="nurture",
            main_kpi=self.customer_repo.count_by_stage(tenant_id, LifecycleStage.MQL),
            main_label="MQLs",
            secondary_kpi=0,
            secondary_label="engagement rate",
            secondary_unit="%",
        )

    def _build_opportunity_kpi(
        self,
        tenant_id: UUID,
        cache: dict | None,
    ) -> StageSummaryKpiDTO:
        if cache:
            hk = cache.get("header_kpis", {})
            return StageSummaryKpiDTO(
                stage="opportunity",
                main_kpi=hk.get("total_sqls", 0),
                main_label="SQLs",
                secondary_kpi=hk.get("conversion_rate", 0),
                secondary_label="pipeline value",
                secondary_unit="%",
            )
        sql_count = self.customer_repo.count_by_stage(tenant_id, LifecycleStage.SQL)
        opp_count = self.customer_repo.count_by_stage(
            tenant_id,
            LifecycleStage.OPPORTUNITY,
        )
        return StageSummaryKpiDTO(
            stage="opportunity",
            main_kpi=sql_count + opp_count,
            main_label="SQLs",
            secondary_kpi=0,
            secondary_label="pipeline value",
            secondary_unit="%",
        )

    def _build_sales_kpi(
        self,
        tenant_id: UUID,
        cache: dict | None,
    ) -> StageSummaryKpiDTO:
        if cache:
            hk = cache.get("header_kpis", {})
            mf = cache.get("mini_funnel", {})
            main_val = hk.get("total_revenue", 0)
            conv_rate = mf.get("conversion_rate", 0)
            new_cust = hk.get("new_customers", 0)
            secondary = conv_rate if conv_rate > 0 else new_cust
            secondary_unit = "%" if conv_rate > 0 else None
            return StageSummaryKpiDTO(
                stage="sales",
                main_kpi=main_val,
                main_label="revenue",
                main_unit="$",
                secondary_kpi=secondary,
                secondary_label="conversion" if conv_rate > 0 else "clientes nuevos",
                secondary_unit=secondary_unit,
            )

        from datetime import datetime as dt_cls
        from datetime import timedelta as td
        from datetime import timezone as tz

        from src.modules.analytics.infrastructure.repositories.sales_metrics_repository import (
            SalesMetricsRepository,
        )

        now = dt_cls.now(tz.utc)
        start_30d = now - td(days=30)
        sales_repo = SalesMetricsRepository(self.db)
        raw_sales = sales_repo.get_sales_summary(tenant_id, start_30d, now)
        total_revenue = sum(float(r.total_revenue) for r in raw_sales)
        new_customers = sum(int(r.unique_customers) for r in raw_sales)
        return StageSummaryKpiDTO(
            stage="sales",
            main_kpi=total_revenue,
            main_label="revenue",
            main_unit="$",
            secondary_kpi=new_customers,
            secondary_label="clientes nuevos",
        )

    @staticmethod
    def _build_adoption_kpi(cache: dict | None) -> StageSummaryKpiDTO:
        if cache:
            hk = cache.get("header_kpis", {})
            mf = cache.get("mini_funnel", {})
            health = hk.get("health_pct", 0)
            active = hk.get("active_customers", 0)
            conv_rate = mf.get("conversion_rate", 0)
            secondary = conv_rate if conv_rate > 0 else active
            secondary_unit = "%" if conv_rate > 0 else None
            return StageSummaryKpiDTO(
                stage="adoption",
                main_kpi=health,
                main_label="salud %",
                main_unit="%",
                secondary_kpi=secondary,
                secondary_label="activacion" if conv_rate > 0 else "activos",
                secondary_unit=secondary_unit,
            )
        return StageSummaryKpiDTO(
            stage="adoption",
            main_kpi=0,
            main_label="salud %",
            main_unit="%",
            secondary_kpi=0,
            secondary_label="activos",
        )

    @staticmethod
    def _build_expansion_kpi(cache: dict | None) -> StageSummaryKpiDTO:
        if cache:
            hk = cache.get("header_kpis", {})
            return StageSummaryKpiDTO(
                stage="expansion",
                main_kpi=hk.get("net_mrr", 0),
                main_label="net MRR",
                main_unit="$",
                secondary_kpi=hk.get("churn_rate_pct", 0),
                secondary_label="churn rate",
                secondary_unit="%",
            )
        return StageSummaryKpiDTO(
            stage="expansion",
            main_kpi=0,
            main_label="net MRR",
            main_unit="$",
            secondary_kpi=0,
            secondary_label="churn rate",
            secondary_unit="%",
        )

    def _build_evangelization_kpi(
        self,
        tenant_id: UUID,
        cache: dict | None,
    ) -> StageSummaryKpiDTO:
        if cache:
            hk = cache.get("header_kpis", {})
            mf = cache.get("mini_funnel", {})
            conv_rate = mf.get("conversion_rate", 0)
            return StageSummaryKpiDTO(
                stage="evangelization",
                main_kpi=hk.get("k_factor", 0),
                main_label="k-factor",
                secondary_kpi=conv_rate,
                secondary_label="conversion",
                secondary_unit="%" if conv_rate > 0 else None,
            )
        evangelists = self.customer_repo.count_by_stage(
            tenant_id,
            LifecycleStage.EVANGELIST,
        )
        return StageSummaryKpiDTO(
            stage="evangelization",
            main_kpi=0,
            main_label="k-factor",
            secondary_kpi=evangelists,
            secondary_label="evangelistas",
        )

    # ------------------------------------------------------------------
    # Time Series — generic daily/weekly chart data for any stage
    # ------------------------------------------------------------------

    # Canonical hex colors per channel slug (mirrors frontend channel-colors.ts)
    _CHANNEL_COLORS: dict[str, str] = {
        "ig-organic": "#E1306C",
        "ig-dm": "#C13584",
        "fb-organic": "#1877F2",
        "fb-messenger": "#0099FF",
        "yt-organic": "#FF0000",
        "yt-ads": "#CC0000",
        "tiktok-organic": "#00C9C8",
        "tiktok-ads": "#00A3A2",
        "tiktok-dm": "#00E5E4",
        "meta-ads": "#5B5FC7",
        "meta-retargeting": "#7B61FF",
        "google-ads": "#EA4335",
        "google-retargeting": "#D93025",
        "google-organic": "#34A853",
        "search-console": "#1B8A3E",
        "ai-search-organic": "#8B5CF6",
        "direct": "#78716C",
        "linkedin-organic": "#0A66C2",
        "whatsapp": "#25D366",
        "manychat-comments": "#7C3AED",
        "manychat-messenger": "#7C3AED",
        "manychat-ig": "#7C3AED",
        "email-capture": "#F59E0B",
        "shopify": "#96BF48",
        "shopify-checkout": "#7EA838",
        "abandoned-cart": "#D97706",
        "website-total": "#0EA5E9",
        "website-capture": "#0284C7",
        "meta-pixel": "#38BDF8",
        "landing-form": "#06B6D4",
        "ai-sdr": "#6366F1",
        "cold-contact": "#A8A29E",
        "meeting-booked": "#14B8A6",
        "link-enviado": "#F97316",
        "checkout-lp": "#FB923C",
    }

    # Metric alias map: frontend sends "visitors" but DB may have "sessions"
    _METRIC_ALIAS_MAP: dict[str, list[str]] = {
        "visitors": ["sessions", "users", "visitors"],
        "leads": ["leads", "new_subscribers"],
    }

    async def get_stage_timeseries(
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
        slug_to_info = {ch["slug"]: ch for ch in stage_channels}
        channel_slugs = list(slug_to_info.keys())

        empty_result = StageTimeSeriesDTO(
            stage=stage,
            metric_name=metric_name,
            granularity=granularity,
            range_days=range_days,
            data_points=[],
            channels_present=[],
            period_totals={},
            previous_period_totals=None,
        )
        if not channel_slugs:
            return empty_result

        # 3. Query current period
        from datetime import timedelta
        from datetime import timezone as tz

        now = datetime.now(tz.utc).date()
        start_date = now - timedelta(days=range_days)
        prev_start = start_date - timedelta(days=range_days)
        db_metric_names = self._METRIC_ALIAS_MAP.get(metric_name, [metric_name])

        rows = self._query_timeseries_rows(
            tenant_id,
            channel_slugs,
            db_metric_names,
            start_date,
            now,
        )

        # 4. Build data points
        date_map, channels_seen = self._build_date_map(rows, granularity)

        data_points = [TimeSeriesPointDTO(date=d.isoformat(), channels=ch_vals) for d, ch_vals in date_map.items()]

        # 5. Period totals
        period_totals = _compute_period_totals(date_map)

        # 6. Previous period totals
        previous_period_totals = self._query_previous_period_totals(
            tenant_id,
            channel_slugs,
            db_metric_names,
            prev_start,
            start_date,
        )

        # 7. Build channels_present
        channels_present = [
            ChannelInfoDTO(
                slug=slug,
                name=slug_to_info.get(slug, {}).get("name", slug),
                color=self._CHANNEL_COLORS.get(slug, "#6B7280"),
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

        # 8. Cache (5 min)
        if self.cache is not None:
            await self.cache.set(tid, stage, cache_period, result.model_dump())

        return result

    def _query_timeseries_rows(
        self,
        tenant_id: UUID,
        channel_slugs: list[str],
        db_metric_names: list[str],
        start_date: date,
        end_date: date,
    ) -> list[Any]:
        """Query official_metrics for current period, grouped by date and channel."""
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
                m.metric_date <= end_date,
            )
            .group_by(m.metric_date, m.channel_slug)
            .order_by(m.metric_date)
        )
        return self.db.execute(stmt).all()

    @staticmethod
    def _build_date_map(rows: list[Any], granularity: str) -> tuple[OrderedDict, set[str]]:
        """Build date_map from query rows and optionally aggregate to weekly."""
        from collections import OrderedDict
        from datetime import timedelta

        date_map = OrderedDict()
        channels_seen: set = set()

        for row in rows:
            d = row.metric_date
            slug = row.channel_slug
            val = float(row.total)
            channels_seen.add(slug)
            if d not in date_map:
                date_map[d] = {}
            date_map[d][slug] = date_map[d].get(slug, 0) + val

        if granularity == "weekly" and date_map:
            weekly_map = OrderedDict()
            for d, ch_vals in date_map.items():
                week_start = d - timedelta(days=d.weekday())
                if week_start not in weekly_map:
                    weekly_map[week_start] = {}
                for slug, val in ch_vals.items():
                    weekly_map[week_start][slug] = weekly_map[week_start].get(slug, 0) + val
            date_map = weekly_map

        return date_map, channels_seen

    def _query_previous_period_totals(
        self,
        tenant_id: UUID,
        channel_slugs: list[str],
        db_metric_names: list[str],
        prev_start: date,
        start_date: date,
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
        if prev_rows:
            return {row.channel_slug: float(row.total) for row in prev_rows}
        return None
