"""Tests for metrics_by_offer DTOs.

Validates that the new DTO shape from
`docs/superpowers/artifacts/2026-04-10-meta-ads-resumen/CONTRACT.md` holds:

- `FunnelStepDTO` accepts `conversion_rate_from_previous=None`
- `OfferMetricsDTO` no longer has a `secondary_metrics` field
- Typed secondary metric fields (impressions/clicks/ctr/cpm/cpc) exist
- reach / frequency default to None
- Root DTO exposes `funnel_all` + `reach_all`
"""

from __future__ import annotations

from uuid import uuid4

from src.modules.advertising.application.dto.metrics_by_offer_dto import (
    BrandingAggregateDTO,
    FunnelStepDTO,
    MetricsByOfferDTO,
    OfferMetricsDTO,
    UnassignedAggregateDTO,
)


class TestFunnelStepDTO:
    def test_accepts_null_conversion_rate(self) -> None:
        step = FunnelStepDTO(
            label="Impresiones",
            metric_name="impressions",
            value=1000.0,
            conversion_rate_from_previous=None,
        )
        assert step.conversion_rate_from_previous is None

    def test_accepts_numeric_conversion_rate(self) -> None:
        step = FunnelStepDTO(
            label="Clics",
            metric_name="clicks",
            value=100.0,
            conversion_rate_from_previous=10.0,
        )
        assert step.conversion_rate_from_previous == 10.0

    def test_camel_serialisation(self) -> None:
        step = FunnelStepDTO(
            label="Clics",
            metric_name="clicks",
            value=100.0,
            conversion_rate_from_previous=10.0,
        )
        data = step.model_dump(by_alias=True)
        assert "metricName" in data
        assert "conversionRateFromPrevious" in data
        assert data["conversionRateFromPrevious"] == 10.0


class TestOfferMetricsDTO:
    def test_secondary_metrics_field_removed(self) -> None:
        assert "secondary_metrics" not in OfferMetricsDTO.model_fields

    def test_has_typed_secondary_metric_fields(self) -> None:
        required = {"impressions", "clicks", "ctr", "cpm", "cpc", "reach", "frequency"}
        assert required.issubset(OfferMetricsDTO.model_fields.keys())

    def test_has_funnel_field(self) -> None:
        assert "funnel" in OfferMetricsDTO.model_fields

    def test_reach_and_frequency_default_to_none(self) -> None:
        dto = OfferMetricsDTO(
            offer_id=uuid4(),
            offer_name="Curso",
            archetype="PROGRAMA",
            expected_metric="purchase",
            expected_metric_label_es="Compra",
            total_spend=100.0,
            currency="USD",
            primary_result_count=5.0,
            primary_metric_name="Costo por Compra",
            primary_metric_unit="currency",
            impressions=1000.0,
            clicks=100.0,
            ctr=10.0,
            cpm=100.0,
            cpc=1.0,
            funnel=[],
            timeseries=[],
        )
        assert dto.reach is None
        assert dto.frequency is None
        assert dto.roas is None
        assert dto.primary_cost_per_result is None
        assert dto.metric_unavailable_reason is None


class TestAggregateDTOs:
    def test_branding_has_new_fields(self) -> None:
        required = {"ctr", "cpm", "cpc", "reach", "frequency", "funnel"}
        assert required.issubset(BrandingAggregateDTO.model_fields.keys())

    def test_unassigned_has_new_fields(self) -> None:
        required = {"ctr", "cpm", "cpc", "reach", "funnel"}
        assert required.issubset(UnassignedAggregateDTO.model_fields.keys())

    def test_unassigned_has_no_frequency(self) -> None:
        # Unassigned doesn't need frequency per CONTRACT §2.
        assert "frequency" not in UnassignedAggregateDTO.model_fields


class TestMetricsByOfferDTO:
    def test_has_funnel_all_and_reach_all(self) -> None:
        assert "funnel_all" in MetricsByOfferDTO.model_fields
        assert "reach_all" in MetricsByOfferDTO.model_fields

    def test_reach_all_defaults_to_none(self) -> None:
        dto = MetricsByOfferDTO(
            period="30d",
            start_date="2026-03-11",
            end_date="2026-04-09",
            currency="USD",
            offers=[],
            unassigned=UnassignedAggregateDTO(
                target_count=0,
                total_spend=0.0,
                impressions=0.0,
                clicks=0.0,
                ctr=0.0,
                cpm=0.0,
                cpc=0.0,
                reach=None,
                funnel=[],
            ),
            branding_only=BrandingAggregateDTO(
                target_count=0,
                total_spend=0.0,
                impressions=0.0,
                clicks=0.0,
                ctr=0.0,
                cpm=0.0,
                cpc=0.0,
                reach=None,
                frequency=None,
                funnel=[],
            ),
            funnel_all=[],
        )
        assert dto.reach_all is None
