"""Sales stage service — extracted from MetricsService.

Handles get_sales_metrics() logic: revenue by offer, tier grouping,
subscription splits, CAC, Shopify enrichment, bottleneck detection.
"""

from collections import defaultdict
from datetime import UTC
from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.analytics.application.dto.capture_dto import MiniFunnelDTO
from src.modules.analytics.application.dto.opportunity_dto import BottleneckDTO
from src.modules.analytics.application.dto.sales_dto import (
    HIGH_CAC_CRITICAL_RATIO,
    HIGH_CAC_WARNING_RATIO,
    LOW_CONVERSION_THRESHOLDS,
    TIER_DISPLAY_ORDER,
    TIER_LABELS,
    OfferSaleDTO,
    RevenueGroupDTO,
    SalesDetailDTO,
    SalesHeaderKpisDTO,
    TierGroupDTO,
    get_subscription_labels,
    get_tier_for_value_level,
)
from src.modules.analytics.application.services.stage_cost_service import (
    StageCostService,
)
from src.modules.analytics.domain.ports import ConnectionPort, OfferReadPort
from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache
from src.modules.analytics.infrastructure.repositories.official_metrics_repository import (
    OfficialMetricsRepository,
)
from src.shared.domain.currency import convert_to_usd

_STAGE_KEY_MAP: dict[str, str] = {
    "CONVERSION": "adquisicion",
    "EXPANSION": "expansion",
}


def _group_raw_sales(
    raw_sales: list,
    offer_map: dict,
) -> tuple[dict[str, dict[str, dict]], dict[str, float], str]:
    """Group raw sales rows by stage and offer, return (stage_data, stage_revenue, display_currency)."""
    stage_data: dict[str, dict[str, dict]] = {
        "adquisicion": {},
        "expansion": {},
    }
    stage_revenue: dict[str, float] = {"adquisicion": 0.0, "expansion": 0.0}

    for row in raw_sales:
        stage_val = row[0]
        offer_id = str(row[1])
        source = row[2] or "MANUAL"
        currency = row[3] or "USD"
        count = int(row[4])
        revenue = float(row[5])
        unique_custs = int(row[6])

        stage_str = stage_val.value if hasattr(stage_val, "value") else str(stage_val)
        stage_key = _STAGE_KEY_MAP.get(stage_str)
        if stage_key is None:
            continue

        if offer_id not in stage_data[stage_key]:
            stage_data[stage_key][offer_id] = {
                "count": 0,
                "revenue": 0.0,
                "currency": currency,
                "sources": defaultdict(int),
                "unique_customers": 0,
            }

        entry = stage_data[stage_key][offer_id]
        entry["count"] += count
        entry["revenue"] += revenue
        entry["sources"][source] += count
        entry["unique_customers"] += unique_custs
        stage_revenue[stage_key] += revenue

    # Include unsold offers in adquisicion
    for offer_id_str, offer in offer_map.items():
        if offer_id_str not in stage_data["adquisicion"]:
            stage_data["adquisicion"][offer_id_str] = {
                "count": 0,
                "revenue": 0.0,
                "currency": offer.currency,
                "sources": {},
                "unique_customers": 0,
            }

    # Determine display currency (most common from sales)
    currency_counts: dict[str, int] = defaultdict(int)
    for row in raw_sales:
        currency_counts[row[3] or "USD"] += int(row[4])
    display_currency = max(currency_counts, key=currency_counts.get) if currency_counts else "USD"

    return stage_data, stage_revenue, display_currency


