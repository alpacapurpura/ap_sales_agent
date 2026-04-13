"""DTOs for metrics grouped by offer.

Exact shape defined in
`docs/superpowers/artifacts/2026-04-10-meta-ads-resumen/CONTRACT.md` §2.
"""

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict


def _to_camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


class _CamelModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=_to_camel,
    )


# ── Shared ────────────────────────────────────────────────────────────────


class FunnelStepDTO(_CamelModel):
    """One step of the Meta Ads conversion funnel.

    Mirrors the shape of `analytics.AdFunnelDTO.steps[i]` but lives in
    advertising to respect DDD boundaries. `conversion_rate_from_previous`
    is a percentage (0-100), or null for the first step / when previous=0.
    """

    label: str
    metric_name: str
    value: float
    conversion_rate_from_previous: float | None = None


# ── Per-offer ──────────────────────────────────────────────────────────────


class OfferTimeSeriesPointDTO(_CamelModel):
    """Data transfer object for offer time series point."""

    date: str
    spend: float
    primary_result: float


class OfferMetricsDTO(_CamelModel):
    """Data transfer object for offer metrics."""

    offer_id: UUID
    offer_name: str
    archetype: str
    expected_metric: str
    expected_metric_label_es: str
    total_spend: float
    currency: str
    primary_result_count: float
    primary_cost_per_result: float | None = None
    primary_metric_name: str
    primary_metric_unit: str  # "currency" | "count"
    roas: float | None = None

    # Secondary metrics — flattened out of the old dict so each field is
    # individually typed and nullable when semantically unreliable.
    impressions: float
    clicks: float
    ctr: float  # percentage 0-100
    cpm: float  # in `currency`
    cpc: float  # in `currency`
    # null unless unambiguous (1 campaign + period_metrics row present)
    reach: float | None = None
    # null unless reach is not null
    frequency: float | None = None

    # Funnel filtered to the offer's associated campaigns.
    funnel: list[FunnelStepDTO]

    timeseries: list[OfferTimeSeriesPointDTO]
    metric_unavailable_reason: str | None = None


# ── Branding aggregate ────────────────────────────────────────────────────


class BrandingAggregateDTO(_CamelModel):
    """Data transfer object for branding aggregate."""

    target_count: int
    total_spend: float
    impressions: float
    clicks: float
    ctr: float
    cpm: float
    cpc: float
    reach: float | None = None  # null in multi-campaign case
    frequency: float | None = None  # null when reach is null
    funnel: list[FunnelStepDTO]


# ── Unassigned aggregate ──────────────────────────────────────────────────


class UnassignedAggregateDTO(_CamelModel):
    """Data transfer object for unassigned aggregate."""

    target_count: int
    total_spend: float
    impressions: float
    clicks: float
    ctr: float
    cpm: float
    cpc: float
    reach: float | None = None  # null when multi-campaign
    funnel: list[FunnelStepDTO]


# ── Root response ─────────────────────────────────────────────────────────


class MetricsByOfferDTO(_CamelModel):
    """Data transfer object for metrics by offer."""

    period: str
    start_date: date
    end_date: date
    currency: str | None = None
    offers: list[OfferMetricsDTO]
    unassigned: UnassignedAggregateDTO
    branding_only: BrandingAggregateDTO

    # "Todas" context — used when the segmenter selection is `all`.
    funnel_all: list[FunnelStepDTO]
    reach_all: float | None = None
