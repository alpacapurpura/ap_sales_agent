"""MetricsService -- dashboard data for marketing funnel visualization.

get_marketing_sankey_metrics() reads from journey_events (separate migration).
get_bowtie_summary() reads from per-stage Redis caches (lightweight KPIs).
get_stage_timeseries() reads from official_metrics for daily/weekly charts.

Stage-specific `get_*_metrics()` methods have been migrated to individual
stage services under `stage_services/`.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.analytics.application.dto.summary_dto import (
    BowtiesSummaryDTO,
    StageSummaryKpiDTO,
)
from src.modules.analytics.application.dto.timeseries_dto import (
    ChannelInfoDTO,
    StageTimeSeriesDTO,
    TimeSeriesPointDTO,
)
from src.modules.analytics.domain.ports import ConnectionPort, OfferReadPort
from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache
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

# Maps our channel slugs to the ChannelType enum for connection lookups (sankey legacy)
_CHANNEL_CONNECTION_MAP: dict[str, ChannelType] = {
    "ig-organic": ChannelType.INSTAGRAM_ACCOUNT,
    "yt-organic": ChannelType.YOUTUBE_ANALYTICS,
    "fb-organic": ChannelType.FACEBOOK_PAGE,
    "meta-ads": ChannelType.META_ADS_ACCOUNT,
    "google-ads": ChannelType.GOOGLE_ANALYTICS,
    "yt-ads": ChannelType.YOUTUBE,
}


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
    ):
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
            tenant_id, LifecycleStage.OPPORTUNITY
        )
        opportunities = sql_count + opp_count

        # 5. Customers (Conversion)
        customers = self.customer_repo.count_by_stage(
            tenant_id, LifecycleStage.CUSTOMER
        )

        # 6. Loyal Customers (Retention)
        # Placeholder heuristic: 40% of customers are retained/loyal
        retention = int(customers * 0.4)

        # 7. Evangelists (Advocacy)
        evangelists = self.customer_repo.count_by_stage(
            tenant_id, LifecycleStage.EVANGELIST
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

        # --- Attraction ---
        attraction_cache = await _get_stage_cache("attraction")
        if attraction_cache:
            total_visitors = 0
            for group_key in ("organic_social", "ga4_search", "paid", "outbound"):
                group = attraction_cache.get(group_key, {})
                totals = group.get("totals", {})
                total_visitors += (
                    totals.get("reach", 0)
                    + totals.get("sessions", 0)
                    + totals.get("contacts", 0)
                )
            connected_count = sum(
                len(attraction_cache.get(g, {}).get("channels", []))
                for g in ("organic_social", "ga4_search", "paid", "outbound")
            )
            stages.append(
                StageSummaryKpiDTO(
                    stage="attraction",
                    main_kpi=total_visitors,
                    main_label="visitantes",
                    secondary_kpi=connected_count,
                    secondary_label="canales activos",
                )
            )
            if attraction_cache.get("last_updated"):
                latest_updated = attraction_cache["last_updated"]
        else:
            # Fallback: lightweight query
            from sqlalchemy import func as sa_func
            from sqlalchemy import select

            from src.modules.analytics.infrastructure.models.metric_aggregation_model import (
                MetricAggregationModel,
            )

            visitor_stmt = select(
                sa_func.coalesce(sa_func.sum(MetricAggregationModel.value), 0.0)
            ).where(
                MetricAggregationModel.tenant_id == tenant_id,
                MetricAggregationModel.metric_name.in_(("reach", "sessions")),
                MetricAggregationModel.period_type == "last_30_days",
            )
            total_visitors = int(self.db.execute(visitor_stmt).scalar() or 0)
            stages.append(
                StageSummaryKpiDTO(
                    stage="attraction",
                    main_kpi=total_visitors,
                    main_label="visitantes",
                    secondary_kpi=0,
                    secondary_label="canales activos",
                )
            )

        # --- Capture ---
        capture_cache = await _get_stage_cache("capture")
        if capture_cache:
            hk = capture_cache.get("header_kpis", {})
            stages.append(
                StageSummaryKpiDTO(
                    stage="capture",
                    main_kpi=hk.get("total_leads", 0),
                    main_label="leads",
                    secondary_kpi=hk.get("conversion_rate", 0),
                    secondary_label="tasa conversion",
                    secondary_unit="%",
                )
            )
        else:
            total_leads = self.lead_repo.count_total(tenant_id)
            stages.append(
                StageSummaryKpiDTO(
                    stage="capture",
                    main_kpi=total_leads,
                    main_label="leads",
                    secondary_kpi=0,
                    secondary_label="tasa conversion",
                    secondary_unit="%",
                )
            )

        # --- Nurture ---
        nurture_cache = await _get_stage_cache("nurture")
        if nurture_cache:
            hk = nurture_cache.get("header_kpis", {})
            stages.append(
                StageSummaryKpiDTO(
                    stage="nurture",
                    main_kpi=hk.get("total_mqls", 0),
                    main_label="MQLs",
                    secondary_kpi=hk.get("conversion_rate", 0),
                    secondary_label="engagement rate",
                    secondary_unit="%",
                )
            )
        else:
            mql_count = self.customer_repo.count_by_stage(tenant_id, LifecycleStage.MQL)
            stages.append(
                StageSummaryKpiDTO(
                    stage="nurture",
                    main_kpi=mql_count,
                    main_label="MQLs",
                    secondary_kpi=0,
                    secondary_label="engagement rate",
                    secondary_unit="%",
                )
            )

        # --- Opportunity ---
        opportunity_cache = await _get_stage_cache("opportunity")
        if opportunity_cache:
            hk = opportunity_cache.get("header_kpis", {})
            stages.append(
                StageSummaryKpiDTO(
                    stage="opportunity",
                    main_kpi=hk.get("total_sqls", 0),
                    main_label="SQLs",
                    secondary_kpi=hk.get("conversion_rate", 0),
                    secondary_label="pipeline value",
                    secondary_unit="%",
                )
            )
        else:
            sql_count = self.customer_repo.count_by_stage(tenant_id, LifecycleStage.SQL)
            opp_count = self.customer_repo.count_by_stage(
                tenant_id, LifecycleStage.OPPORTUNITY
            )
            stages.append(
                StageSummaryKpiDTO(
                    stage="opportunity",
                    main_kpi=sql_count + opp_count,
                    main_label="SQLs",
                    secondary_kpi=0,
                    secondary_label="pipeline value",
                    secondary_unit="%",
                )
            )

        # --- Sales ---
        sales_cache = await _get_stage_cache("sales")
        if sales_cache:
            hk = sales_cache.get("header_kpis", {})
            mf = sales_cache.get("mini_funnel", {})
            main_val = hk.get("total_revenue", 0)
            conv_rate = mf.get("conversion_rate", 0)
            new_cust = hk.get("new_customers", 0)
            secondary = conv_rate if conv_rate > 0 else new_cust
            secondary_unit = "%" if conv_rate > 0 else None
            stages.append(
                StageSummaryKpiDTO(
                    stage="sales",
                    main_kpi=main_val,
                    main_label="revenue",
                    main_unit="$",
                    secondary_kpi=secondary,
                    secondary_label="conversion"
                    if conv_rate > 0
                    else "clientes nuevos",
                    secondary_unit=secondary_unit,
                )
            )
        else:
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
            stages.append(
                StageSummaryKpiDTO(
                    stage="sales",
                    main_kpi=total_revenue,
                    main_label="revenue",
                    main_unit="$",
                    secondary_kpi=new_customers,
                    secondary_label="clientes nuevos",
                )
            )

        # --- Adoption ---
        adoption_cache = await _get_stage_cache("adoption")
        if adoption_cache:
            hk = adoption_cache.get("header_kpis", {})
            mf = adoption_cache.get("mini_funnel", {})
            health = hk.get("health_pct", 0)
            active = hk.get("active_customers", 0)
            conv_rate = mf.get("conversion_rate", 0)
            secondary = conv_rate if conv_rate > 0 else active
            secondary_unit = "%" if conv_rate > 0 else None
            stages.append(
                StageSummaryKpiDTO(
                    stage="adoption",
                    main_kpi=health,
                    main_label="salud %",
                    main_unit="%",
                    secondary_kpi=secondary,
                    secondary_label="activacion" if conv_rate > 0 else "activos",
                    secondary_unit=secondary_unit,
                )
            )
        else:
            stages.append(
                StageSummaryKpiDTO(
                    stage="adoption",
                    main_kpi=0,
                    main_label="salud %",
                    main_unit="%",
                    secondary_kpi=0,
                    secondary_label="activos",
                )
            )

        # --- Expansion ---
        expansion_cache = await _get_stage_cache("expansion")
        if expansion_cache:
            hk = expansion_cache.get("header_kpis", {})
            stages.append(
                StageSummaryKpiDTO(
                    stage="expansion",
                    main_kpi=hk.get("net_mrr", 0),
                    main_label="net MRR",
                    main_unit="$",
                    secondary_kpi=hk.get("churn_rate_pct", 0),
                    secondary_label="churn rate",
                    secondary_unit="%",
                )
            )
        else:
            stages.append(
                StageSummaryKpiDTO(
                    stage="expansion",
                    main_kpi=0,
                    main_label="net MRR",
                    main_unit="$",
                    secondary_kpi=0,
                    secondary_label="churn rate",
                    secondary_unit="%",
                )
            )

        # --- Evangelization ---
        evangelization_cache = await _get_stage_cache("evangelization")
        if evangelization_cache:
            hk = evangelization_cache.get("header_kpis", {})
            mf = evangelization_cache.get("mini_funnel", {})
            conv_rate = mf.get("conversion_rate", 0)
            stages.append(
                StageSummaryKpiDTO(
                    stage="evangelization",
                    main_kpi=hk.get("k_factor", 0),
                    main_label="k-factor",
                    secondary_kpi=conv_rate,
                    secondary_label="conversion",
                    secondary_unit="%" if conv_rate > 0 else None,
                )
            )
        else:
            evangelists = self.customer_repo.count_by_stage(
                tenant_id, LifecycleStage.EVANGELIST
            )
            stages.append(
                StageSummaryKpiDTO(
                    stage="evangelization",
                    main_kpi=0,
                    main_label="k-factor",
                    secondary_kpi=evangelists,
                    secondary_label="evangelistas",
                )
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
        from datetime import date as date_type
        from datetime import timedelta
        from datetime import timezone as tz

        now = datetime.now(tz.utc).date()
        start_date = now - timedelta(days=range_days)
        prev_start = start_date - timedelta(days=range_days)

        # Map metric aliases: frontend sends "visitors" but DB may have "sessions"
        db_metric_names = [metric_name]
        if metric_name == "visitors":
            db_metric_names = ["sessions", "users", "visitors"]
        elif metric_name == "leads":
            db_metric_names = ["leads", "new_subscribers"]

        from sqlalchemy import func as sa_f
        from sqlalchemy import select as sa_select

        from src.modules.analytics.infrastructure.models.official_metrics_model import (
            OfficialMetricModel,
        )

        m = OfficialMetricModel

        # Current period: group by date, channel_slug
        stmt = (
            sa_select(
                m.metric_date,
                m.channel_slug,
                sa_f.sum(m.value).label("total"),
            )
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
        rows = self.db.execute(stmt).all()

        # 4. Build data points
        from collections import OrderedDict

        date_map: dict[date_type, dict[str, float]] = OrderedDict()
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
            weekly_map: dict[date_type, dict[str, float]] = OrderedDict()
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
        period_totals: dict[str, float] = {}
        for ch_vals in date_map.values():
            for slug, val in ch_vals.items():
                period_totals[slug] = period_totals.get(slug, 0) + val

        # 6. Previous period totals
        prev_stmt = (
            sa_select(
                m.channel_slug,
                sa_f.sum(m.value).label("total"),
            )
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
        previous_period_totals = (
            {row.channel_slug: float(row.total) for row in prev_rows}
            if prev_rows
            else None
        )

        # 7. Build channels_present
        channels_present = []
        for slug in sorted(channels_seen):
            info = slug_to_info.get(slug, {})
            channels_present.append(
                ChannelInfoDTO(
                    slug=slug,
                    name=info.get("name", slug),
                    color=self._CHANNEL_COLORS.get(slug, "#6B7280"),
                )
            )

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