def _build_offer_sale_dto(
    offer_id_str: str,
    data: dict,
    offer_map: dict,
    stage_key: str,
) -> OfferSaleDTO | None:
    """Build a single OfferSaleDTO, returning None for lead magnets."""
    offer = offer_map.get(offer_id_str)
    value_level = offer.value_level if offer else None

    if value_level and value_level in ("lead_magnet", "level_0_free"):
        return None

    offer_name = offer.public_name if offer else f"Oferta {offer_id_str[:8]}"
    offer_type = offer.offer_type if offer else "unknown"
    pricing_type = offer.pricing_type if offer else "one_time"
    offer_currency = data["currency"]
    usd_revenue = convert_to_usd(data["revenue"], offer_currency)

    # Subscription split
    new_subs = None
    new_sub_rev = None
    renewals = None
    renewal_rev = None
    sub_new_label = None
    sub_renewal_label = None

    labels = get_subscription_labels(pricing_type, offer_type)
    if labels is not None:
        if stage_key == "adquisicion":
            new_subs = data["count"]
            new_sub_rev = data["revenue"]
        else:
            renewals = data["count"]
            renewal_rev = data["revenue"]
        sub_new_label = labels.get("new_label")
        sub_renewal_label = labels.get("renewal_label")

    return OfferSaleDTO(
        offer_id=offer_id_str,
        public_name=offer_name,
        offer_type=offer_type,
        pricing_type=pricing_type,
        total_revenue=data["revenue"],
        sales_count=data["count"],
        currency=offer_currency,
        usd_revenue=usd_revenue,
        source_breakdown=dict(data["sources"]),
        new_subscriptions=new_subs,
        new_subscription_revenue=new_sub_rev,
        renewals=renewals,
        renewal_revenue=renewal_rev,
        subscription_new_label=sub_new_label,
        subscription_renewal_label=sub_renewal_label,
    )


def _build_revenue_group(
    stage_key: str,
    group_label: str,
    stage_data: dict[str, dict[str, dict]],
    stage_revenue: dict[str, float],
    total_revenue_all: float,
    offer_map: dict,
    display_currency: str,
) -> RevenueGroupDTO:
    """Build a RevenueGroupDTO for one stage (adquisicion or expansion)."""
    offers_by_tier: dict[str, list[OfferSaleDTO]] = defaultdict(list)
    group_revenue = stage_revenue[stage_key]
    group_customers = 0

    for offer_id_str, data in stage_data[stage_key].items():
        offer = offer_map.get(offer_id_str)
        value_level = offer.value_level if offer else None
        tier = get_tier_for_value_level(value_level)

        offer_dto = _build_offer_sale_dto(offer_id_str, data, offer_map, stage_key)
        if offer_dto is None:
            continue

        offers_by_tier[tier].append(offer_dto)
        group_customers += data["unique_customers"]

    tiers = [
        TierGroupDTO(
            tier_key=tier_key,
            tier_label=TIER_LABELS[tier_key],
            offers=offers_by_tier[tier_key],
        )
        for tier_key in TIER_DISPLAY_ORDER
        if tier_key in offers_by_tier
    ]

    rev_pct = round(group_revenue / total_revenue_all * 100, 1) if total_revenue_all > 0 else 0.0

    return RevenueGroupDTO(
        group_key=stage_key,
        group_label=group_label,
        total_revenue=group_revenue,
        total_revenue_usd=convert_to_usd(group_revenue, display_currency),
        customer_count=group_customers,
        revenue_percentage=rev_pct,
        currency=display_currency,
        tiers=tiers,
    )


