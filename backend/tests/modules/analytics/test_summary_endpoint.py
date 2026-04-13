"""Tests for summary and attraction DTO shapes.

Validates that DTO Pydantic models have all expected fields and
can be instantiated with valid data. Pure Python — no DB, no async.
"""

from src.modules.analytics.application.dto.attraction_dto import (
    AttractionDetailDTO,
    AvailableChannelsDTO,
    ChannelMetricDTO,
    MetricValueDTO,
    SubSourceDTO,
    TrafficGroupDTO,
)
from src.modules.analytics.application.dto.summary_dto import (
    BowtiesSummaryDTO,
    StageSummaryKpiDTO,
)


class TestStageSummaryKpiDTO:
    """StageSummaryKpiDTO carries stage-level KPI data."""

    def test_required_fields(self):
        """DTO can be instantiated with all required fields."""
        dto = StageSummaryKpiDTO(
            stage="attraction",
            main_kpi=15000.0,
            main_label="Alcance",
            secondary_kpi=3000.0,
            secondary_label="Clics",
        )
        assert dto.stage == "attraction"
        assert dto.main_kpi == 15000.0
        assert dto.main_label == "Alcance"
        assert dto.secondary_kpi == 3000.0
        assert dto.secondary_label == "Clics"

    def test_optional_unit_fields(self):
        """main_unit and secondary_unit are optional and default to None."""
        dto = StageSummaryKpiDTO(
            stage="sales",
            main_kpi=50000.0,
            main_label="Ingresos",
            main_unit="currency",
            secondary_kpi=120.0,
            secondary_label="Ordenes",
        )
        assert dto.main_unit == "currency"
        assert dto.secondary_unit is None

    def test_all_fields_present(self):
        """DTO should have stage, main_kpi, main_label, main_unit, secondary_kpi, secondary_label, secondary_unit."""
        fields = set(StageSummaryKpiDTO.model_fields.keys())
        expected = {
            "stage",
            "main_kpi",
            "main_label",
            "main_unit",
            "secondary_kpi",
            "secondary_label",
            "secondary_unit",
        }
        assert fields == expected, f"Missing fields: {expected - fields}; extra: {fields - expected}"


class TestBowtiesSummaryDTO:
    """BowtiesSummaryDTO wraps stage KPIs for the funnel overview."""

    def test_stages_is_list(self):
        """stages field should accept a list of StageSummaryKpiDTO."""
        stages = [
            StageSummaryKpiDTO(
                stage=s,
                main_kpi=100.0,
                main_label="KPI",
                secondary_kpi=50.0,
                secondary_label="KPI2",
            )
            for s in [
                "attraction",
                "capture",
                "nurture",
                "opportunity",
                "sales",
                "adoption",
                "expansion",
                "evangelization",
            ]
        ]
        dto = BowtiesSummaryDTO(stages=stages, period="last_30_days")
        assert len(dto.stages) == 8
        assert dto.period == "last_30_days"

    def test_last_updated_optional(self):
        """last_updated is optional and defaults to None."""
        dto = BowtiesSummaryDTO(stages=[], period="daily")
        assert dto.last_updated is None

    def test_all_fields_present(self):
        """DTO should have stages, period, and last_updated."""
        fields = set(BowtiesSummaryDTO.model_fields.keys())
        expected = {"stages", "period", "last_updated"}
        assert fields == expected


class TestMetricValueDTO:
    """MetricValueDTO carries a single named metric value."""

    def test_basic_instantiation(self):
        """Can create with name and value only."""
        dto = MetricValueDTO(name="reach", value=5000.0)
        assert dto.name == "reach"
        assert dto.value == 5000.0
        assert dto.unit == "count"  # default

    def test_with_currency(self):
        """Can specify unit and currency."""
        dto = MetricValueDTO(
            name="spend",
            value=123.45,
            unit="currency",
            currency="USD",
        )
        assert dto.unit == "currency"
        assert dto.currency == "USD"

    def test_with_breakdown(self):
        """Can include a breakdown dict."""
        dto = MetricValueDTO(
            name="engagement",
            value=1200.0,
            breakdown={"likes": 800, "comments": 400},
        )
        assert dto.breakdown is not None
        assert dto.breakdown["likes"] == 800


