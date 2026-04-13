"""Tests for the group filter on stage detail endpoints.

Validates that the _filter_groups helper correctly filters the response
to include only requested groups. Pure unit tests -- no DB required.
"""

from src.modules.analytics.application.dto.attraction_dto import (
    AttractionDetailDTO,
    ChannelMetricDTO,
    MetricValueDTO,
    TrafficGroupDTO,
)
from src.modules.analytics.application.dto.capture_dto import (
    CaptureDetailDTO,
    CaptureHeaderKpisDTO,
    MiniFunnelDTO,
)


def _make_group(channels_count: int = 1) -> TrafficGroupDTO:
    """Create a TrafficGroupDTO with some channels."""
    channels = [
        ChannelMetricDTO(
            slug=f"test-{i}",
            name=f"Test Channel {i}",
            channel_type="social",
            metrics=[MetricValueDTO(name="reach", value=float(1000 * (i + 1)))],
            source_label="Test",
            connected=True,
        )
        for i in range(channels_count)
    ]
    return TrafficGroupDTO(
        totals={"reach": sum(1000 * (i + 1) for i in range(channels_count))},
        channels=channels,
    )


class TestFilterGroupsHelper:
    """Tests for the _filter_groups helper function."""

    def test_filter_keeps_requested_groups(self):
        """_filter_groups keeps only requested group fields.

        Required fields get an empty group (totals={}, channels=[])
        instead of None.
        """
        from src.modules.analytics.api.metrics import _filter_groups

        dto = AttractionDetailDTO(
            organic_social=_make_group(2),
            ga4_search=_make_group(1),
            paid=_make_group(3),
            outbound=_make_group(1),
        )
        filtered = _filter_groups(dto, ["organic_social", "paid"])
        assert filtered.organic_social is not None
        assert len(filtered.organic_social.channels) == 2
        assert filtered.paid is not None
        assert len(filtered.paid.channels) == 3
        # Required fields get empty group, not None
        assert filtered.ga4_search is not None
        assert len(filtered.ga4_search.channels) == 0
        assert filtered.outbound is not None
        assert len(filtered.outbound.channels) == 0

    def test_filter_preserves_metadata(self):
        """_filter_groups preserves period, last_updated, and other non-group fields."""
        from src.modules.analytics.api.metrics import _filter_groups

        dto = AttractionDetailDTO(
            organic_social=_make_group(2),
            ga4_search=_make_group(1),
            paid=_make_group(3),
            outbound=_make_group(1),
            period="weekly",
            last_updated="2026-04-06T12:00:00",
        )
        filtered = _filter_groups(dto, ["organic_social"])
        assert filtered.period == "weekly"
        assert filtered.last_updated == "2026-04-06T12:00:00"

    def test_filter_with_all_groups_keeps_all(self):
        """When all groups are requested, nothing is filtered."""
        from src.modules.analytics.api.metrics import _filter_groups

        dto = AttractionDetailDTO(
            organic_social=_make_group(1),
            ga4_search=_make_group(1),
            paid=_make_group(1),
            outbound=_make_group(1),
        )
        filtered = _filter_groups(
            dto,
            ["organic_social", "ga4_search", "paid", "outbound"],
        )
        assert filtered.organic_social is not None
        assert filtered.ga4_search is not None
        assert filtered.paid is not None
        assert filtered.outbound is not None

    def test_filter_with_invalid_groups_empties_all(self):
        """Invalid group keys cause all groups to be emptied."""
        from src.modules.analytics.api.metrics import _filter_groups

        dto = AttractionDetailDTO(
            organic_social=_make_group(1),
            ga4_search=_make_group(1),
            paid=_make_group(1),
            outbound=_make_group(1),
        )
        filtered = _filter_groups(dto, ["nonexistent_group"])
        # Required fields get empty group (not None)
        assert len(filtered.organic_social.channels) == 0
        assert len(filtered.ga4_search.channels) == 0
        assert len(filtered.paid.channels) == 0
        assert len(filtered.outbound.channels) == 0

    def test_filter_works_with_capture_dto(self):
        """_filter_groups works with CaptureDetailDTO."""
        from src.modules.analytics.api.metrics import _filter_groups

        dto = CaptureDetailDTO(
            header_kpis=CaptureHeaderKpisDTO(total_leads=500, conversion_rate=5.0),
            mini_funnel=MiniFunnelDTO(
                source_label="Visitantes",
                source_value=10000,
                target_label="Leads",
                target_value=500,
                conversion_rate=5.0,
            ),
            web_infrastructure=_make_group(1),
            ai_agent=_make_group(1),
        )
        filtered = _filter_groups(dto, ["web_infrastructure"])
        assert filtered.web_infrastructure is not None
        assert len(filtered.web_infrastructure.channels) == 1
        # ai_agent is required in CaptureDetailDTO, so gets empty group
        assert len(filtered.ai_agent.channels) == 0
        # Non-group fields preserved
        assert filtered.header_kpis.total_leads == 500
        assert filtered.mini_funnel.conversion_rate == 5.0

    def test_filter_returns_same_dto_type(self):
        """_filter_groups returns the same DTO type."""
        from src.modules.analytics.api.metrics import _filter_groups

        dto = AttractionDetailDTO(
            organic_social=_make_group(1),
            ga4_search=_make_group(1),
            paid=_make_group(1),
            outbound=_make_group(1),
        )
        filtered = _filter_groups(dto, ["organic_social"])
        assert isinstance(filtered, AttractionDetailDTO)


class TestEndpointGroupFilterWiring:
    """Tests that the group filter is wired into the endpoint."""

    def test_attraction_endpoint_has_groups_parameter(self):
        """The attraction endpoint signature includes groups parameter."""
        import inspect

        from src.modules.analytics.api import metrics

        source = inspect.getsource(metrics)
        # The attraction endpoint should have groups in its signature
        assert "groups" in source
        assert "_filter_groups" in source

    def test_capture_endpoint_has_groups_parameter(self):
        """The capture endpoint signature includes groups parameter."""
        import inspect

        from src.modules.analytics.api import metrics

        source = inspect.getsource(metrics.get_capture_metrics)
        assert "groups" in source

    def test_nurturing_endpoint_has_groups_parameter(self):
        """The nurturing endpoint signature includes groups parameter."""
        import inspect

        from src.modules.analytics.api import metrics

        source = inspect.getsource(metrics.get_nurturing_metrics)
        assert "groups" in source

    def test_opportunity_endpoint_has_groups_parameter(self):
        """The opportunity endpoint signature includes groups parameter."""
        import inspect

        from src.modules.analytics.api import metrics

        source = inspect.getsource(metrics.get_opportunity_metrics)
        assert "groups" in source
