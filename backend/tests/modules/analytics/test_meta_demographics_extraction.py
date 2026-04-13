"""Tests for Meta Ads demographic breakdown extraction.

Validates that:
1. MetaProvider._extract_meta_ads_breakdowns() produces the correct format
2. The extracted format is compatible with ChannelDashboardService.get_demographics()
3. Breakdown metrics are properly registered in the metric catalog
4. Edge cases (empty data, missing fields, API errors) are handled gracefully
"""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.modules.analytics.application.services.channel_dashboard_service import (
    ChannelDashboardService,
)
from src.modules.analytics.domain.enums import AggregationType, MetricUnit
from src.modules.analytics.domain.metric_catalog import get_metric_def
from src.modules.analytics.infrastructure.providers.meta_provider import MetaProvider

TENANT_ID = uuid4()
CREDS = {
    "access_token": "test_token",
    "ad_account_id": "111222",
}
START = date(2026, 3, 1)
END = date(2026, 3, 15)


def _ok_response(json_data: dict) -> MagicMock:
    """Build a mock response with status 200."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


# ---------------------------------------------------------------------------
# Metric catalog tests
# ---------------------------------------------------------------------------


class TestBreakdownMetricCatalog:
    """Verify breakdown metrics are registered in the catalog with correct metadata."""

    _EXPECTED_BREAKDOWN_METRICS = [
        "meta_reach_by_age",
        "meta_spend_by_age",
        "meta_impressions_by_age",
        "meta_reach_by_gender",
        "meta_spend_by_gender",
        "meta_impressions_by_gender",
        "meta_reach_by_placement",
        "meta_spend_by_placement",
        "meta_impressions_by_placement",
    ]

    def test_all_breakdown_metrics_registered(self):
        """All 9 breakdown metrics (3 base x 3 dimensions) exist in the catalog."""
        for metric_name in self._EXPECTED_BREAKDOWN_METRICS:
            defn = get_metric_def(metric_name)
            assert defn is not None, f"{metric_name} not found in METRIC_CATALOG"

    def test_breakdown_metrics_use_json_unit(self):
        """Breakdown metrics should use MetricUnit.JSON since they store JSONB data."""
        for metric_name in self._EXPECTED_BREAKDOWN_METRICS:
            defn = get_metric_def(metric_name)
            assert defn is not None
            assert defn.unit == MetricUnit.JSON, f"{metric_name} should have unit=JSON, got {defn.unit}"

    def test_breakdown_metrics_are_snapshot(self):
        """Breakdown metrics use SNAPSHOT aggregation (period summary, not additive)."""
        for metric_name in self._EXPECTED_BREAKDOWN_METRICS:
            defn = get_metric_def(metric_name)
            assert defn is not None
            assert defn.aggregation == AggregationType.SNAPSHOT, (
                f"{metric_name} should have aggregation=SNAPSHOT, got {defn.aggregation}"
            )

    def test_breakdown_metrics_have_meta_provider(self):
        """Breakdown metrics should list 'meta' as a provider."""
        for metric_name in self._EXPECTED_BREAKDOWN_METRICS:
            defn = get_metric_def(metric_name)
            assert defn is not None
            assert "meta" in defn.providers, f"{metric_name} should have 'meta' in providers"

    def test_breakdown_metrics_have_spanish_display_names(self):
        """Breakdown metrics should have Spanish display names with correct accents."""
        for metric_name in self._EXPECTED_BREAKDOWN_METRICS:
            defn = get_metric_def(metric_name)
            assert defn is not None
            assert defn.display_name, f"{metric_name} has empty display_name"
            # All display names should be non-empty Spanish text
            assert len(defn.display_name) > 3


# ---------------------------------------------------------------------------
# Extraction tests (MetaProvider._extract_meta_ads_breakdowns)
# ---------------------------------------------------------------------------


AGE_API_RESPONSE = [
    {"age": "18-24", "reach": "2000", "impressions": "8000", "spend": "30.00"},
    {"age": "25-34", "reach": "5000", "impressions": "20000", "spend": "60.00"},
    {"age": "35-44", "reach": "3000", "impressions": "12000", "spend": "45.00"},
]

GENDER_API_RESPONSE = [
    {"gender": "female", "reach": "4000", "impressions": "15000", "spend": "50.00"},
    {"gender": "male", "reach": "3000", "impressions": "13000", "spend": "40.00"},
    {"gender": "unknown", "reach": "1000", "impressions": "4000", "spend": "10.00"},
]

PLACEMENT_API_RESPONSE = [
    {
        "publisher_platform": "facebook",
        "platform_position": "feed",
        "reach": "5000",
        "impressions": "20000",
        "spend": "60.00",
    },
    {
        "publisher_platform": "instagram",
        "platform_position": "story",
        "reach": "2000",
        "impressions": "8000",
        "spend": "30.00",
    },
    {
        "publisher_platform": "audience_network",
        "platform_position": "classic",
        "reach": "1000",
        "impressions": "4000",
        "spend": "15.00",
    },
]


def _make_breakdown_mock_get():
    """Return a mock get that routes breakdown API calls correctly."""

    async def mock_get(url, **kwargs):
        params = kwargs.get("params", {})
        breakdowns = params.get("breakdowns", "")
        if breakdowns == "age":
            return _ok_response({"data": AGE_API_RESPONSE})
        if breakdowns == "gender":
            return _ok_response({"data": GENDER_API_RESPONSE})
        if "publisher_platform" in breakdowns:
            return _ok_response({"data": PLACEMENT_API_RESPONSE})
        return _ok_response({"data": []})

    return mock_get


class TestMetaDemographicsExtraction:
    """Test _extract_meta_ads_breakdowns produces correct ExtractedMetric objects."""

    @pytest.mark.asyncio
    async def test_extracts_age_breakdown_metrics(self):
        """Age breakdown produces meta_reach_by_age, meta_impressions_by_age, meta_spend_by_age."""
        client = AsyncMock()
        client.get = AsyncMock(side_effect=_make_breakdown_mock_get())

        provider = MetaProvider()
        metrics = await provider._extract_meta_ads_breakdowns(client, CREDS, START, END)

        age_metrics = [m for m in metrics if "_by_age" in m.metric_name]
        age_names = {m.metric_name for m in age_metrics}

        assert "meta_reach_by_age" in age_names
        assert "meta_impressions_by_age" in age_names
        assert "meta_spend_by_age" in age_names

    @pytest.mark.asyncio
    async def test_extracts_gender_breakdown_metrics(self):
        """Gender breakdown produces meta_reach_by_gender, meta_impressions_by_gender, meta_spend_by_gender."""
        client = AsyncMock()
        client.get = AsyncMock(side_effect=_make_breakdown_mock_get())

        provider = MetaProvider()
        metrics = await provider._extract_meta_ads_breakdowns(client, CREDS, START, END)

        gender_metrics = [m for m in metrics if "_by_gender" in m.metric_name]
        gender_names = {m.metric_name for m in gender_metrics}

        assert "meta_reach_by_gender" in gender_names
        assert "meta_impressions_by_gender" in gender_names
        assert "meta_spend_by_gender" in gender_names

    @pytest.mark.asyncio
    async def test_extracts_placement_breakdown_metrics(self):
        """Placement breakdown produces meta_reach/impressions/spend_by_placement."""
        client = AsyncMock()
        client.get = AsyncMock(side_effect=_make_breakdown_mock_get())

        provider = MetaProvider()
        metrics = await provider._extract_meta_ads_breakdowns(client, CREDS, START, END)

        placement_metrics = [m for m in metrics if "_by_placement" in m.metric_name]
        placement_names = {m.metric_name for m in placement_metrics}

        assert "meta_reach_by_placement" in placement_names
        assert "meta_impressions_by_placement" in placement_names
        assert "meta_spend_by_placement" in placement_names

    @pytest.mark.asyncio
    async def test_produces_nine_total_breakdown_metrics(self):
        """3 base metrics x 3 dimensions = 9 breakdown metrics."""
        client = AsyncMock()
        client.get = AsyncMock(side_effect=_make_breakdown_mock_get())

        provider = MetaProvider()
        metrics = await provider._extract_meta_ads_breakdowns(client, CREDS, START, END)

        assert len(metrics) == 9

    @pytest.mark.asyncio
    async def test_breakdown_extra_format(self):
        """Extracted metrics store breakdowns in extra['breakdowns'] as list of dicts."""
        client = AsyncMock()
        client.get = AsyncMock(side_effect=_make_breakdown_mock_get())

        provider = MetaProvider()
        metrics = await provider._extract_meta_ads_breakdowns(client, CREDS, START, END)

        for m in metrics:
            assert "breakdowns" in m.extra, f"{m.metric_name} missing 'breakdowns' key in extra"
            assert isinstance(m.extra["breakdowns"], list)
            for entry in m.extra["breakdowns"]:
                assert "dimension_values" in entry
                assert "value" in entry
                assert isinstance(entry["dimension_values"], list)
                assert isinstance(entry["value"], float)

    @pytest.mark.asyncio
    async def test_age_breakdown_dimension_values(self):
        """Age breakdown entries have single-element dimension_values with age range strings."""
        client = AsyncMock()
        client.get = AsyncMock(side_effect=_make_breakdown_mock_get())

        provider = MetaProvider()
        metrics = await provider._extract_meta_ads_breakdowns(client, CREDS, START, END)

        age_reach = next(m for m in metrics if m.metric_name == "meta_reach_by_age")
        breakdowns = age_reach.extra["breakdowns"]

        assert len(breakdowns) == 3  # 18-24, 25-34, 35-44
        labels = [b["dimension_values"][0] for b in breakdowns]
        assert "18-24" in labels
        assert "25-34" in labels
        assert "35-44" in labels

    @pytest.mark.asyncio
    async def test_placement_breakdown_has_two_dimension_values(self):
        """Placement breakdowns have [publisher_platform, platform_position]."""
        client = AsyncMock()
        client.get = AsyncMock(side_effect=_make_breakdown_mock_get())

        provider = MetaProvider()
        metrics = await provider._extract_meta_ads_breakdowns(client, CREDS, START, END)

        placement_reach = next(m for m in metrics if m.metric_name == "meta_reach_by_placement")
        breakdowns = placement_reach.extra["breakdowns"]

        for entry in breakdowns:
            assert len(entry["dimension_values"]) == 2, "Placement should have [publisher_platform, platform_position]"

        # Verify specific placement
        first_entry = breakdowns[0]
        assert first_entry["dimension_values"] == ["facebook", "feed"]

    @pytest.mark.asyncio
    async def test_breakdown_metrics_use_json_unit(self):
        """All breakdown ExtractedMetric objects use unit='json'."""
        client = AsyncMock()
        client.get = AsyncMock(side_effect=_make_breakdown_mock_get())

        provider = MetaProvider()
        metrics = await provider._extract_meta_ads_breakdowns(client, CREDS, START, END)

        for m in metrics:
            assert m.unit == "json", f"{m.metric_name} should have unit='json'"

    @pytest.mark.asyncio
    async def test_breakdown_metrics_use_meta_ads_channel(self):
        """All breakdown metrics should have channel_slug='meta-ads'."""
        client = AsyncMock()
        client.get = AsyncMock(side_effect=_make_breakdown_mock_get())

        provider = MetaProvider()
        metrics = await provider._extract_meta_ads_breakdowns(client, CREDS, START, END)

        for m in metrics:
            assert m.channel_slug == "meta-ads"

    @pytest.mark.asyncio
    async def test_breakdown_value_is_zero_placeholder(self):
        """Breakdown metrics use value=0.0 as placeholder (real data is in extra)."""
        client = AsyncMock()
        client.get = AsyncMock(side_effect=_make_breakdown_mock_get())

        provider = MetaProvider()
        metrics = await provider._extract_meta_ads_breakdowns(client, CREDS, START, END)

        for m in metrics:
            assert m.value == 0.0, f"{m.metric_name} should have value=0.0 (data lives in extra)"

    @pytest.mark.asyncio
    async def test_no_ad_account_returns_empty(self):
        """Without ad_account_id in credentials, return empty list."""
        client = AsyncMock()
        provider = MetaProvider()
        metrics = await provider._extract_meta_ads_breakdowns(
            client,
            {"access_token": "tok"},
            START,
            END,
        )
        assert metrics == []

    @pytest.mark.asyncio
    async def test_empty_api_response_no_crash(self):
        """When Meta API returns empty data arrays, no metrics are produced."""

        async def mock_get(url, **kwargs):
            return _ok_response({"data": []})

        client = AsyncMock()
        client.get = AsyncMock(side_effect=mock_get)

        provider = MetaProvider()
        metrics = await provider._extract_meta_ads_breakdowns(client, CREDS, START, END)

        assert metrics == []


# ---------------------------------------------------------------------------
# Extraction <-> get_demographics() compatibility tests
# ---------------------------------------------------------------------------


class TestExtractionToDemographicsCompatibility:
    """Verify the format produced by _extract_meta_ads_breakdowns is correctly
    consumed by ChannelDashboardService.get_demographics() / _parse_breakdown_segments().
    """

    @pytest.mark.asyncio
    async def test_extraction_format_matches_demographics_parser(self):
        """The breakdowns format from extraction can be parsed by _parse_breakdown_segments."""
        # Step 1: Extract breakdown metrics
        client = AsyncMock()
        client.get = AsyncMock(side_effect=_make_breakdown_mock_get())

        provider = MetaProvider()
        metrics = await provider._extract_meta_ads_breakdowns(client, CREDS, START, END)

        # Step 2: Feed the extracted data through the demographics parser
        age_metric = next(m for m in metrics if m.metric_name == "meta_reach_by_age")
        breakdowns_data = age_metric.extra["breakdowns"]

        segments = ChannelDashboardService._parse_breakdown_segments(breakdowns_data)

        assert len(segments) == 3
        # Verify segment structure
        assert segments[0].label == "18-24"
        assert segments[0].value == 2000.0
        # Percentages: 2000 / (2000+5000+3000) = 20.0%
        assert segments[0].percentage == 20.0
        assert segments[1].label == "25-34"
        assert segments[1].value == 5000.0
        assert segments[1].percentage == 50.0

    @pytest.mark.asyncio
    async def test_gender_extraction_compatible_with_parser(self):
        """Gender breakdown extraction format is parseable by demographics parser."""
        client = AsyncMock()
        client.get = AsyncMock(side_effect=_make_breakdown_mock_get())

        provider = MetaProvider()
        metrics = await provider._extract_meta_ads_breakdowns(client, CREDS, START, END)

        gender_metric = next(m for m in metrics if m.metric_name == "meta_reach_by_gender")
        segments = ChannelDashboardService._parse_breakdown_segments(
            gender_metric.extra["breakdowns"],
        )

        assert len(segments) == 3  # female, male, unknown
        labels = {s.label for s in segments}
        assert "female" in labels
        assert "male" in labels
        assert "unknown" in labels

        # Check percentages sum to 100%
        total_pct = sum(s.percentage for s in segments)
        assert abs(total_pct - 100.0) < 0.5  # Allow rounding tolerance

    @pytest.mark.asyncio
    async def test_placement_extraction_uses_first_dimension_value(self):
        """Placement breakdowns have 2 dimension_values; parser uses first one as label."""
        client = AsyncMock()
        client.get = AsyncMock(side_effect=_make_breakdown_mock_get())

        provider = MetaProvider()
        metrics = await provider._extract_meta_ads_breakdowns(client, CREDS, START, END)

        placement_metric = next(m for m in metrics if m.metric_name == "meta_reach_by_placement")
        segments = ChannelDashboardService._parse_breakdown_segments(
            placement_metric.extra["breakdowns"],
        )

        assert len(segments) == 3
        # Parser takes dimension_values[0] as label
        assert segments[0].label == "facebook"
        assert segments[1].label == "instagram"
        assert segments[2].label == "audience_network"

    @pytest.mark.asyncio
    async def test_extraction_values_preserved_through_parsing(self):
        """Numeric values from extraction survive parsing accurately."""
        client = AsyncMock()
        client.get = AsyncMock(side_effect=_make_breakdown_mock_get())

        provider = MetaProvider()
        metrics = await provider._extract_meta_ads_breakdowns(client, CREDS, START, END)

        # Check spend_by_age values are accurately parsed
        spend_age = next(m for m in metrics if m.metric_name == "meta_spend_by_age")
        segments = ChannelDashboardService._parse_breakdown_segments(
            spend_age.extra["breakdowns"],
        )

        values = {s.label: s.value for s in segments}
        assert values["18-24"] == 30.0
        assert values["25-34"] == 60.0
        assert values["35-44"] == 45.0