def _build_sales_bottlenecks(
    conv_rate: float,
    sql_count: int,
    cac: float | None,
    new_customers: int,
    total_rev: float,
) -> list[BottleneckDTO]:
    """Detect sales-stage bottlenecks (low conversion, high CAC ratio)."""
    bottlenecks: list[BottleneckDTO] = []

    if sql_count > 0:
        if conv_rate < LOW_CONVERSION_THRESHOLDS["critical"]:
            severity, threshold = "critical", LOW_CONVERSION_THRESHOLDS["critical"]
        elif conv_rate < LOW_CONVERSION_THRESHOLDS["warning"]:
            severity, threshold = "warning", LOW_CONVERSION_THRESHOLDS["warning"]
        else:
            severity = None
        if severity:
            bottlenecks.append(
                BottleneckDTO(
                    type="low_conversion_rate",
                    metric_label="Tasa de Conversion",
                    current_rate=conv_rate,
                    severity=severity,
                    threshold=threshold,
                    tip="Baja conversion de oportunidades a ventas -- revisa tu proceso de cierre",
                ),
            )

    if cac is not None and new_customers > 0 and total_rev > 0:
        aov = total_rev / new_customers
        cac_ratio = cac / aov if aov > 0 else 0.0
        if cac_ratio >= HIGH_CAC_CRITICAL_RATIO:
            severity, threshold = "critical", HIGH_CAC_CRITICAL_RATIO * 100
        elif cac_ratio >= HIGH_CAC_WARNING_RATIO:
            severity, threshold = "warning", HIGH_CAC_WARNING_RATIO * 100
        else:
            severity = None
        if severity:
            bottlenecks.append(
                BottleneckDTO(
                    type="high_cac_ratio",
                    metric_label="CAC / Ticket Promedio",
                    current_rate=round(cac_ratio * 100, 1),
                    severity=severity,
                    threshold=threshold,
                    tip="Tu costo de adquisicion es alto respecto al ticket promedio -- optimiza tu funnel pre-venta",
                ),
            )

    return bottlenecks


