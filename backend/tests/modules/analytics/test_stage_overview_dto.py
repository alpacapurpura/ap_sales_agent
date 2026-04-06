"""Tests for StageOverviewDTO and related DTOs.

Validates DTO shapes, serialization, and required fields.
Pure Python -- no DB, no async.
"""

from src.modules.analytics.application.dto.stage_overview_dto import (
    BottleneckOverviewDTO,
    ChannelOverviewDTO,
    GroupOverviewDTO,
    MetricValueDTO,
    MiniFunnelOverviewDTO,
    StageOverviewDTO,
)


class TestMetricValueDTO:
    """MetricValueDTO carries a single named KPI value."""

    def test_basic_instantiation(self):
        dto = MetricValueDTO(name="reach", value=5000.0)
        assert dto.name == "reach"
        assert dto.value == 5000.0
        assert dto.unit is None

    def test_with_unit(self):
        dto = MetricValueDTO(name="spend", value=123.45, unit="currency")
        assert dto.unit == "currency"


class TestChannelOverviewDTO:
    """ChannelOverviewDTO carries lightweight channel info + 1 headline KPI."""

    def test_serialization(self):
        dto = ChannelOverviewDTO(
            slug="ig-organic",
            name="Instagram Organic",
            channel_type="social",
            group_key="organic_social",
            connected=True,
            headline_kpi=MetricValueDTO(name="reach", value=5000.0),
            last_updated="2026-04-06T12:00:00",
            stale=False,
            provider_name="meta",
        )
        data = dto.model_dump()
        assert data["slug"] == "ig-organic"
        assert data["connected"] is True
        assert data["headline_kpi"]["name"] == "reach"
        assert data["headline_kpi"]["value"] == 5000.0
        assert data["provider_name"] == "meta"

    def test_minimal_instantiation(self):
        dto = ChannelOverviewDTO(
            slug="cold-contact",
            name="Cold Contact",
            channel_type="outbound",
            group_key="outbound",
            connected=False,
        )
        assert dto.headline_kpi is None
        assert dto.last_updated is None
        assert dto.stale is False
        assert dto.provider_name is None


class TestGroupOverviewDTO:
    """GroupOverviewDTO summarizes a channel group."""

    def test_serialization(self):
        dto = GroupOverviewDTO(
            group_key="organic_social",
            group_label="Social Orgánico",
            channel_count=3,
        )
        data = dto.model_dump()
        assert data["group_key"] == "organic_social"
        assert data["group_label"] == "Social Orgánico"
        assert data["channel_count"] == 3


class TestMiniFunnelOverviewDTO:
    """MiniFunnelOverviewDTO carries the stage transition metric."""

    def test_serialization(self):
        dto = MiniFunnelOverviewDTO(
            source_label="Visitantes",
            source_value=10000.0,
            target_label="Leads",
            target_value=500.0,
            conversion_rate=5.0,
        )
        data = dto.model_dump()
        assert data["source_label"] == "Visitantes"
        assert data["conversion_rate"] == 5.0


class TestBottleneckOverviewDTO:
    """BottleneckOverviewDTO carries a simplified bottleneck alert."""

    def test_serialization(self):
        dto = BottleneckOverviewDTO(
            type="abandoned_cart",
            metric_label="Tasa de Abandono",
            severity="warning",
        )
        data = dto.model_dump()
        assert data["type"] == "abandoned_cart"
        assert data["severity"] == "warning"


class TestStageOverviewDTO:
    """StageOverviewDTO is the top-level overview response."""

    def test_includes_required_fields(self):
        """All expected fields are present."""
        fields = set(StageOverviewDTO.model_fields.keys())
        expected = {
            "stage",
            "header_kpis",
            "mini_funnel",
            "groups",
            "channel_list",
            "bottlenecks",
            "period",
            "last_updated",
        }
        assert expected == fields, (
            f"Missing: {expected - fields}; Extra: {fields - expected}"
        )

    def test_full_instantiation(self):
        """Can create with all fields populated."""
        dto = StageOverviewDTO(
            stage="attraction",
            header_kpis={"total_visitors": 15000.0, "total_channels": 5.0},
            mini_funnel=None,
            groups=[
                GroupOverviewDTO(
                    group_key="organic_social",
                    group_label="Social Orgánico",
                    channel_count=3,
                ),
            ],
            channel_list=[
                ChannelOverviewDTO(
                    slug="ig-organic",
                    name="Instagram Organic",
                    channel_type="social",
                    group_key="organic_social",
                    connected=True,
                    headline_kpi=MetricValueDTO(name="reach", value=5000.0),
                ),
            ],
            bottlenecks=[],
            period="last_30_days",
            last_updated="2026-04-06T12:00:00",
        )
        assert dto.stage == "attraction"
        assert len(dto.groups) == 1
        assert len(dto.channel_list) == 1
        assert dto.period == "last_30_days"

    def test_defaults(self):
        """Defaults for period and last_updated."""
        dto = StageOverviewDTO(
            stage="capture",
            header_kpis={},
            groups=[],
            channel_list=[],
            bottlenecks=[],
        )
        assert dto.period == "last_30_days"
        assert dto.last_updated is None
        assert dto.mini_funnel is None

    def test_with_mini_funnel(self):
        """Can include a mini funnel."""
        dto = StageOverviewDTO(
            stage="capture",
            header_kpis={"total_leads": 500.0},
            mini_funnel=MiniFunnelOverviewDTO(
                source_label="Visitantes",
                source_value=10000.0,
                target_label="Leads",
                target_value=500.0,
                conversion_rate=5.0,
            ),
            groups=[],
            channel_list=[],
            bottlenecks=[],
        )
        assert dto.mini_funnel is not None
        assert dto.mini_funnel.conversion_rate == 5.0

    def test_with_bottlenecks(self):
        """Can include bottleneck alerts."""
        dto = StageOverviewDTO(
            stage="opportunity",
            header_kpis={},
            groups=[],
            channel_list=[],
            bottlenecks=[
                BottleneckOverviewDTO(
                    type="abandoned_cart",
                    metric_label="Tasa de Abandono",
                    severity="critical",
                ),
            ],
        )
        assert len(dto.bottlenecks) == 1
        assert dto.bottlenecks[0].severity == "critical"
