"""Summary stage service — extracted from MetricsService.

Handles get_bowtie_summary() logic: lightweight KPIs for all 8 stages,
reading from per-stage Redis caches with fallback to DB queries.
"""

from datetime import UTC
from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.analytics.application.dto.summary_dto import (
    BowtiesSummaryDTO,
    StageSummaryKpiDTO,
)
from src.modules.analytics.domain.ports import ConnectionPort, OfferReadPort
from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache
from src.modules.crm.infrastructure.repositories.customer_repository import (
    CustomerRepository,
)
from src.modules.crm.infrastructure.repositories.lead_metrics_repository import (
    LeadRepository,
)
from src.shared.domain.enums import LifecycleStage


class SummaryStageService:
    """Provides lightweight KPIs for the Bowtie funnel row."""

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
        # Legacy repos for fallback
        self.customer_repo = CustomerRepository(db)
        self.lead_repo = LeadRepository(db)

    def _build_attraction_kpi(
        self,
        cache: dict | None,
        tenant_id: UUID,
    ) -> tuple[StageSummaryKpiDTO, str | None]:
        """Build attraction KPI from cache or DB fallback. Returns (kpi, last_updated)."""
        if cache:
            total_visitors = 0
            for group_key in ("organic_social", "ga4_search", "paid", "outbound"):
                totals = cache.get(group_key, {}).get("totals", {})
                total_visitors += totals.get("reach", 0) + totals.get("sessions", 0) + totals.get("contacts", 0)
            connected_count = sum(
                len(cache.get(g, {}).get("channels", [])) for g in ("organic_social", "ga4_search", "paid", "outbound")
            )
            return StageSummaryKpiDTO(
                stage="attraction",
                main_kpi=total_visitors,
                main_label="visitantes",
                secondary_kpi=connected_count,
                secondary_label="canales activos",
            ), cache.get("last_updated")

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
        return StageSummaryKpiDTO(
            stage="attraction",
            main_kpi=total_visitors,
            main_label="visitantes",
            secondary_kpi=0,
            secondary_label="canales activos",
        ), None

    @staticmethod
    def _build_simple_header_kpi(
        cache: dict | None,
        stage: str,
        main_field: str,
        main_label: str,
        secondary_field: str,
        secondary_label: str,
        fallback_main: int = 0,
        main_unit: str | None = None,
        secondary_unit: str | None = "%",
    ) -> StageSummaryKpiDTO:
        """Build a KPI for stages that just read header_kpis fields."""
        if cache:
            hk = cache.get("header_kpis", {})
            return StageSummaryKpiDTO(
                stage=stage,
                main_kpi=hk.get(main_field, 0),
                main_label=main_label,
                main_unit=main_unit,
                secondary_kpi=hk.get(secondary_field, 0),
                secondary_label=secondary_label,
                secondary_unit=secondary_unit,
            )
        return StageSummaryKpiDTO(
            stage=stage,
            main_kpi=fallback_main,
            main_label=main_label,
            main_unit=main_unit,
            secondary_kpi=0,
            secondary_label=secondary_label,
            secondary_unit=secondary_unit,
        )

    def _build_sales_kpi(
        self,
        cache: dict | None,
        tenant_id: UUID,
    ) -> StageSummaryKpiDTO:
        """Build sales KPI from cache or DB fallback."""
        if cache:
            hk = cache.get("header_kpis", {})
            mf = cache.get("mini_funnel", {})
            conv_rate = mf.get("conversion_rate", 0)
            new_cust = hk.get("new_customers", 0)
            secondary = conv_rate if conv_rate > 0 else new_cust
            return StageSummaryKpiDTO(
                stage="sales",
                main_kpi=hk.get("total_revenue", 0),
                main_label="revenue",
                main_unit="$",
                secondary_kpi=secondary,
                secondary_label="conversion" if conv_rate > 0 else "clientes nuevos",
                secondary_unit="%" if conv_rate > 0 else None,
            )

        from datetime import datetime as dt_cls
        from datetime import timedelta as td

        from src.modules.analytics.infrastructure.repositories.sales_metrics_repository import (
            SalesMetricsRepository,
        )

        now = dt_cls.now(UTC)
        sales_repo = SalesMetricsRepository(self.db)
        raw_sales = sales_repo.get_sales_summary(tenant_id, now - td(days=30), now)
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
        """Build adoption KPI from cache or empty fallback."""
        if cache:
            hk = cache.get("header_kpis", {})
            mf = cache.get("mini_funnel", {})
            conv_rate = mf.get("conversion_rate", 0)
            active = hk.get("active_customers", 0)
            secondary = conv_rate if conv_rate > 0 else active
            return StageSummaryKpiDTO(
                stage="adoption",
                main_kpi=hk.get("health_pct", 0),
                main_label="salud %",
                main_unit="%",
                secondary_kpi=secondary,
                secondary_label="activacion" if conv_rate > 0 else "activos",
                secondary_unit="%" if conv_rate > 0 else None,
            )
        return StageSummaryKpiDTO(
            stage="adoption",
            main_kpi=0,
            main_label="salud %",
            main_unit="%",
            secondary_kpi=0,
            secondary_label="activos",
        )

    def _build_evangelization_kpi(
        self,
        cache: dict | None,
        tenant_id: UUID,
    ) -> StageSummaryKpiDTO:
        """Build evangelization KPI from cache or DB fallback."""
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

    async def get_summary(self, tenant_id: UUID) -> BowtiesSummaryDTO:
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

        # Helper to read a stage cache
        async def _get_stage_cache(stage: str) -> dict | None:
            if self.cache is None:
                return None
            return await self.cache.get(tid, stage, "last_30_days")

        stages: list[StageSummaryKpiDTO] = []

        # --- Attraction ---
        attraction_kpi, latest_updated = self._build_attraction_kpi(
            await _get_stage_cache("attraction"),
            tenant_id,
        )
        stages.append(attraction_kpi)

        # --- Capture ---
        capture_cache = await _get_stage_cache("capture")
        fallback_leads = self.lead_repo.count_total(tenant_id) if not capture_cache else 0
        stages.append(
            self._build_simple_header_kpi(
                capture_cache,
                "capture",
                "total_leads",
                "leads",
                "conversion_rate",
                "tasa conversion",
                fallback_main=fallback_leads,
            ),
        )

        # --- Nurture ---
        nurture_cache = await _get_stage_cache("nurture")
        fallback_mqls = self.customer_repo.count_by_stage(tenant_id, LifecycleStage.MQL) if not nurture_cache else 0
        stages.append(
            self._build_simple_header_kpi(
                nurture_cache,
                "nurture",
                "total_mqls",
                "MQLs",
                "conversion_rate",
                "engagement rate",
                fallback_main=fallback_mqls,
            ),
        )

        # --- Opportunity ---
        opportunity_cache = await _get_stage_cache("opportunity")
        if not opportunity_cache:
            sql_count = self.customer_repo.count_by_stage(tenant_id, LifecycleStage.SQL)
            opp_count = self.customer_repo.count_by_stage(
                tenant_id,
                LifecycleStage.OPPORTUNITY,
            )
            fallback_sqls = sql_count + opp_count
        else:
            fallback_sqls = 0
        stages.append(
            self._build_simple_header_kpi(
                opportunity_cache,
                "opportunity",
                "total_sqls",
                "SQLs",
                "conversion_rate",
                "pipeline value",
                fallback_main=fallback_sqls,
            ),
        )

        # --- Sales ---
        stages.append(
            self._build_sales_kpi(
                await _get_stage_cache("sales"),
                tenant_id,
            ),
        )

        # --- Adoption ---
        stages.append(self._build_adoption_kpi(await _get_stage_cache("adoption")))

        # --- Expansion ---
        stages.append(
            self._build_simple_header_kpi(
                await _get_stage_cache("expansion"),
                "expansion",
                "net_mrr",
                "net MRR",
                "churn_rate_pct",
                "churn rate",
                main_unit="$",
            ),
        )

        # --- Evangelization ---
        stages.append(
            self._build_evangelization_kpi(
                await _get_stage_cache("evangelization"),
                tenant_id,
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
