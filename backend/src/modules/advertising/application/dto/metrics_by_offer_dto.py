"""DTOs for metrics grouped by offer."""

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


class OfferTimeSeriesPointDTO(_CamelModel):
    date: str
    spend: float
    primary_result: float


class OfferMetricsDTO(_CamelModel):
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
    secondary_metrics: dict[str, float]
    timeseries: list[OfferTimeSeriesPointDTO]
    metric_unavailable_reason: str | None = None


class UnassignedAggregateDTO(_CamelModel):
    target_count: int
    total_spend: float
    impressions: float
    clicks: float


class BrandingAggregateDTO(_CamelModel):
    target_count: int
    total_spend: float
    reach: float
    impressions: float


class MetricsByOfferDTO(_CamelModel):
    period: str
    start_date: date
    end_date: date
    currency: str | None = None
    offers: list[OfferMetricsDTO]
    unassigned: UnassignedAggregateDTO
    branding_only: BrandingAggregateDTO