class SalesStageService:
    """Provides sales stage metrics for the Bowtie dashboard."""

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

    def _enrich_with_shopify(
        self,
        tenant_id: UUID,
        start_date: "object",
        end_date: "object",
        display_currency: str,
        total_rev: float,
        total_rev_usd: float,
        new_customers: int,
        total_investment: float,
        cac: float | None,
    ) -> tuple[SalesHeaderKpisDTO, int, float]:
        """Build SalesHeaderKpisDTO enriched with Shopify metrics.

        Returns (header_kpis, new_customers, total_rev) with possible
        Shopify fallback values applied.
        """
        official_repo = OfficialMetricsRepository(self.db)
        shopify_agg = official_repo.get_channel_metrics(
            tenant_id,
            "shopify",
            "shopify",
            start_date.date(),
            end_date.date(),
        )

        shopify_revenue = shopify_agg.get("revenue", 0.0)
        shopify_order_count = int(shopify_agg.get("order_count", 0))
        shopify_avg_order = shopify_agg.get("avg_order_value", 0.0)

        shopify_currency = display_currency
        if shopify_revenue > 0:
            sample_rows = official_repo.get_metrics(
                tenant_id,
                channel_slug="shopify",
                metric_name="revenue",
                start_date=start_date.date(),
                end_date=end_date.date(),
            )
            if sample_rows:
                shopify_currency = sample_rows[0].currency or "USD"

        # Fallback: when CRM has no revenue, use Shopify as primary
        if total_rev == 0 and shopify_revenue > 0:
            total_rev = shopify_revenue
            total_rev_usd = convert_to_usd(shopify_revenue, shopify_currency)
        if new_customers == 0 and shopify_order_count > 0:
            new_customers = shopify_order_count
            if total_investment > 0 and new_customers > 0:
                cac = round(total_investment / new_customers, 2)

        header_kpis = SalesHeaderKpisDTO(
            total_revenue=total_rev,
            total_revenue_usd=total_rev_usd,
            currency=display_currency,
            new_customers=new_customers,
            cac=cac,
            cac_incomplete=False,
            net_sales=shopify_agg.get("net_sales", 0.0),
            total_discounts=shopify_agg.get("total_discounts", 0.0),
            total_tax=shopify_agg.get("total_tax", 0.0),
            refund_count=int(shopify_agg.get("refund_count", 0)),
            refund_amount=shopify_agg.get("refund_amount", 0.0),
            shipping_revenue=shopify_agg.get("shipping_revenue", 0.0),
            repeat_customers=int(shopify_agg.get("repeat_customers", 0)),
            discount_usage_count=int(shopify_agg.get("discount_usage_count", 0)),
            shopify_revenue=shopify_revenue,
            shopify_order_count=shopify_order_count,
            shopify_avg_order_value=shopify_avg_order,
            shopify_currency=shopify_currency,
        )

        return header_kpis, new_customers, total_rev

    async def get_metrics(
        self,
        tenant_id: UUID,
        start_date: "object",
        end_date: "object",
    ) -> SalesDetailDTO:
        """Return sales-stage (Stage 4) metrics."""
        from datetime import datetime as dt_cls

        from src.modules.analytics.infrastructure.repositories.sales_metrics_repository import (
            SalesMetricsRepository,
        )

        # 1. Check cache
        if self.cache is not None:
            cached = await self.cache.get(str(tenant_id), "sales", "last_30_days")
            if cached is not None:
                return SalesDetailDTO(**cached)

        # 2. Query raw sales aggregations
        sales_repo = SalesMetricsRepository(self.db)
        raw_sales = sales_repo.get_sales_summary(tenant_id, start_date, end_date)

        # 3. Get all offers for enrichment via OfferReadPort
        offer_map = {}
        if self.offer_port is not None:
            offers = await self.offer_port.get_offers_by_tenant(tenant_id)
            offer_map = {str(o.id): o for o in offers}

        # 4. Group sales by stage
        stage_data, stage_revenue, display_currency = _group_raw_sales(
            raw_sales,
            offer_map,
        )

        # 5. Build RevenueGroupDTOs
        total_revenue_all = sum(stage_revenue.values())
        adquisicion = _build_revenue_group(
            "adquisicion",
            "Adquisicion",
            stage_data,
            stage_revenue,
            total_revenue_all,
            offer_map,
            display_currency,
        )
        expansion = _build_revenue_group(
            "expansion",
            "Expansion",
            stage_data,
            stage_revenue,
            total_revenue_all,
            offer_map,
            display_currency,
        )

        # 6. Header KPIs + Shopify enrichment
        new_customers = sales_repo.get_total_conversion_customers(
            tenant_id,
            start_date,
            end_date,
        )
        cost_svc = StageCostService(self.db)
        total_investment, cost_complete = cost_svc.get_total_funnel_investment(
            tenant_id,
            start_date,
            end_date,
        )
        cac = round(total_investment / new_customers, 2) if new_customers > 0 else None
        total_rev_usd = convert_to_usd(total_revenue_all, display_currency)

        header_kpis, new_customers, total_rev = self._enrich_with_shopify(
            tenant_id,
            start_date,
            end_date,
            display_currency,
            total_revenue_all,
            total_rev_usd,
            new_customers,
            total_investment,
            cac,
        )
        header_kpis.cac_incomplete = not cost_complete

        # 7. Mini funnel: SQLs -> Customers
        sql_count = sales_repo.get_total_sql_count(tenant_id, start_date, end_date)
        conv_rate = round(new_customers / sql_count * 100, 2) if sql_count > 0 else 0.0

        mini_funnel = MiniFunnelDTO(
            source_label="Oportunidades",
            source_value=sql_count,
            target_label="Ventas",
            target_value=new_customers,
            conversion_rate=conv_rate,
        )

        # 8. Bottleneck detection
        bottlenecks = _build_sales_bottlenecks(
            conv_rate,
            sql_count,
            cac,
            new_customers,
            total_rev,
        )

        now = dt_cls.now(UTC)

        result = SalesDetailDTO(
            header_kpis=header_kpis,
            mini_funnel=mini_funnel,
            adquisicion=adquisicion,
            expansion=expansion,
            bottlenecks=bottlenecks,
            period="last_30_days",
            last_updated=now.isoformat(),
        )

        # 9. Set cache
        if self.cache is not None:
            await self.cache.set(
                str(tenant_id),
                "sales",
                "last_30_days",
                result.model_dump(),
            )

        return result
