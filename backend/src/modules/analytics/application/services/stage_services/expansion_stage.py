"""Expansion stage service — extracted from MetricsService.

Handles get_expansion_metrics() logic: Net MRR, Avg LTV, Churn Rate,
renewal/upsell/churn grouping, bottleneck detection.
"""

from datetime import UTC
from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.analytics.application.dto.capture_dto import MiniFunnelDTO
from src.modules.analytics.application.dto.expansion_dto import (
    ExpansionDetailDTO,
    ExpansionGroupDTO,
    ExpansionHeaderKpisDTO,
    ExpansionOfferDTO,
)
from src.modules.analytics.application.dto.opportunity_dto import BottleneckDTO
from src.modules.analytics.domain.period_config import DateRange
from src.modules.analytics.domain.ports import ConnectionPort, OfferReadPort
from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache
from src.shared.domain.currency import convert_to_usd


def _build_expansion_offers(
    raw_items: list[tuple],
    offer_map: dict,
    display_currency: str,
) -> list[ExpansionOfferDTO]:
    """Build ExpansionOfferDTO list from raw repository tuples."""
    result_offers = []
    for item in raw_items:
        offer_id_str = str(item[0])
        count = item[1]
        revenue = item[2]
        currency = item[3] if len(item) > 3 else display_currency
        offer = offer_map.get(offer_id_str)
        name = offer.public_name if offer else f"Oferta {offer_id_str[:8]}"
        usd_rev = convert_to_usd(revenue, currency)
        result_offers.append(
            ExpansionOfferDTO(
                offer_id=offer_id_str,
                public_name=name,
                count=count,
                revenue=revenue,
                currency=currency,
                usd_revenue=usd_rev,
            ),
        )
    return result_offers


def _build_expansion_group(
    group_key: str,
    group_label: str,
    group_subtitle: str,
    offers: list[ExpansionOfferDTO],
    rate_pct: float,
    display_currency: str,
    *,
    total_count_override: int | None = None,
) -> ExpansionGroupDTO:
    """Build a single ExpansionGroupDTO with totals from its offers."""
    total_count = total_count_override if total_count_override is not None else sum(o.count for o in offers)
    total_revenue = sum(o.revenue for o in offers)
    return ExpansionGroupDTO(
        group_key=group_key,
        group_label=group_label,
        group_subtitle=group_subtitle,
        total_count=total_count,
        total_revenue=total_revenue,
        total_revenue_usd=convert_to_usd(total_revenue, display_currency),
        currency=display_currency,
        rate_pct=rate_pct,
        offers=offers,
    )