class TestChannelMetricDTO:
    """ChannelMetricDTO carries multi-metric data for a single channel."""

    def test_required_fields(self):
        """Can instantiate with all required fields."""
        dto = ChannelMetricDTO(
            slug="ig-organic",
            name="Instagram Organic",
            channel_type="social",
            metrics=[MetricValueDTO(name="reach", value=5000.0)],
            source_label="Instagram",
            connected=True,
        )
        assert dto.slug == "ig-organic"
        assert dto.connected is True
        assert len(dto.metrics) == 1

    def test_backward_compat_value_property(self):
        """value computed field returns first metric's value."""
        dto = ChannelMetricDTO(
            slug="test",
            name="Test",
            channel_type="social",
            metrics=[
                MetricValueDTO(name="reach", value=5000.0),
                MetricValueDTO(name="engagement", value=1200.0),
            ],
            source_label="Test",
            connected=True,
        )
        assert dto.value == 5000.0

    def test_value_property_empty_metrics(self):
        """value returns 0.0 when metrics list is empty."""
        dto = ChannelMetricDTO(
            slug="test",
            name="Test",
            channel_type="social",
            metrics=[],
            source_label="Test",
            connected=False,
        )
        assert dto.value == 0.0

    def test_optional_fields_default_none(self):
        """Optional fields default to None or False."""
        dto = ChannelMetricDTO(
            slug="test",
            name="Test",
            channel_type="social",
            metrics=[],
            source_label="Test",
            connected=True,
        )
        assert dto.cost_type is None
        assert dto.last_updated is None
        assert dto.stale is False
        assert dto.error_message is None
        assert dto.source_display_name is None
        assert dto.provider_name is None
        assert dto.sub_sources is None


class TestSubSourceDTO:
    """SubSourceDTO for multi-source channel breakdowns."""

    def test_basic_instantiation(self):
        dto = SubSourceDTO(name="Meta Direct", leads=50)
        assert dto.name == "Meta Direct"
        assert dto.leads == 50
        assert dto.conversations == 0  # default


class TestTrafficGroupDTO:
    """TrafficGroupDTO wraps a group of channels with totals."""

    def test_structure(self):
        """Can create with totals dict and channel list."""
        dto = TrafficGroupDTO(
            totals={"reach": 10000, "clicks": 500},
            channels=[
                ChannelMetricDTO(
                    slug="ig-organic",
                    name="IG",
                    channel_type="social",
                    metrics=[MetricValueDTO(name="reach", value=10000.0)],
                    source_label="Instagram",
                    connected=True,
                ),
            ],
        )
        assert dto.totals["reach"] == 10000
        assert len(dto.channels) == 1


class TestAttractionDetailDTO:
    """AttractionDetailDTO has all channel groups."""

    def _make_group(self):
        return TrafficGroupDTO(totals={}, channels=[])

    def test_required_groups(self):
        """AttractionDetailDTO requires organic_social, ga4_search, paid, outbound."""
        dto = AttractionDetailDTO(
            organic_social=self._make_group(),
            ga4_search=self._make_group(),
            paid=self._make_group(),
            outbound=self._make_group(),
        )
        assert dto.organic_social is not None
        assert dto.ga4_search is not None
        assert dto.paid is not None
        assert dto.outbound is not None

    def test_optional_groups_default_none(self):
        """available group is optional."""
        dto = AttractionDetailDTO(
            organic_social=self._make_group(),
            ga4_search=self._make_group(),
            paid=self._make_group(),
            outbound=self._make_group(),
        )
        assert dto.available is None

    def test_period_default(self):
        """Default period is last_30_days."""
        dto = AttractionDetailDTO(
            organic_social=self._make_group(),
            ga4_search=self._make_group(),
            paid=self._make_group(),
            outbound=self._make_group(),
        )
        assert dto.period == "last_30_days"

    def test_all_channel_group_fields(self):
        """AttractionDetailDTO should have organic_social, ga4_search, paid, outbound."""
        fields = set(AttractionDetailDTO.model_fields.keys())
        expected_groups = {
            "organic_social",
            "ga4_search",
            "paid",
            "outbound",
        }
        assert expected_groups.issubset(fields), f"Missing channel group fields: {expected_groups - fields}"

    def test_has_available_field(self):
        """AttractionDetailDTO should have an 'available' field for unconnected channels."""
        assert "available" in AttractionDetailDTO.model_fields


class TestAvailableChannelsDTO:
    """AvailableChannelsDTO wraps channels not yet connected."""

    def test_structure(self):
        dto = AvailableChannelsDTO(
            channels=[
                ChannelMetricDTO(
                    slug="tiktok-organic",
                    name="TikTok Organic",
                    channel_type="social",
                    metrics=[],
                    source_label="TikTok",
                    connected=False,
                ),
            ],
        )
        assert len(dto.channels) == 1
        assert dto.channels[0].connected is False
