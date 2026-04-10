"""Group Meta Ads metrics by offer for the multi-offer dashboard view.

For each active association, this service computes:
- total spend, impressions, clicks, reach (secondary metrics)
- primary result count (lead/message/purchase/... depending on expected_metric)
- primary cost per result (spend / primary_result_count)
- ROAS (only for PURCHASE/SUBSCRIPTION)
- daily timeseries of spend + primary_result

It also aggregates unassigned-campaign spend and branding-only spend into
separate buckets so the frontend can render the segmenter UI.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from src.modules.advertising.application.dto.metrics_by_offer_dto import (
    BrandingAggregateDTO,
    MetricsByOfferDTO,
    OfferMetricsDTO,
    OfferTimeSeriesPointDTO,
    UnassignedAggregateDTO,
)
from src.modules.advertising.domain.enums import (
    AssociationType,
    OfferExpectedMetric,
    expected_metric_label_es,
    resolve_expected_metric,
)
from src.modules.advertising.infrastructure.repositories.association_repository import (
    AssociationRepository,
)
from src.modules.advertising.infrastructure.repositories.metrics_repository import (
    MetricRow,
    MetricsRepository,
    resolve_period_window,
)

if TYPE_CHECKING:
    from datetime import date
    from uuid import UUID

    from sqlalchemy.orm import Session

    from src.shared.domain.ports import OfferReadDTO, OfferReadPort

_PRIMARY_METRIC_CONFIG: dict[OfferExpectedMetric, dict] = {
    OfferExpectedMetric.LEAD: {
        "metric_names": {"meta_leads", "meta_registrations"},
        "label": "Costo por Lead",
        "unit": "currency",
    },
    OfferExpectedMetric.MESSAGE: {
        "metric_names": {"meta_conversations_started"},
        "label": "Costo por Mensaje",
        "unit": "currency",
    },
    OfferExpectedMetric.PURCHASE: {
        "metric_names": {"conversions"},
        "label": "Costo por Compra",
        "unit": "currency",
    },
    OfferExpectedMetric.SUBSCRIPTION: {
        "metric_names": {"conversions"},
        "label": "Costo por Suscripción",
        "unit": "currency",
    },
    OfferExpectedMetric.CALL_BOOKED: {
        "metric_names": {"meta_conversations_started"},
        "label": "Costo por Llamada",
        "unit": "currency",
    },
    OfferExpectedMetric.FORM_SUBMIT: {
        "metric_names": {"meta_leads"},
        "label": "Costo por Formulario",
        "unit": "currency",
    },
}

_ROAS_METRICS = {OfferExpectedMetric.PURCHASE, OfferExpectedMetric.SUBSCRIPTION}
_SECONDARY_METRIC_NAMES = {
    "spend",
    "impressions",
    "clicks",
    "reach",
    "ctr",
    "cpc",
    "cpm",
}
_RELEVANT_METRIC_NAMES = _SECONDARY_METRIC_NAMES | {
    "meta_leads",
    "meta_registrations",
    "meta_conversations_started",
    "conversions",
    "meta_conversion_value",
}


class MetricsByOfferService:
    """Compose MetricsByOfferDTO from associations + official metrics."""

    def __init__(self, db: Session, offer_read_port: OfferReadPort) -> None:
        self._db = db
        self._offer_read_port = offer_read_port
        self._association_repo = AssociationRepository(db)
        self._metrics_repo = MetricsRepository(db)

    async def run(self, tenant_id: UUID, period: str = "30d") -> MetricsByOfferDTO:
        start_date, end_date = resolve_period_window(period)
        currency = self._metrics_repo.detect_currency(tenant_id)
        rows = self._metrics_repo.load_rows(
            tenant_id,
            start_date=start_date,
            end_date=end_date,
            metric_names=list(_RELEVANT_METRIC_NAMES),
        )

        associations = self._association_repo.list_active(tenant_id)
        offers = await self._offer_read_port.get_offers_by_tenant(tenant_id)
        offer_by_id = {o.id: o for o in offers}

        # Build {offer_id: list[target_ids]} per target_type
        campaign_ids_by_offer: dict[UUID, set[str]] = defaultdict(set)
        adset_ids_by_offer: dict[UUID, set[str]] = defaultdict(set)
        branded_campaign_ids: set[str] = set()

        for a in associations:
            if a.association_type == AssociationType.EXCLUDED_BRANDING.value:
                if a.target_type == "campaign":
                    branded_campaign_ids.add(a.target_external_id)
                continue
            if a.offer_id is None:
                continue
            if a.target_type == "campaign":
                campaign_ids_by_offer[a.offer_id].add(a.target_external_id)
            elif a.target_type == "ad_set":
                adset_ids_by_offer[a.offer_id].add(a.target_external_id)

        offers_out: list[OfferMetricsDTO] = []
        assigned_campaign_ids: set[str] = set()
        assigned_adset_ids: set[str] = set()

        for campaign_ids in campaign_ids_by_offer.values():
            assigned_campaign_ids.update(campaign_ids)
        for adset_ids in adset_ids_by_offer.values():
            assigned_adset_ids.update(adset_ids)

        # Compute metrics per offer
        offer_ids_with_associations = set(campaign_ids_by_offer.keys()) | set(
            adset_ids_by_offer.keys()
        )
        for offer_id in offer_ids_with_associations:
            offer = offer_by_id.get(offer_id)
            if offer is None:
                continue
            expected = resolve_expected_metric(
                archetype=offer.offer_type,
                onboarding_action=offer.onboarding_action,
                is_lead_magnet=offer.is_lead_magnet,
                has_checkout_url=bool(offer.checkout_page_url),
            )
            campaign_ids = campaign_ids_by_offer.get(offer_id, set())
            adset_ids = adset_ids_by_offer.get(offer_id, set())
            filtered = [
                r
                for r in rows
                if (r.campaign_id in campaign_ids or r.ad_set_id in adset_ids)
            ]
            offers_out.append(
                self._build_offer_metrics(
                    offer=offer,
                    expected=expected,
                    rows=filtered,
                    currency=currency,
                )
            )

        # Unassigned aggregate: campaigns with effective metrics but no association,
        # NOT branded
        unassigned = self._aggregate_unassigned(
            rows=rows,
            assigned_campaign_ids=assigned_campaign_ids,
            assigned_adset_ids=assigned_adset_ids,
            branded_campaign_ids=branded_campaign_ids,
        )

        branding_only = self._aggregate_branding(
            rows=rows, branded_campaign_ids=branded_campaign_ids
        )

        return MetricsByOfferDTO(
            period=period,
            start_date=start_date,
            end_date=end_date,
            currency=currency,
            offers=offers_out,
            unassigned=unassigned,
            branding_only=branding_only,
        )

    def _build_offer_metrics(
        self,
        *,
        offer: OfferReadDTO,
        expected: OfferExpectedMetric,
        rows: list[MetricRow],
        currency: str | None,
    ) -> OfferMetricsDTO:
        config = _PRIMARY_METRIC_CONFIG.get(expected)
        primary_metric_names: set[str] = (
            set(config["metric_names"]) if config else set()
        )
        primary_label = config["label"] if config else "Resultado"
        primary_unit = config["unit"] if config else "currency"

        total_spend = sum(r.value for r in rows if r.metric_name == "spend")
        impressions = sum(r.value for r in rows if r.metric_name == "impressions")
        clicks = sum(r.value for r in rows if r.metric_name == "clicks")
        reach = sum(r.value for r in rows if r.metric_name == "reach")

        primary_count = sum(
            r.value for r in rows if r.metric_name in primary_metric_names
        )

        ctr = (clicks / impressions * 100.0) if impressions else 0.0
        cpc = (total_spend / clicks) if clicks else 0.0
        cpm = (total_spend / impressions * 1000.0) if impressions else 0.0

        primary_cost_per_result: float | None
        metric_unavailable_reason: str | None = None
        if primary_count > 0:
            primary_cost_per_result = round(total_spend / primary_count, 2)
        else:
            primary_cost_per_result = None
            if not primary_metric_names:
                metric_unavailable_reason = "metric_not_supported"
            elif total_spend > 0:
                metric_unavailable_reason = "no_events_reported"

        # ROAS only when expected is PURCHASE/SUBSCRIPTION and we have conversion_value
        roas: float | None = None
        if expected in _ROAS_METRICS:
            conversion_value = sum(
                r.value for r in rows if r.metric_name == "meta_conversion_value"
            )
            if total_spend > 0:
                roas = round(conversion_value / total_spend, 2)

        timeseries = self._build_timeseries(
            rows=rows, primary_metric_names=primary_metric_names
        )

        return OfferMetricsDTO(
            offer_id=offer.id,
            offer_name=offer.public_name,
            archetype=offer.offer_type,
            expected_metric=expected.value,
            expected_metric_label_es=expected_metric_label_es(expected.value),
            total_spend=round(total_spend, 2),
            currency=offer.currency or currency or "USD",
            primary_result_count=round(primary_count, 2),
            primary_cost_per_result=primary_cost_per_result,
            primary_metric_name=primary_label,
            primary_metric_unit=primary_unit,
            roas=roas,
            secondary_metrics={
                "impressions": round(impressions, 2),
                "clicks": round(clicks, 2),
                "reach": round(reach, 2),
                "ctr": round(ctr, 2),
                "cpc": round(cpc, 2),
                "cpm": round(cpm, 2),
            },
            timeseries=timeseries,
            metric_unavailable_reason=metric_unavailable_reason,
        )

    @staticmethod
    def _build_timeseries(
        *, rows: list[MetricRow], primary_metric_names: set[str]
    ) -> list[OfferTimeSeriesPointDTO]:
        by_day: dict[date, dict[str, float]] = defaultdict(
            lambda: {"spend": 0.0, "primary": 0.0}
        )
        for r in rows:
            if r.metric_name == "spend":
                by_day[r.metric_date]["spend"] += r.value
            elif r.metric_name in primary_metric_names:
                by_day[r.metric_date]["primary"] += r.value

        return [
            OfferTimeSeriesPointDTO(
                date=day.isoformat(),
                spend=round(values["spend"], 2),
                primary_result=round(values["primary"], 2),
            )
            for day, values in sorted(by_day.items())
        ]

    def _aggregate_unassigned(
        self,
        *,
        rows: list[MetricRow],
        assigned_campaign_ids: set[str],
        assigned_adset_ids: set[str],
        branded_campaign_ids: set[str],
    ) -> UnassignedAggregateDTO:
        unassigned_targets: set[str] = set()
        total_spend = 0.0
        impressions = 0.0
        clicks = 0.0
        for r in rows:
            if r.campaign_id and r.campaign_id in branded_campaign_ids:
                continue
            if r.campaign_id and r.campaign_id in assigned_campaign_ids:
                continue
            if r.ad_set_id and r.ad_set_id in assigned_adset_ids:
                continue
            if r.campaign_id:
                unassigned_targets.add(f"campaign:{r.campaign_id}")
            if r.ad_set_id:
                unassigned_targets.add(f"ad_set:{r.ad_set_id}")
            if r.metric_name == "spend":
                total_spend += r.value
            elif r.metric_name == "impressions":
                impressions += r.value
            elif r.metric_name == "clicks":
                clicks += r.value
        return UnassignedAggregateDTO(
            target_count=len(unassigned_targets),
            total_spend=round(total_spend, 2),
            impressions=round(impressions, 2),
            clicks=round(clicks, 2),
        )

    def _aggregate_branding(
        self, *, rows: list[MetricRow], branded_campaign_ids: set[str]
    ) -> BrandingAggregateDTO:
        total_spend = 0.0
        reach = 0.0
        impressions = 0.0
        seen: set[str] = set()
        for r in rows:
            if r.campaign_id not in branded_campaign_ids:
                continue
            seen.add(r.campaign_id)
            if r.metric_name == "spend":
                total_spend += r.value
            elif r.metric_name == "reach":
                reach += r.value
            elif r.metric_name == "impressions":
                impressions += r.value
        return BrandingAggregateDTO(
            target_count=len(seen),
            total_spend=round(total_spend, 2),
            reach=round(reach, 2),
            impressions=round(impressions, 2),
        )


__all__ = ["MetricsByOfferService"]