class ExpansionStageService:
    """Provides expansion stage metrics for the Bowtie dashboard."""

    def __init__(
        self,
        db: Session,
        cache: MetricsCache | None = None,
        connection_port: ConnectionPort | None = None,
        offer_port: OfferReadPort | None = None,
    ) -> None:
        """Initialize expansion stage service."""
        self.db = db
        self.cache = cache
        self.connection_port = connection_port
        self.offer_port = offer_port

    async def get_metrics(
        self,
        tenant_id: UUID,
        date_range: DateRange,
    ) -> ExpansionDetailDTO:
        """Return expansion-stage (Stage 6) metrics.

        Flow:
        1. Check MetricsCache (300s TTL for expansion stage)
        2. On miss: query ExpansionMetricsRepository for renewal/upsell/churn data
        3. Query OfferReadPort for offer name enrichment
        4. Build three ExpansionGroupDTOs: retencion, crecimiento, cancelaciones
        5. Calculate header KPIs (Net MRR, Avg LTV, Churn Rate)
        6. Build mini funnel (Activos -> Expansion)
        7. Detect bottlenecks (churn rate > 3% warning, > 5% critical)
        8. Cache result and return ExpansionDetailDTO
        """
        from datetime import datetime as dt_cls

        from src.modules.analytics.infrastructure.repositories.expansion_repository import (
            ExpansionMetricsRepository,
        )

        start_dt, end_dt = date_range.to_datetime_range()

        # 1. Check cache
        if self.cache is not None:
            cached = await self.cache.get(str(tenant_id), "expansion", date_range.period_type)
            if cached is not None:
                return ExpansionDetailDTO(**cached)

        # 2. Query expansion data
        exp_repo = ExpansionMetricsRepository(self.db)
        sales_grouped = exp_repo.get_expansion_sales_grouped(
            tenant_id,
            start_dt,
            end_dt,
        )
        churn_by_offer = exp_repo.get_churn_data_by_offer(
            tenant_id,
            start_dt,
            end_dt,
        )
        total_churn_count = exp_repo.get_total_churn_count(
            tenant_id,
            start_dt,
            end_dt,
        )
        active_customer_count = exp_repo.get_active_customer_count(tenant_id)
        avg_ltv, ltv_currency = exp_repo.get_avg_ltv(tenant_id)
        upsell_customer_count = exp_repo.get_expansion_customer_count(
            tenant_id,
            start_dt,
            end_dt,
        )

        # 3. Get offers for enrichment
        offer_map = {}
        if self.offer_port is not None:
            offers = await self.offer_port.get_offers_by_tenant(tenant_id)
            offer_map = {str(o.id): o for o in offers}

        # Determine display currency from first sale found
        display_currency = "MXN"
        renewals = sales_grouped.get("renewals", [])
        upsells = sales_grouped.get("upsells", [])
        if renewals:
            display_currency = renewals[0][3]
        elif upsells:
            display_currency = upsells[0][3]

        # 4. Build ExpansionGroupDTOs
        renewal_offers = _build_expansion_offers(renewals, offer_map, display_currency)
        retention_rate = (
            round(
                (active_customer_count - total_churn_count) / active_customer_count * 100,
                1,
            )
            if active_customer_count > 0
            else 100.0
        )
        retencion = _build_expansion_group(
            "retencion",
            "Retencion",
            "Renovaciones de suscripciones activas",
            renewal_offers,
            retention_rate,
            display_currency,
        )

        upsell_offers = _build_expansion_offers(upsells, offer_map, display_currency)
        expansion_rate = (
            round(upsell_customer_count / active_customer_count * 100, 1) if active_customer_count > 0 else 0.0
        )
        crecimiento = _build_expansion_group(
            "crecimiento",
            "Crecimiento",
            "Ventas adicionales y upgrades a clientes existentes",
            upsell_offers,
            expansion_rate,
            display_currency,
        )

        churn_offers = _build_expansion_offers(
            churn_by_offer,
            offer_map,
            display_currency,
        )
        churn_rate_pct = round(total_churn_count / active_customer_count * 100, 1) if active_customer_count > 0 else 0.0
        cancelaciones = _build_expansion_group(
            "cancelaciones",
            "Cancelaciones",
            "Suscripciones perdidas y ingreso afectado",
            churn_offers,
            churn_rate_pct,
            display_currency,
            total_count_override=total_churn_count,
        )

        # 5. Header KPIs
        net_mrr = retencion.total_revenue + crecimiento.total_revenue - cancelaciones.total_revenue
        net_mrr_usd = convert_to_usd(net_mrr, display_currency)
        avg_ltv_usd = convert_to_usd(avg_ltv, ltv_currency)

        header_kpis = ExpansionHeaderKpisDTO(
            net_mrr=net_mrr,
            net_mrr_usd=net_mrr_usd,
            currency=display_currency,
            avg_ltv=avg_ltv,
            avg_ltv_usd=avg_ltv_usd,
            churn_rate_pct=churn_rate_pct,
        )

        # 6. Mini funnel: Activos -> Expansion
        total_expansion_count = retencion.total_count + crecimiento.total_count
        expansion_conv_rate = (
            round(total_expansion_count / active_customer_count * 100, 1) if active_customer_count > 0 else 0.0
        )

        mini_funnel = MiniFunnelDTO(
            source_label="Activos",
            source_value=active_customer_count,
            target_label="Expansion",
            target_value=total_expansion_count,
            conversion_rate=expansion_conv_rate,
        )

        # 7. Bottleneck detection
        bottlenecks: list[BottleneckDTO] = []

        if churn_rate_pct > 5.0:
            bottlenecks.append(
                BottleneckDTO(
                    type="high_churn_rate",
                    metric_label="Tasa de Cancelacion",
                    current_rate=churn_rate_pct,
                    severity="critical",
                    threshold=5.0,
                    tip="Revisa la calidad y satisfaccion de tu producto o servicio",
                ),
            )
        elif churn_rate_pct > 3.0:
            bottlenecks.append(
                BottleneckDTO(
                    type="high_churn_rate",
                    metric_label="Tasa de Cancelacion",
                    current_rate=churn_rate_pct,
                    severity="warning",
                    threshold=3.0,
                    tip="Revisa la calidad y satisfaccion de tu producto o servicio",
                ),
            )

        now = dt_cls.now(UTC)

        result = ExpansionDetailDTO(
            header_kpis=header_kpis,
            mini_funnel=mini_funnel,
            retencion=retencion,
            crecimiento=crecimiento,
            cancelaciones=cancelaciones,
            bottlenecks=bottlenecks,
            period=date_range.period_type,
            last_updated=now.isoformat(),
        )

        # 8. Set cache
        if self.cache is not None:
            await self.cache.set(
                str(tenant_id),
                "expansion",
                date_range.period_type,
                result.model_dump(),
            )

        return result
