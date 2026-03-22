"""Tests for multi-metric DTO contracts.

Validates:
- MetricValueDTO serialization with breakdown dict
- ChannelMetricDTO.value property backward compat
- AttractionDetailDTO structure with all 4 groups
"""

import pytest

from src.modules.analytics.application.dto.attraction_dto import (
    AttractionDetailDTO,
    AvailableChannelsDTO,
    ChannelMetricDTO,
    MetricValueDTO,
    TrafficGroupDTO,
)


class TestMetricValueDTO:
    """MetricValueDTO carries a single named metric."""

    def test_basic_serialization(self):
        mv = MetricValueDTO(name="reach", value=5000.0)
        data = mv.model_dump()
        assert data["name"] == "reach"
        assert data["value"] == 5000.0
        assert data["unit"] == "count"
        assert data["currency"] is None
        assert data["breakdown"] is None

    def test_with_currency(self):
        mv = MetricValueDTO(
            name="spend", value=123.45, unit="currency", currency="USD"
        )
        assert mv.unit == "currency"
        assert mv.currency == "USD"
        assert mv.value == 123.45

    def test_with_breakdown(self):
        breakdown = {"likes": 120, "comments": 45, "shares": 30, "saves": 10}
        mv = MetricValueDTO(
            name="engagement", value=205.0, breakdown=breakdown
        )
        assert mv.breakdown == breakdown
        assert mv.value == 205.0

    def test_serialization_roundtrip(self):
        breakdown = {"likes": 10, "comments": 5}
        mv = MetricValueDTO(
            name="engagement",
            value=15.0,
            unit="count",
            breakdown=breakdown,
        )
        data = mv.model_dump()
        restored = MetricValueDTO(**data)
        assert restored == mv


class TestChannelMetricDTO:
    """ChannelMetricDTO carries multiple MetricValueDTO objects."""

    def test_value_property_returns_first_metric(self):
        dto = ChannelMetricDTO(
            slug="ig-organic",
            name="Instagram Organic",
            channel_type="social",
            metrics=[
                MetricValueDTO(name="reach", value=5000.0),
                MetricValueDTO(name="engagement", value=1200.0),
            ],
            source_label="Instagram",
            connected=True,
        )
        assert dto.value == 5000.0

    def test_value_property_returns_zero_when_empty(self):
        dto = ChannelMetricDTO(
            slug="ig-organic",
            name="Instagram Organic",
            channel_type="social",
            metrics=[],
            source_label="Instagram",
            connected=True,
        )
        assert dto.value == 0.0

    def test_stale_and_error_fields(self):
        dto = ChannelMetricDTO(
            slug="meta-ads",
            name="Meta Ads",
            channel_type="paid",
            metrics=[MetricValueDTO(name="reach", value=100.0)],
            source_label="Meta Ads",
            connected=True,
            stale=True,
            error_message="Token expirado",
        )
        assert dto.stale is True
        assert dto.error_message == "Token expirado"

    def test_serialization_includes_value_in_metrics_list(self):
        dto = ChannelMetricDTO(
            slug="google-organic",
            name="Google Organic",
            channel_type="search",
            metrics=[
                MetricValueDTO(name="sessions", value=3000.0),
                MetricValueDTO(name="users", value=2500.0),
            ],
            source_label="Google Search",
            connected=True,
        )
        data = dto.model_dump()
        assert len(data["metrics"]) == 2
        assert data["metrics"][0]["name"] == "sessions"
        assert data["metrics"][1]["name"] == "users"

    def test_backward_compat_defaults(self):
        """Ensure backward-compat fields still have defaults."""
        dto = ChannelMetricDTO(
            slug="test",
            name="Test",
            channel_type="social",
            metrics=[],
            source_label="Test",
            connected=False,
        )
        assert dto.cost_type is None
        assert dto.last_updated is None
        assert dto.stale is False
        assert dto.error_message is None


class TestTrafficGroupDTO:
    """TrafficGroupDTO carries totals dict keyed by metric name."""

    def test_totals_dict(self):
        group = TrafficGroupDTO(
            totals={"reach": 5000.0, "engagement": 1200.0},
            channels=[],
        )
        assert group.totals["reach"] == 5000.0
        assert group.totals["engagement"] == 1200.0

    def test_empty_totals(self):
        group = TrafficGroupDTO(totals={}, channels=[])
        assert group.totals == {}


class TestAttractionDetailDTO:
    """AttractionDetailDTO has 4 groups: organic_social, ga4_search, paid, outbound."""

    def test_four_group_structure(self):
        empty_group = TrafficGroupDTO(totals={}, channels=[])
        dto = AttractionDetailDTO(
            organic_social=empty_group,
            ga4_search=empty_group,
            paid=empty_group,
            outbound=empty_group,
        )
        assert dto.organic_social is not None
        assert dto.ga4_search is not None
        assert dto.paid is not None
        assert dto.outbound is not None
        assert dto.period == "last_30_days"

    def test_with_available_channels(self):
        empty_group = TrafficGroupDTO(totals={}, channels=[])
        available = AvailableChannelsDTO(
            channels=[
                ChannelMetricDTO(
                    slug="linkedin-organic",
                    name="LinkedIn Organic",
                    channel_type="social",
                    metrics=[],
                    source_label="LinkedIn",
                    connected=False,
                )
            ]
        )
        dto = AttractionDetailDTO(
            organic_social=empty_group,
            ga4_search=empty_group,
            paid=empty_group,
            outbound=empty_group,
            available=available,
        )
        assert len(dto.available.channels) == 1
        assert dto.available.channels[0].slug == "linkedin-organic"

    def test_full_serialization(self):
        ig_channel = ChannelMetricDTO(
            slug="ig-organic",
            name="Instagram Organic",
            channel_type="social",
            metrics=[
                MetricValueDTO(name="reach", value=5000.0),
                MetricValueDTO(
                    name="engagement",
                    value=1200.0,
                    breakdown={"likes": 800, "comments": 400},
                ),
            ],
            source_label="Instagram",
            connected=True,
        )
        organic = TrafficGroupDTO(
            totals={"reach": 5000.0, "engagement": 1200.0},
            channels=[ig_channel],
        )
        dto = AttractionDetailDTO(
            organic_social=organic,
            ga4_search=TrafficGroupDTO(totals={}, channels=[]),
            paid=TrafficGroupDTO(totals={}, channels=[]),
            outbound=TrafficGroupDTO(totals={}, channels=[]),
            last_updated="2026-03-15T03:15:00Z",
        )
        data = dto.model_dump()
        assert data["organic_social"]["totals"]["reach"] == 5000.0
        assert len(data["organic_social"]["channels"]) == 1
        assert data["last_updated"] == "2026-03-15T03:15:00Z"
