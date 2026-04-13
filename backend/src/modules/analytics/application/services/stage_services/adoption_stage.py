"""Adoption stage service — extracted from MetricsService.

Handles get_adoption_metrics() logic: customer health per offer,
TTV, refunds, bottleneck detection.
"""

from datetime import UTC
from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.analytics.application.dto.adoption_dto import (
    AdoptionDetailDTO,
    AdoptionHeaderKpisDTO,
    OfferHealthDTO,
)
from src.modules.analytics.application.dto.capture_dto import MiniFunnelDTO
from src.modules.analytics.application.dto.opportunity_dto import BottleneckDTO
from src.modules.analytics.domain.ports import ConnectionPort, OfferReadPort
from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache
from src.shared.domain.currency import convert_to_usd


def _build_adoption_bottlenecks(
    health_pct: float,
    avg_ttv: float | None,
    offer_list: list[OfferHealthDTO],
) -> list[BottleneckDTO]:
    """Detect adoption bottlenecks based on health thresholds."""
    bottlenecks: list[BottleneckDTO] = []

    # Overall health bottleneck
    if health_pct < 70.0:
        if avg_ttv is not None and avg_ttv > 7:
            tip = (
                "Mejora tu proceso de bienvenida -- tus clientes tardan "
                "mucho en empezar a usar tu producto"
            )
        else:
            tip = (
                "Contacta a tus clientes inactivos con un mensaje "
                "personalizado o una oferta especial para reactivarlos"
            )
        bottlenecks.append(
            BottleneckDTO(
                type="low_adoption_health",
                metric_label="Salud del cliente",
                current_rate=health_pct,
                severity="warning",
                threshold=70.0,
                tip=tip,
            ),
        )

    # Per-offer bottleneck
    bottlenecks.extend(
        BottleneckDTO(
            type="offer_low_health",
            metric_label=f"Salud: {offer.public_name}",
            current_rate=offer.health_pct,
            severity="warning",
            threshold=60.0,
            tip=(
                "Revisa el engagement de este producto -- mas de "
                "la mitad de sus clientes estan inactivos"
            ),
        )
        for offer in offer_list
        if offer.health_pct < 60.0
    )

    return bottlenecks


class AdoptionStageService:
    """Provides adoption stage metrics for the Bowtie dashboard."""

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

    async def get_metrics(
        self,
        tenant_id: UUID,
        start_date: "object",
        end_date: "object",
    ) -> AdoptionDetailDTO:
        """Return adoption-stage (Stage 5) metrics.

        Flow:
        1. Check MetricsCache
        2. On miss: query AdoptionMetricsRepository for health, TTV, refunds
        3. Query OfferReadPort for offer name enrichment
        4. Build per-offer OfferHealthDTOs
        5. Calculate header KPIs (distinct customer counts, not per-offer sums)
        6. Build mini funnel (Ventas -> Activos)
        7. Detect bottlenecks (overall health < 70%, per-offer health < 60%)
        8. Cache result and return AdoptionDetailDTO
        """
        from datetime import datetime as dt_cls

        from src.modules.analytics.infrastructure.repositories.adoption_repository import (
            AdoptionMetricsRepository,
        )

        # 1. Check cache
        if self.cache is not None:
            cached = await self.cache.get(str(tenant_id), "adoption", "last_30_days")
            if cached is not None:
                return AdoptionDetailDTO(**cached)

        # 2. Query repository
        repo = AdoptionMetricsRepository(self.db)
        health_rows = repo.get_customer_health_by_offer(tenant_id, start_date, end_date)
        ttv_map = repo.get_avg_ttv_by_offer(tenant_id, start_date, end_date)
        total_customers, total_sales = repo.get_total_customers_and_sales(
            tenant_id,
            start_date,
            end_date,
        )
        refund_count, refund_amount, refund_currency = repo.get_refunds(
            tenant_id,
            start_date,
            end_date,
        )

        # 3. Get offer names via OfferReadPort
        offer_name_map: dict[str, str] = {}
        if self.offer_port is not None:
            offers = await self.offer_port.get_offers_by_tenant(tenant_id)
            offer_name_map = {str(o.id): o.public_name for o in offers}

        # 4. Build per-offer OfferHealthDTOs
        offer_list: list[OfferHealthDTO] = []
        for row in health_rows:
            offer_id_str = str(row[0])
            total = int(row[1])
            active = int(row[2])
            inactive = int(row[3])
            health = round(active / total * 100, 1) if total > 0 else 0.0
            public_name = offer_name_map.get(offer_id_str, "Oferta")

            offer_list.append(
                OfferHealthDTO(
                    offer_id=offer_id_str,
                    public_name=public_name,
                    total_customers=total,
                    active_count=active,
                    inactive_count=inactive,
                    health_pct=health,
                    ttv_days=ttv_map.get(offer_id_str),
                ),
            )

        # 5. Header KPIs -- use distinct total counts (avoid double-counting)
        total_active_per_offer = sum(int(row[2]) for row in health_rows)
        total_inactive_per_offer = sum(int(row[3]) for row in health_rows)

        # If per-offer sums exceed distinct total, customer bought multiple offers
        if total_active_per_offer + total_inactive_per_offer > total_customers > 0:
            active_customers = total_customers - total_inactive_per_offer
            active_customers = max(active_customers, 0)
            inactive_customers = total_customers - active_customers
        else:
            active_customers = total_active_per_offer
            inactive_customers = total_inactive_per_offer

        health_pct = (
            round(active_customers / total_customers * 100, 1)
            if total_customers > 0
            else 0.0
        )

        # Global avg TTV
        all_ttvs = list(ttv_map.values())
        avg_ttv = round(sum(all_ttvs) / len(all_ttvs), 1) if all_ttvs else None

        refund_amount_usd = convert_to_usd(refund_amount, refund_currency)

        header_kpis = AdoptionHeaderKpisDTO(
            active_customers=active_customers,
            inactive_customers=inactive_customers,
            health_pct=health_pct,
            avg_ttv_days=avg_ttv,
            refund_count=refund_count,
            refund_amount=refund_amount,
            refund_currency=refund_currency,
            refund_amount_usd=refund_amount_usd,
        )

        # 6. Mini funnel: Ventas -> Activos
        conv_rate = (
            round(active_customers / total_sales * 100, 1) if total_sales > 0 else 0.0
        )
        mini_funnel = MiniFunnelDTO(
            source_label="Ventas",
            source_value=total_sales,
            target_label="Activos",
            target_value=active_customers,
            conversion_rate=conv_rate,
        )

        # 7. Bottleneck detection
        bottlenecks = _build_adoption_bottlenecks(health_pct, avg_ttv, offer_list)

        now = dt_cls.now(UTC)

        result = AdoptionDetailDTO(
            header_kpis=header_kpis,
            mini_funnel=mini_funnel,
            offers=offer_list,
            bottlenecks=bottlenecks,
            period="last_30_days",
            last_updated=now.isoformat(),
        )

        # 8. Set cache
        if self.cache is not None:
            await self.cache.set(
                str(tenant_id),
                "adoption",
                "last_30_days",
                result.model_dump(),
            )

        return result
