"""Group Meta Ads metrics by offer for the multi-offer dashboard view.

For each active association, this service computes:
- total spend, impressions, clicks, reach (secondary metrics)
- primary result count (lead/message/purchase/... depending on expected_metric)
- primary cost per result (spend / primary_result_count)
- ROAS (only for PURCHASE/SUBSCRIPTION)
- daily timeseries of spend + primary_result
- a 5-step Meta Ads funnel filtered to the offer's campaigns

It also aggregates unassigned-campaign spend and branding-only spend into
separate buckets so the frontend can render the segmenter UI, plus a
"Todas" (`funnel_all` / `reach_all`) context for the default segmenter state.

Design source of truth:
`docs/superpowers/artifacts/2026-04-10-meta-ads-resumen/CONTRACT.md`

Reach rules (non-negotiable):
- len(campaign_ids) == 0 → reach = None
- len(campaign_ids) == 1 → reach from period_metrics matching that campaign,
  or None if no row exists
- len(campaign_ids) >= 2 → reach = None (audience overlap is not additive)
- Channel-level `reach_all` comes from the period_metrics row with
  `campaign_id IS NULL`.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from src.modules.advertising.application.dto.metrics_by_offer_dto import (
    BrandingAggregateDTO,
    FunnelStepDTO,
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
from src.shared.domain.locale import TenantLocale

if TYPE_CHECKING:
    from datetime import date
    from uuid import UUID

    from sqlalchemy.orm import Session

    from src.modules.analytics.infrastructure.models.period_metrics_model import (
        PeriodMetricModel,
    )
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

# Canonical Meta Ads funnel (5 steps). Semantics mirror
# `channel_dashboard_service._build_funnel` for consistency — the only
# reason this is duplicated is the DDD cross-module import prohibition
# (see CONTRACT §1c).
_FUNNEL_STEPS: list[tuple[str, str]] = [
    ("Impresiones", "impressions"),
    ("Clics", "clicks"),
    ("Visitas a Landing", "meta_landing_page_views"),
    ("Leads", "meta_leads"),
    ("Compras", "conversions"),
]
_FUNNEL_METRIC_NAMES = {metric for _, metric in _FUNNEL_STEPS}

# Metrics to load in a single DB roundtrip. Includes funnel metrics so
# `_build_funnel_for_campaigns` can filter in-memory.
_SECONDARY_METRIC_NAMES = {
    "spend",
    "impressions",
    "clicks",
}
_RELEVANT_METRIC_NAMES = (
    _SECONDARY_METRIC_NAMES
    | _FUNNEL_METRIC_NAMES
    | {
        "meta_registrations",
        "meta_conversations_started",
        "meta_conversion_value",
    }
)


class MetricsByOfferService:
    """Compose MetricsByOfferDTO from associations + official metrics."""

    def __init__(self, db: Session, offer_read_port: OfferReadPort) -> None:
        self._db = db
        self._offer_read_port = offer_read_port
        self._association_repo = AssociationRepository(db)
        self._metrics_repo = MetricsRepository(db)

    async def run(
        self,
        tenant_id: UUID,
        period: str = "30d",
        tenant_locale: TenantLocale | None = None,
    ) -> MetricsByOfferDTO:
        locale = tenant_locale or TenantLocale.default()
        start_date, end_date = resolve_period_window(period, tz=locale.timezone)
        currency = self._metrics_repo.detect_currency(tenant_id)
        rows = self._metrics_repo.load_rows(
            tenant_id,
            start_date=start_date,
            end_date=end_date,
            metric_names=list(_RELEVANT_METRIC_NAMES),
        )

        # Single roundtrip: load every reach row for the window. The
        # result contains both the channel-level row (campaign_id IS NULL)
        # used for `reach_all`, and per-campaign rows used by offers.
        period_reach_rows = self._metrics_repo.list_period_metrics_for_reach(
            tenant_id,
            start_date=start_date,
            end_date=end_date,
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

        assigned_campaign_ids: set[str] = set()
        assigned_adset_ids: set[str] = set()
        for campaign_ids in campaign_ids_by_offer.values():
            assigned_campaign_ids.update(campaign_ids)
        for adset_ids in adset_ids_by_offer.values():
            assigned_adset_ids.update(adset_ids)

        offers_out: list[OfferMetricsDTO] = []
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
                    all_rows=rows,
                    campaign_ids=campaign_ids,
                    adset_ids=adset_ids,
                    currency=currency,
                    period_reach_rows=period_reach_rows,
                )
            )

        unassigned = self._aggregate_unassigned(
            rows=rows,
            assigned_campaign_ids=assigned_campaign_ids,
            assigned_adset_ids=assigned_adset_ids,
            branded_campaign_ids=branded_campaign_ids,
            period_reach_rows=period_reach_rows,
        )

        branding_only = self._aggregate_branding(
            rows=rows,
            branded_campaign_ids=branded_campaign_ids,
            period_reach_rows=period_reach_rows,
        )

        funnel_all = self._build_funnel_for_campaigns(
            rows=rows,
            campaign_ids=None,  # no filter → global
            ad_set_ids=None,
        )
        reach_all = self._compute_reach_all(period_reach_rows)

        return MetricsByOfferDTO(
            period=period,
            start_date=start_date,
            end_date=end_date,
            currency=currency,
            offers=offers_out,
            unassigned=unassigned,
            branding_only=branding_only,
            funnel_all=funnel_all,
            reach_all=reach_all,
        )

    # ── Offer aggregation ─────────────────────────────────────────────────

    def _build_offer_metrics(
        self,
        *,
        offer: OfferReadDTO,
        expected: OfferExpectedMetric,
        rows: list[MetricRow],
        all_rows: list[MetricRow],
        campaign_ids: set[str],
        adset_ids: set[str],
        currency: str | None,
        period_reach_rows: list[PeriodMetricModel],
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

        primary_count = sum(
            r.value for r in rows if r.metric_name in primary_metric_names
        )

        ctr = (clicks / impressions * 100.0) if impressions else 0.0
        cpc = (total_spend / clicks) if clicks else 0.0
        cpm = (total_spend / impressions * 1000.0) if impressions else 0.0

        reach = self._compute_reach_for_campaigns(period_reach_rows, campaign_ids)
        frequency = self._compute_frequency(impressions, reach)

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
            if total_spend > 0 and primary_count > 0:
                roas = round(conversion_value / total_spend, 2)

        timeseries = self._build_timeseries(
            rows=rows, primary_metric_names=primary_metric_names
        )

        # Pass sets directly (never collapse to None) so a degenerate offer
        # with zero associations returns an all-zero funnel, NOT the global
        # aggregate. Sentinel `None` is reserved for funnel_all.
        funnel = self._build_funnel_for_campaigns(
            rows=all_rows,
            campaign_ids=campaign_ids,
            ad_set_ids=adset_ids,
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
            impressions=round(impressions, 2),
            clicks=round(clicks, 2),
            ctr=round(ctr, 2),
            cpm=round(cpm, 2),
            cpc=round(cpc, 2),
            reach=reach,
            frequency=frequency,
            funnel=funnel,
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

    # ── Unassigned / Branding aggregates ──────────────────────────────────

    def _aggregate_unassigned(
        self,
        *,
        rows: list[MetricRow],
        assigned_campaign_ids: set[str],
        assigned_adset_ids: set[str],
        branded_campaign_ids: set[str],
        period_reach_rows: list[PeriodMetricModel],
    ) -> UnassignedAggregateDTO:
        unassigned_targets: set[str] = set()
        unassigned_campaign_ids: set[str] = set()
        total_spend = 0.0
        impressions = 0.0
        clicks = 0.0
        funnel_row_filter: list[MetricRow] = []
        for r in rows:
            # Skip pure account-level rows (no campaign_id AND no ad_set_id).
            # Meta's Insights API emits ad-account-level aggregates that are
            # neither assignable nor branded — they would show as phantom
            # "unassigned spend" with zero actionable targets. Exclude them
            # so "Sin asignar" only reflects assignable campaigns/ad_sets.
            if not r.campaign_id and not r.ad_set_id:
                continue
            if r.campaign_id and r.campaign_id in branded_campaign_ids:
                continue
            if r.campaign_id and r.campaign_id in assigned_campaign_ids:
                continue
            if r.ad_set_id and r.ad_set_id in assigned_adset_ids:
                continue
            if r.campaign_id:
                unassigned_targets.add(f"campaign:{r.campaign_id}")
                unassigned_campaign_ids.add(r.campaign_id)
            if r.ad_set_id:
                unassigned_targets.add(f"ad_set:{r.ad_set_id}")
            funnel_row_filter.append(r)
            if r.metric_name == "spend":
                total_spend += r.value
            elif r.metric_name == "impressions":
                impressions += r.value
            elif r.metric_name == "clicks":
                clicks += r.value

        ctr = (clicks / impressions * 100.0) if impressions else 0.0
        cpc = (total_spend / clicks) if clicks else 0.0
        cpm = (total_spend / impressions * 1000.0) if impressions else 0.0

        reach = self._compute_reach_for_campaigns(
            period_reach_rows, unassigned_campaign_ids
        )

        funnel = self._build_funnel_from_rows(funnel_row_filter)

        return UnassignedAggregateDTO(
            target_count=len(unassigned_targets),
            total_spend=round(total_spend, 2),
            impressions=round(impressions, 2),
            clicks=round(clicks, 2),
            ctr=round(ctr, 2),
            cpm=round(cpm, 2),
            cpc=round(cpc, 2),
            reach=reach,
            funnel=funnel,
        )

    def _aggregate_branding(
        self,
        *,
        rows: list[MetricRow],
        branded_campaign_ids: set[str],
        period_reach_rows: list[PeriodMetricModel],
    ) -> BrandingAggregateDTO:
        total_spend = 0.0
        impressions = 0.0
        clicks = 0.0
        seen: set[str] = set()
        funnel_row_filter: list[MetricRow] = []
        for r in rows:
            if r.campaign_id not in branded_campaign_ids:
                continue
            seen.add(r.campaign_id)
            funnel_row_filter.append(r)
            if r.metric_name == "spend":
                total_spend += r.value
            elif r.metric_name == "impressions":
                impressions += r.value
            elif r.metric_name == "clicks":
                clicks += r.value

        ctr = (clicks / impressions * 100.0) if impressions else 0.0
        cpc = (total_spend / clicks) if clicks else 0.0
        cpm = (total_spend / impressions * 1000.0) if impressions else 0.0

        reach = self._compute_reach_for_campaigns(period_reach_rows, seen)
        frequency = self._compute_frequency(impressions, reach)

        funnel = self._build_funnel_from_rows(funnel_row_filter)

        return BrandingAggregateDTO(
            target_count=len(seen),
            total_spend=round(total_spend, 2),
            impressions=round(impressions, 2),
            clicks=round(clicks, 2),
            ctr=round(ctr, 2),
            cpm=round(cpm, 2),
            cpc=round(cpc, 2),
            reach=reach,
            frequency=frequency,
            funnel=funnel,
        )

    # ── Funnel helpers ────────────────────────────────────────────────────

    def _build_funnel_for_campaigns(
        self,
        *,
        rows: list[MetricRow],
        campaign_ids: set[str] | None,
        ad_set_ids: set[str] | None = None,
    ) -> list[FunnelStepDTO]:
        """Build a 5-step Meta Ads funnel from rows.

        **Sentinel semantics (explicit, not overloaded):**
        - `campaign_ids=None` AND `ad_set_ids=None` → global funnel over ALL
          rows (used by `funnel_all`). Callers MUST pass None (not empty
          sets) to opt into this behaviour.
        - Either argument is a set (even empty) → filter mode. Rows pass if
          their `campaign_id` is in `campaign_ids` OR their `ad_set_id` is in
          `ad_set_ids`. An empty set on both arguments legitimately returns
          an all-zero funnel (no rows match) — useful for offers with no
          associations, so we never silently leak the global aggregate under
          an offer's label.

        Semantics (identical to
        `channel_dashboard_service._build_funnel`):
        - value = sum of each metric across matching rows
        - conversion_rate_from_previous = round(value/prev*100, 2)
        - None for the first step or when prev == 0
        """
        if campaign_ids is None and ad_set_ids is None:
            # Explicit global mode — used by funnel_all only.
            filtered = rows
        else:
            cids: set[str] = campaign_ids if campaign_ids is not None else set()
            asids: set[str] = ad_set_ids if ad_set_ids is not None else set()
            filtered = [
                r for r in rows if (r.campaign_id in cids or r.ad_set_id in asids)
            ]
        return self._build_funnel_from_rows(filtered)

    @staticmethod
    def _build_funnel_from_rows(rows: list[MetricRow]) -> list[FunnelStepDTO]:
        totals: dict[str, float] = {name: 0.0 for _, name in _FUNNEL_STEPS}
        for r in rows:
            if r.metric_name in totals:
                totals[r.metric_name] += r.value

        steps: list[FunnelStepDTO] = []
        prev_value: float | None = None
        for label, metric_name in _FUNNEL_STEPS:
            value = totals[metric_name]
            conv_rate: float | None
            if prev_value is not None and prev_value > 0:
                conv_rate = round((value / prev_value) * 100, 2)
            else:
                conv_rate = None
            steps.append(
                FunnelStepDTO(
                    label=label,
                    metric_name=metric_name,
                    value=round(value, 2),
                    conversion_rate_from_previous=conv_rate,
                )
            )
            prev_value = value
        return steps

    # ── Reach helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _compute_reach_for_campaigns(
        period_reach_rows: list[PeriodMetricModel],
        campaign_ids: set[str],
    ) -> float | None:
        """Return a reliable reach value for the given campaigns.

        Rules (non-negotiable — see CONTRACT §1b):
          - len(campaign_ids) == 0 → None
          - len(campaign_ids) == 1 → value from the matching period_metrics
            row, or None if no row exists for that campaign_id
          - len(campaign_ids) >= 2 → None (audience overlap makes sum invalid)

        **Signature deviation from CONTRACT §4:** the CONTRACT originally
        defined this as `(self, tenant_id, start_date, end_date, campaign_ids)`
        with a DB roundtrip inside. The implementation receives pre-loaded
        rows instead so the service loads period_metrics once in `run()` and
        partitions in-memory for both `reach_all` and per-offer/per-bucket
        reach. This is intentional — fewer DB roundtrips, same guarantees,
        easier to test (no DB mock needed). See CONTRACT §5a "single
        roundtrip" goal and REVIEW.md M1.

        **Ad-set associations:** offers associated only via `ad_set` (no
        campaign association) get `campaign_ids = set()` → reach = None.
        Pre-existing limitation — the ETL today only emits campaign-level
        reach rows, so even if ad-set ids were threaded through here there
        would be no rows to look up. Documented in REVIEW.md M4.
        """
        if not campaign_ids:
            return None
        if len(campaign_ids) > 1:
            return None

        target_id = next(iter(campaign_ids))
        matching = [r for r in period_reach_rows if r.campaign_id == target_id]
        if not matching:
            return None
        # Take the most recent period_start row (already ordered desc
        # by the repository, but be defensive).
        best = max(matching, key=lambda r: r.period_start)
        try:
            return float(best.value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _compute_reach_all(
        period_reach_rows: list[PeriodMetricModel],
    ) -> float | None:
        """Channel-level reach (campaign_id IS NULL), or None if absent.

        Takes pre-loaded rows to share the single DB roundtrip with
        `_compute_reach_for_campaigns`. See the docstring of that method for
        rationale and the CONTRACT §4 deviation note.
        """
        channel_rows = [r for r in period_reach_rows if r.campaign_id is None]
        if not channel_rows:
            return None
        best = max(channel_rows, key=lambda r: r.period_start)
        try:
            return float(best.value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _compute_frequency(impressions: float, reach: float | None) -> float | None:
        """Frequency = impressions / reach, null when reach is null or zero.

        Kept in the service (not a DTO field derivation) because reach
        null-ness is the authoritative signal. If reach is unreliable,
        frequency is unreliable too.
        """
        if reach is None or reach <= 0:
            return None
        return round(impressions / reach, 2)


__all__ = ["MetricsByOfferService"]
