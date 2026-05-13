"""Tests for demographics breakdown service — parses audience breakdown from official_metrics."""

import json
from unittest.mock import MagicMock
from uuid import UUID

from luana_core_analytics_engine.application.dto.channel_dashboard_dto import (
    DemographicsDTO,
)
from luana_core_analytics_engine.application.services.channel_dashboard_service import (
    ChannelDashboardService,
)

TENANT_ID = UUID("11111111-1111-1111-1111-111111111111")


def _make_metric_row(metric_name: str, extra: dict) -> MagicMock:
    """Build a mock row matching official_metrics columns."""
    row = MagicMock()
    row._mapping = {
        "metric_name": metric_name,
        "extra": json.dumps(extra),
    }
    return row


class TestGetDemographics:
    """Tests for ChannelDashboardService.get_demographics()."""

    def test_parses_age_breakdowns(self):
        """Age breakdown from meta_reach_by_age is parsed correctly."""
        db = MagicMock()
        db.execute.return_value = MagicMock(
            fetchall=MagicMock(
                return_value=[
                    _make_metric_row(
                        "meta_reach_by_age",
                        {
                            "breakdowns": [
                                {"dimension_values": ["18-24"], "value": 3000},
                                {"dimension_values": ["25-34"], "value": 7000},
                            ],
                        },
                    ),
                ],
            ),
        )

        service = ChannelDashboardService(db)
        result = service.get_demographics(TENANT_ID, "meta-ads", "30d")

        assert isinstance(result, DemographicsDTO)
        assert len(result.age) == 2
        assert result.age[0].label == "18-24"
        assert result.age[0].value == 3000
        assert result.age[0].percentage == 30.0
        assert result.age[1].label == "25-34"
        assert result.age[1].value == 7000
        assert result.age[1].percentage == 70.0

    def test_parses_gender_breakdowns(self):
        """Gender breakdown from meta_reach_by_gender is parsed correctly."""
        db = MagicMock()
        db.execute.return_value = MagicMock(
            fetchall=MagicMock(
                return_value=[
                    _make_metric_row(
                        "meta_reach_by_gender",
                        {
                            "breakdowns": [
                                {"dimension_values": ["male"], "value": 4000},
                                {"dimension_values": ["female"], "value": 6000},
                            ],
                        },
                    ),
                ],
            ),
        )

        service = ChannelDashboardService(db)
        result = service.get_demographics(TENANT_ID, "meta-ads", "30d")

        assert len(result.gender) == 2
        assert result.gender[0].label == "male"
        assert result.gender[1].label == "female"
        assert result.gender[1].percentage == 60.0

    def test_parses_placement_breakdowns(self):
        """Placement breakdown from meta_reach_by_placement is parsed correctly."""
        db = MagicMock()
        db.execute.return_value = MagicMock(
            fetchall=MagicMock(
                return_value=[
                    _make_metric_row(
                        "meta_reach_by_placement",
                        {
                            "breakdowns": [
                                {"dimension_values": ["facebook_feed"], "value": 5000},
                                {
                                    "dimension_values": ["instagram_stories"],
                                    "value": 3000,
                                },
                                {
                                    "dimension_values": ["audience_network"],
                                    "value": 2000,
                                },
                            ],
                        },
                    ),
                ],
            ),
        )

        service = ChannelDashboardService(db)
        result = service.get_demographics(TENANT_ID, "meta-ads", "30d")

        assert len(result.placement) == 3
        assert result.placement[0].label == "facebook_feed"
        assert result.placement[0].value == 5000
        assert result.placement[0].percentage == 50.0

    def test_all_three_breakdown_types(self):
        """When all 3 breakdown metrics exist, all are populated."""
        db = MagicMock()
        db.execute.return_value = MagicMock(
            fetchall=MagicMock(
                return_value=[
                    _make_metric_row(
                        "meta_reach_by_age",
                        {
                            "breakdowns": [
                                {"dimension_values": ["25-34"], "value": 8000},
                                {"dimension_values": ["35-44"], "value": 2000},
                            ],
                        },
                    ),
                    _make_metric_row(
                        "meta_reach_by_gender",
                        {
                            "breakdowns": [
                                {"dimension_values": ["female"], "value": 6000},
                                {"dimension_values": ["male"], "value": 4000},
                            ],
                        },
                    ),
                    _make_metric_row(
                        "meta_reach_by_placement",
                        {
                            "breakdowns": [
                                {"dimension_values": ["facebook_feed"], "value": 10000},
                            ],
                        },
                    ),
                ],
            ),
        )

        service = ChannelDashboardService(db)
        result = service.get_demographics(TENANT_ID, "meta-ads", "30d")

        assert len(result.age) == 2
        assert len(result.gender) == 2
        assert len(result.placement) == 1
        # Single placement = 100%
        assert result.placement[0].percentage == 100.0

    def test_empty_data_returns_empty_lists(self):
        """When no breakdown metrics exist, return empty lists."""
        db = MagicMock()
        db.execute.return_value = MagicMock(fetchall=MagicMock(return_value=[]))

        service = ChannelDashboardService(db)
        result = service.get_demographics(TENANT_ID, "meta-ads", "30d")

        assert result.age == []
        assert result.gender == []
        assert result.placement == []

    def test_filters_by_tenant_id(self):
        """Verify the SQL uses tenant_id in the query."""
        db = MagicMock()
        db.execute.return_value = MagicMock(fetchall=MagicMock(return_value=[]))

        service = ChannelDashboardService(db)
        service.get_demographics(TENANT_ID, "meta-ads", "30d")

        # Verify execute was called
        db.execute.assert_called_once()
        # Verify the params contain tenant_id
        call_args = db.execute.call_args
        params = call_args[0][1]  # Second positional arg (params dict)
        assert params["tenant_id"] == str(TENANT_ID)

    def test_handles_missing_extra_gracefully(self):
        """When extra JSON is empty or missing breakdowns key, returns empty."""
        db = MagicMock()
        db.execute.return_value = MagicMock(
            fetchall=MagicMock(
                return_value=[
                    _make_metric_row("meta_reach_by_age", {}),
                    _make_metric_row("meta_reach_by_gender", {"breakdowns": []}),
                ],
            ),
        )

        service = ChannelDashboardService(db)
        result = service.get_demographics(TENANT_ID, "meta-ads", "30d")

        assert result.age == []
        assert result.gender == []
        assert result.placement == []

    def test_handles_extra_as_already_parsed_dict(self):
        """When extra is returned as dict (not string), still works."""
        db = MagicMock()
        row = MagicMock()
        row._mapping = {
            "metric_name": "meta_reach_by_age",
            "extra": {
                "breakdowns": [
                    {"dimension_values": ["18-24"], "value": 5000},
                ],
            },
        }
        db.execute.return_value = MagicMock(fetchall=MagicMock(return_value=[row]))

        service = ChannelDashboardService(db)
        result = service.get_demographics(TENANT_ID, "meta-ads", "30d")

        assert len(result.age) == 1
        assert result.age[0].value == 5000

    def test_zero_total_gives_zero_percentages(self):
        """When all values are 0, percentages are 0 (no division by zero)."""
        db = MagicMock()
        db.execute.return_value = MagicMock(
            fetchall=MagicMock(
                return_value=[
                    _make_metric_row(
                        "meta_reach_by_age",
                        {
                            "breakdowns": [
                                {"dimension_values": ["18-24"], "value": 0},
                                {"dimension_values": ["25-34"], "value": 0},
                            ],
                        },
                    ),
                ],
            ),
        )

        service = ChannelDashboardService(db)
        result = service.get_demographics(TENANT_ID, "meta-ads", "30d")

        assert len(result.age) == 2
        assert result.age[0].percentage == 0.0
        assert result.age[1].percentage == 0.0
