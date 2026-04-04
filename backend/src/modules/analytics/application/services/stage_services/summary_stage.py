"""Summary stage service — extracted from MetricsService.

Handles get_bowtie_summary() logic: lightweight KPIs for all 8 stages,
reading from per-stage Redis caches with fallback to DB queries.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.analytics.application.dto.summary_dto import (
    BowtiesSummaryDTO,
    StageSummaryKpiDTO,
)
from src.modules.crm.domain.enums import LifecycleStage
from src.modules.crm.infrastructure.repositories.customer_repository import (
    CustomerRepository,
)
from src.modules.crm.infrastructure.repositories.lead_metrics_repository import (
    LeadRepository,
)
from src.modules.analytics.domain.ports import ConnectionPort, OfferReadPort
from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache


class SummaryStageService:
    """Provides lightweight KPIs for the Bowtie funnel row."""

    def __init__(
        self,
        db: Session,
        cache: Optional[MetricsCache] = None,
        connection_port: Optional[ConnectionPort] = None,
        offer_port: Optional[OfferReadPort] = None,
    ):
        self.db = db
        self.cache = cache
        self.connection_port = connection_port
        self.offer_port = offer_port
        # Legacy repos for fallback
        self.customer_repo = CustomerRepository(db)
        self.lead_repo = LeadRepository(db)

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

        stages: list[StageSummaryKpiDTO] = []
        latest_updated: Optional[str] = None

        # Helper to read a stage cache
        async def _get_stage_cache(stage: str) -> Optional[dict]:
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
                total_visitors += totals.get("reach", 0) + totals.get("sessions", 0) + totals.get("contacts", 0)
            connected_count = sum(
                len(attraction_cache.get(g, {}).get("channels", []))
                for g in ("organic_social", "ga4_search", "paid", "outbound")
            )
            stages.append(StageSummaryKpiDTO(
                stage="attraction", main_kpi=total_visitors,
                main_label="visitantes", secondary_kpi=connected_count,
                secondary_label="canales activos",
            ))
            if attraction_cache.get("last_updated"):
                latest_updated = attraction_cache["last_updated"]
        else:
            # Fallback: lightweight query
            from src.modules.analytics.infrastructure.models.metric_aggregation_model import (
                MetricAggregationModel,
            )
            from sqlalchemy import select, func as sa_func

            visitor_stmt = (
                select(sa_func.coalesce(sa_func.sum(MetricAggregationModel.value), 0.0))
                .where(
                    MetricAggregationModel.tenant_id == tenant_id,
                    MetricAggregationModel.metric_name.in_(("reach", "sessions")),
                    MetricAggregationModel.period_type == "last_30_days",
                )
            )
            total_visitors = int(self.db.execute(visitor_stmt).scalar() or 0)
            stages.append(StageSummaryKpiDTO(
                stage="attraction", main_kpi=total_visitors,
                main_label="visitantes", secondary_kpi=0,
                secondary_label="canales activos",
            ))

        # --- Capture ---
        capture_cache = await _get_stage_cache("capture")
        if capture_cache:
            hk = capture_cache.get("header_kpis", {})
            stages.append(StageSummaryKpiDTO(
                stage="capture", main_kpi=hk.get("total_leads", 0),
                main_label="leads", secondary_kpi=hk.get("conversion_rate", 0),
                secondary_label="tasa conversion", secondary_unit="%",
            ))
        else:
            total_leads = self.lead_repo.count_total(tenant_id)
            stages.append(StageSummaryKpiDTO(
                stage="capture", main_kpi=total_leads,
                main_label="leads", secondary_kpi=0,
                secondary_label="tasa conversion", secondary_unit="%",
            ))

        # --- Nurture ---
        nurture_cache = await _get_stage_cache("nurture")
        if nurture_cache:
            hk = nurture_cache.get("header_kpis", {})
            stages.append(StageSummaryKpiDTO(
                stage="nurture", main_kpi=hk.get("total_mqls", 0),
                main_label="MQLs", secondary_kpi=hk.get("conversion_rate", 0),
                secondary_label="engagement rate", secondary_unit="%",
            ))
        else:
            mql_count = self.customer_repo.count_by_stage(tenant_id, LifecycleStage.MQL)
            stages.append(StageSummaryKpiDTO(
                stage="nurture", main_kpi=mql_count,
                main_label="MQLs", secondary_kpi=0,
                secondary_label="engagement rate", secondary_unit="%",
            ))

        # --- Opportunity ---
        opportunity_cache = await _get_stage_cache("opportunity")
        if opportunity_cache:
            hk = opportunity_cache.get("header_kpis", {})
            stages.append(StageSummaryKpiDTO(
                stage="opportunity", main_kpi=hk.get("total_sqls", 0),
                main_label="SQLs", secondary_kpi=hk.get("conversion_rate", 0),
                secondary_label="pipeline value", secondary_unit="%",
            ))
        else:
            sql_count = self.customer_repo.count_by_stage(tenant_id, LifecycleStage.SQL)
            opp_count = self.customer_repo.count_by_stage(tenant_id, LifecycleStage.OPPORTUNITY)
            stages.append(StageSummaryKpiDTO(
                stage="opportunity", main_kpi=sql_count + opp_count,
                main_label="SQLs", secondary_kpi=0,
                secondary_label="pipeline value", secondary_unit="%",
            ))

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
            stages.append(StageSummaryKpiDTO(
                stage="sales", main_kpi=main_val,
                main_label="revenue", main_unit="$",
                secondary_kpi=secondary,
                secondary_label="conversion" if conv_rate > 0 else "clientes nuevos",
                secondary_unit=secondary_unit,
            ))
        else:
            from src.modules.analytics.infrastructure.repositories.sales_metrics_repository import (
                SalesMetricsRepository,
            )
            from datetime import datetime as dt_cls, timedelta as td, timezone as tz

            now = dt_cls.now(tz.utc)
            start_30d = now - td(days=30)
            sales_repo = SalesMetricsRepository(self.db)
            raw_sales = sales_repo.get_sales_summary(tenant_id, start_30d, now)
            total_revenue = sum(float(r.total_revenue) for r in raw_sales)
            new_customers = sum(int(r.unique_customers) for r in raw_sales)
            stages.append(StageSummaryKpiDTO(
                stage="sales", main_kpi=total_revenue,
                main_label="revenue", main_unit="$",
                secondary_kpi=new_customers,
                secondary_label="clientes nuevos",
            ))

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
            stages.append(StageSummaryKpiDTO(
                stage="adoption", main_kpi=health,
                main_label="salud %", main_unit="%",
                secondary_kpi=secondary,
                secondary_label="activacion" if conv_rate > 0 else "activos",
                secondary_unit=secondary_unit,
            ))
        else:
            stages.append(StageSummaryKpiDTO(
                stage="adoption", main_kpi=0,
                main_label="salud %", main_unit="%",
                secondary_kpi=0, secondary_label="activos",
            ))

        # --- Expansion ---
        expansion_cache = await _get_stage_cache("expansion")
        if expansion_cache:
            hk = expansion_cache.get("header_kpis", {})
            stages.append(StageSummaryKpiDTO(
                stage="expansion", main_kpi=hk.get("net_mrr", 0),
                main_label="net MRR", main_unit="$",
                secondary_kpi=hk.get("churn_rate_pct", 0),
                secondary_label="churn rate", secondary_unit="%",
            ))
        else:
            stages.append(StageSummaryKpiDTO(
                stage="expansion", main_kpi=0,
                main_label="net MRR", main_unit="$",
                secondary_kpi=0, secondary_label="churn rate", secondary_unit="%",
            ))

        # --- Evangelization ---
        evangelization_cache = await _get_stage_cache("evangelization")
        if evangelization_cache:
            hk = evangelization_cache.get("header_kpis", {})
            mf = evangelization_cache.get("mini_funnel", {})
            conv_rate = mf.get("conversion_rate", 0)
            stages.append(StageSummaryKpiDTO(
                stage="evangelization", main_kpi=hk.get("k_factor", 0),
                main_label="k-factor",
                secondary_kpi=conv_rate,
                secondary_label="conversion", secondary_unit="%" if conv_rate > 0 else None,
            ))
        else:
            evangelists = self.customer_repo.count_by_stage(tenant_id, LifecycleStage.EVANGELIST)
            stages.append(StageSummaryKpiDTO(
                stage="evangelization", main_kpi=0,
                main_label="k-factor",
                secondary_kpi=evangelists, secondary_label="evangelistas",
            ))

        result = BowtiesSummaryDTO(
            stages=stages,
            period="last_30_days",
            last_updated=latest_updated,
        )

        # Cache the summary with short TTL
        if self.cache is not None:
            await self.cache.set(
                tid, "summary", "last_30_days", result.model_dump()
            )

        return result
