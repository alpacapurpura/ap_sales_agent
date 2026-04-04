"""Sales stage service — extracted from MetricsService.

Handles get_sales_metrics() logic: revenue by offer, tier grouping,
subscription splits, CAC, Shopify enrichment, bottleneck detection.
"""

from collections import defaultdict
from typing import Dict, List, Optional
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
    convert_to_usd,
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


class SalesStageService:
    """Provides sales stage metrics for the Bowtie dashboard."""

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

    async def get_metrics(
        self,
        tenant_id: UUID,
        start_date: "object",
        end_date: "object",
    ) -> SalesDetailDTO:
        """Return sales-stage (Stage 4) metrics.

        Flow:
        1. Check MetricsCache (300s TTL for sales stage)
        2. On miss: query SalesMetricsRepository for raw aggregations
        3. Query OfferReadPort for offer enrichment (names, value_levels, pricing_type)
        4. Group sales by stage (CONVERSION->adquisicion, EXPANSION->expansion)
        5. Sub-group by tier using get_tier_for_value_level
        6. Build per-offer OfferSaleDTOs with source breakdown and subscription split
        7. Calculate header KPIs (revenue, new_customers, CAC)
        8. Build mini funnel (SQLs -> Customers)
        9. Detect bottlenecks (low_conversion_rate, high_cac_ratio)
        10. Cache result and return SalesDetailDTO
        """
        from datetime import datetime as dt_cls, timezone as tz
        from src.modules.analytics.infrastructure.repositories.sales_metrics_repository import (
            SalesMetricsRepository,
        )

        # 1. Check cache
        if self.cache is not None:
            cached = await self.cache.get(
                str(tenant_id), "sales", "last_30_days"
            )
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

        # 4. Group sales by stage -> offer_id -> accumulate
        # Structure: {stage_key: {offer_id_str: {source: str, counts/revenue}}}
        stage_data: Dict[str, Dict[str, dict]] = {
            "adquisicion": {},
            "expansion": {},
        }

        # Track per-stage customer counts and revenue totals
        _stage_customer_counts: Dict[str, int] = {"adquisicion": 0, "expansion": 0}
        stage_revenue: Dict[str, float] = {"adquisicion": 0.0, "expansion": 0.0}

        for row in raw_sales:
            # row: (stage, offer_id, source, currency, count, total_revenue, unique_customers)
            stage_val = row[0]
            offer_id = str(row[1])
            source = row[2] or "MANUAL"
            currency = row[3] or "USD"
            count = int(row[4])
            revenue = float(row[5])
            unique_custs = int(row[6])

            # Map SaleStage to group key
            stage_str = stage_val.value if hasattr(stage_val, "value") else str(stage_val)
            if stage_str == "CONVERSION":
                stage_key = "adquisicion"
            elif stage_str == "EXPANSION":
                stage_key = "expansion"
            else:
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

        # 5. Also include unsold offers from the catalog (show with $0)
        for offer_id_str, offer in offer_map.items():
            for stage_key in ("adquisicion", "expansion"):
                if offer_id_str not in stage_data[stage_key]:
                    # Only add to adquisicion for unsold offers
                    if stage_key == "adquisicion":
                        stage_data[stage_key][offer_id_str] = {
                            "count": 0,
                            "revenue": 0.0,
                            "currency": offer.currency,
                            "sources": {},
                            "unique_customers": 0,
                        }

        # Determine tenant display currency (most common from sales)
        currency_counts: Dict[str, int] = defaultdict(int)
        for row in raw_sales:
            currency_counts[row[3] or "USD"] += int(row[4])
        display_currency = max(currency_counts, key=currency_counts.get) if currency_counts else "USD"

        # 6. Build RevenueGroupDTO for each stage
        total_revenue_all = sum(stage_revenue.values())

        def _build_revenue_group(
            stage_key: str, group_label: str
        ) -> RevenueGroupDTO:
            offers_by_tier: Dict[str, List[OfferSaleDTO]] = defaultdict(list)
            group_revenue = stage_revenue[stage_key]
            group_customers = 0

            for offer_id_str, data in stage_data[stage_key].items():
                offer = offer_map.get(offer_id_str)

                # Determine tier
                value_level = offer.value_level if offer else None
                tier = get_tier_for_value_level(value_level)

                # Skip lead magnets (don't generate revenue)
                if value_level and value_level in ("lead_magnet", "level_0_free"):
                    continue

                # Build OfferSaleDTO
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
                    else:  # expansion
                        renewals = data["count"]
                        renewal_rev = data["revenue"]
                    sub_new_label = labels.get("new_label")
                    sub_renewal_label = labels.get("renewal_label")

                offer_dto = OfferSaleDTO(
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
                offers_by_tier[tier].append(offer_dto)
                group_customers += data["unique_customers"]

            # Build TierGroupDTOs in display order
            tiers = []
            for tier_key in TIER_DISPLAY_ORDER:
                if tier_key in offers_by_tier:
                    tiers.append(TierGroupDTO(
                        tier_key=tier_key,
                        tier_label=TIER_LABELS[tier_key],
                        offers=offers_by_tier[tier_key],
                    ))

            rev_pct = round(group_revenue / total_revenue_all * 100, 1) if total_revenue_all > 0 else 0.0
            group_usd = convert_to_usd(group_revenue, display_currency)

            return RevenueGroupDTO(
                group_key=stage_key,
                group_label=group_label,
                total_revenue=group_revenue,
                total_revenue_usd=group_usd,
                customer_count=group_customers,
                revenue_percentage=rev_pct,
                currency=display_currency,
                tiers=tiers,
            )

        adquisicion = _build_revenue_group("adquisicion", "Adquisicion")
        expansion = _build_revenue_group("expansion", "Expansion")

        # 7. Header KPIs
        new_customers = sales_repo.get_total_conversion_customers(
            tenant_id, start_date, end_date
        )

        cost_svc = StageCostService(self.db)
        total_investment, cost_complete = cost_svc.get_total_funnel_investment(
            tenant_id, start_date, end_date
        )
        cac = round(total_investment / new_customers, 2) if new_customers > 0 else None
        cac_incomplete = not cost_complete

        total_rev = total_revenue_all
        total_rev_usd = convert_to_usd(total_rev, display_currency)

        # Enrich with Shopify metrics from official_metrics
        official_repo = OfficialMetricsRepository(self.db)
        shopify_agg = official_repo.get_channel_metrics(
            tenant_id, "shopify", "shopify", start_date.date(), end_date.date(),
        )

        # Extract Shopify aggregates
        shopify_revenue = shopify_agg.get("revenue", 0.0)
        shopify_order_count = int(shopify_agg.get("order_count", 0))
        shopify_avg_order = shopify_agg.get("avg_order_value", 0.0)

        # Determine Shopify currency from stored metrics
        shopify_currency = display_currency
        if shopify_revenue > 0:
            sample_rows = official_repo.get_metrics(
                tenant_id, channel_slug="shopify", metric_name="revenue",
                start_date=start_date.date(), end_date=end_date.date(),
            )
            if sample_rows:
                shopify_currency = sample_rows[0].currency or "USD"
                if not currency_counts:
                    display_currency = shopify_currency

        # FALLBACK: when CRM has no revenue, use Shopify as primary
        if total_rev == 0 and shopify_revenue > 0:
            total_rev = shopify_revenue
            total_rev_usd = convert_to_usd(shopify_revenue, shopify_currency)
        if new_customers == 0 and shopify_order_count > 0:
            new_customers = shopify_order_count
            # Recalculate CAC with updated new_customers
            if total_investment > 0 and new_customers > 0:
                cac = round(total_investment / new_customers, 2)

        header_kpis = SalesHeaderKpisDTO(
            total_revenue=total_rev,
            total_revenue_usd=total_rev_usd,
            currency=display_currency,
            new_customers=new_customers,
            cac=cac,
            cac_incomplete=cac_incomplete,
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

        # 8. Mini funnel: SQLs -> Customers
        sql_count = sales_repo.get_total_sql_count(tenant_id, start_date, end_date)
        conv_rate = round(new_customers / sql_count * 100, 2) if sql_count > 0 else 0.0

        mini_funnel = MiniFunnelDTO(
            source_label="Oportunidades",
            source_value=sql_count,
            target_label="Ventas",
            target_value=new_customers,
            conversion_rate=conv_rate,
        )

        # 9. Bottleneck detection
        bottlenecks: list[BottleneckDTO] = []

        # Low conversion rate (SQL -> Customer)
        if sql_count > 0:
            if conv_rate < LOW_CONVERSION_THRESHOLDS["critical"]:
                bottlenecks.append(BottleneckDTO(
                    type="low_conversion_rate",
                    metric_label="Tasa de Conversion",
                    current_rate=conv_rate,
                    severity="critical",
                    threshold=LOW_CONVERSION_THRESHOLDS["critical"],
                    tip="Baja conversion de oportunidades a ventas -- revisa tu proceso de cierre",
                ))
            elif conv_rate < LOW_CONVERSION_THRESHOLDS["warning"]:
                bottlenecks.append(BottleneckDTO(
                    type="low_conversion_rate",
                    metric_label="Tasa de Conversion",
                    current_rate=conv_rate,
                    severity="warning",
                    threshold=LOW_CONVERSION_THRESHOLDS["warning"],
                    tip="Baja conversion de oportunidades a ventas -- revisa tu proceso de cierre",
                ))

        # High CAC ratio (CAC / AOV)
        if cac is not None and new_customers > 0 and total_rev > 0:
            aov = total_rev / new_customers
            cac_ratio = cac / aov if aov > 0 else 0.0
            if cac_ratio >= HIGH_CAC_CRITICAL_RATIO:
                bottlenecks.append(BottleneckDTO(
                    type="high_cac_ratio",
                    metric_label="CAC / Ticket Promedio",
                    current_rate=round(cac_ratio * 100, 1),
                    severity="critical",
                    threshold=HIGH_CAC_CRITICAL_RATIO * 100,
                    tip="Tu costo de adquisicion es alto respecto al ticket promedio -- optimiza tu funnel pre-venta",
                ))
            elif cac_ratio >= HIGH_CAC_WARNING_RATIO:
                bottlenecks.append(BottleneckDTO(
                    type="high_cac_ratio",
                    metric_label="CAC / Ticket Promedio",
                    current_rate=round(cac_ratio * 100, 1),
                    severity="warning",
                    threshold=HIGH_CAC_WARNING_RATIO * 100,
                    tip="Tu costo de adquisicion es alto respecto al ticket promedio -- optimiza tu funnel pre-venta",
                ))

        now = dt_cls.now(tz.utc)

        result = SalesDetailDTO(
            header_kpis=header_kpis,
            mini_funnel=mini_funnel,
            adquisicion=adquisicion,
            expansion=expansion,
            bottlenecks=bottlenecks,
            period="last_30_days",
            last_updated=now.isoformat(),
        )

        # 10. Set cache
        if self.cache is not None:
            await self.cache.set(
                str(tenant_id),
                "sales",
                "last_30_days",
                result.model_dump(),
            )

        return result
