"""Tests for MetricResolver — pure domain class that resolves period KPIs and daily time series.

Covers:
- Account-level filtering (BUG1: double-counting prevention)
- Derived metric recalculation from components (BUG2)
- Alias mapping (BUG3: hero_metrics names → catalog names)
- Edge cases: zero denominators, missing data, NON_AGGREGABLE latest-value
"""

from datetime import date

import pytest

from src.modules.analytics.domain.metric_resolver import MetricResolver

# ── Helpers ──────────────────────────────────────────────────────────────────


def _row(
    d: date,
    name: str,
    value: float,
    campaign_id: str | None = None,
    ad_set_id: str | None = None,
    ad_id: str | None = None,
) -> tuple[date, str, float, str | None, str | None, str | None]:
    """Shorthand to build a raw daily row tuple."""
    return (d, name, value, campaign_id, ad_set_id, ad_id)


D1 = date(2026, 3, 1)
D2 = date(2026, 3, 2)
D3 = date(2026, 3, 3)


# ── Period KPI tests ─────────────────────────────────────────────────────────


class TestResolveAdditive:
    """ADDITIVE metrics should SUM only account-level rows."""

    def test_sums_only_account_level_rows(self) -> None:
        """BUG1 regression: campaign-level rows must NOT be included in the sum."""
        rows = [
            # Account-level rows have no campaign_id
            _row(D1, "spend", 100.0),
            _row(D2, "spend", 200.0),
            # Campaign-level — should be EXCLUDED
            _row(D1, "spend", 60.0, campaign_id="camp_1"),
            _row(D2, "spend", 140.0, campaign_id="camp_1"),
        ]
        resolver = MetricResolver()
        result = resolver.resolve_period_kpis(rows, ["spend"])
        assert result["spend"] == 300.0  # 100 + 200, NOT 500

    def test_sums_multiple_days(self) -> None:
        rows = [
            _row(D1, "impressions", 1000.0),
            _row(D2, "impressions", 2000.0),
            _row(D3, "impressions", 3000.0),
        ]
        resolver = MetricResolver()
        result = resolver.resolve_period_kpis(rows, ["impressions"])
        assert result["impressions"] == 6000.0


class TestResolveDerived:
    """DERIVED metrics: recalculate from ADDITIVE component sums."""

    def test_cpc_from_components(self) -> None:
        """CPC = spend / clicks across the full period."""
        rows = [
            _row(D1, "spend", 100.0),
            _row(D2, "spend", 100.0),
            _row(D3, "spend", 100.0),
            _row(D1, "clicks", 20.0),
            _row(D2, "clicks", 20.0),
            _row(D3, "clicks", 20.0),
        ]
        resolver = MetricResolver()
        result = resolver.resolve_period_kpis(rows, ["CPC"])
        assert result["CPC"] == pytest.approx(5.0)

    def test_roas_from_components(self) -> None:
        """ROAS = meta_conversion_value / spend."""
        rows = [
            _row(D1, "meta_conversion_value", 300.0),
            _row(D2, "meta_conversion_value", 300.0),
            _row(D3, "meta_conversion_value", 300.0),
            _row(D1, "spend", 100.0),
            _row(D2, "spend", 100.0),
            _row(D3, "spend", 100.0),
        ]
        resolver = MetricResolver()
        result = resolver.resolve_period_kpis(rows, ["ROAS"])
        assert result["ROAS"] == pytest.approx(3.0)

    def test_cpa_from_components(self) -> None:
        """CPA (meta_cost_per_purchase) = spend / conversions."""
        rows = [
            _row(D1, "spend", 100.0),
            _row(D2, "spend", 100.0),
            _row(D3, "spend", 100.0),
            _row(D1, "conversions", 3.0),
            _row(D2, "conversions", 4.0),
            _row(D3, "conversions", 3.0),
        ]
        resolver = MetricResolver()
        result = resolver.resolve_period_kpis(rows, ["CPA"])
        assert result["CPA"] == pytest.approx(30.0)

    def test_cpl_from_components(self) -> None:
        """CPL (meta_cost_per_lead) = spend / meta_leads."""
        rows = [
            _row(D1, "spend", 100.0),
            _row(D2, "spend", 100.0),
            _row(D3, "spend", 100.0),
            _row(D1, "meta_leads", 5.0),
            _row(D2, "meta_leads", 5.0),
            _row(D3, "meta_leads", 5.0),
        ]
        resolver = MetricResolver()
        result = resolver.resolve_period_kpis(rows, ["CPL"])
        assert result["CPL"] == pytest.approx(20.0)


class TestResolveWeightedAverage:
    """WEIGHTED_AVERAGE metrics: recalculate numerator/denominator from formula."""

    def test_ctr_from_components(self) -> None:
        """BUG2 regression: CTR = SUM(clicks)/SUM(impressions)*100 for the period."""
        rows = [
            _row(D1, "clicks", 10.0),
            _row(D2, "clicks", 20.0),
            _row(D3, "clicks", 30.0),
            _row(D1, "impressions", 1000.0),
            _row(D2, "impressions", 2000.0),
            _row(D3, "impressions", 3000.0),
        ]
        resolver = MetricResolver()
        result = resolver.resolve_period_kpis(rows, ["CTR"])
        # CTR = 60 / 6000 * 100 = 1.0%
        assert result["CTR"] == pytest.approx(1.0)

    def test_cpm_from_components(self) -> None:
        """CPM = SUM(spend) / SUM(impressions) * 1000."""
        rows = [
            _row(D1, "spend", 100.0),
            _row(D2, "spend", 100.0),
            _row(D3, "spend", 100.0),
            _row(D1, "impressions", 1000.0),
            _row(D2, "impressions", 2000.0),
            _row(D3, "impressions", 3000.0),
        ]
        resolver = MetricResolver()
        result = resolver.resolve_period_kpis(rows, ["CPM"])
        # CPM = 300 / 6000 * 1000 = 50.0
        assert result["CPM"] == pytest.approx(50.0)


class TestResolveNonAggregable:
    """NON_AGGREGABLE metrics: use latest date's value."""

    def test_uses_latest_date_value(self) -> None:
        rows = [
            _row(D1, "reach", 1000.0),
            _row(D2, "reach", 1200.0),
            _row(D3, "reach", 1100.0),
        ]
        resolver = MetricResolver()
        result = resolver.resolve_period_kpis(rows, ["reach"])
        # D3 is the latest → 1100
        assert result["reach"] == 1100.0


class TestEdgeCases:
    """Edge cases: zero denominator, missing components, alias mapping."""

    def test_zero_denominator_returns_none(self) -> None:
        """Division by zero should yield None, not crash."""
        rows = [
            _row(D1, "spend", 100.0),
            _row(D1, "clicks", 0.0),
            _row(D2, "spend", 100.0),
            _row(D2, "clicks", 0.0),
        ]
        resolver = MetricResolver()
        result = resolver.resolve_period_kpis(rows, ["CPC"])
        assert result["CPC"] is None

    def test_missing_metric_returns_none(self) -> None:
        """Requesting a metric with no data at all returns None."""
        rows = [
            _row(D1, "spend", 100.0),
        ]
        resolver = MetricResolver()
        result = resolver.resolve_period_kpis(rows, ["CPC"])
        # clicks not in rows → CPC cannot be computed
        assert result["CPC"] is None

    def test_alias_mapping_resolves_correctly(self) -> None:
        """BUG3 regression: hero_metrics aliases should map to canonical names."""
        resolver = MetricResolver()
        assert resolver.resolve_alias("ROAS") == "meta_purchase_roas"
        assert resolver.resolve_alias("CPA") == "meta_cost_per_purchase"
        assert resolver.resolve_alias("CPL") == "meta_cost_per_lead"
        assert resolver.resolve_alias("CTR") == "ctr"
        assert resolver.resolve_alias("CPC") == "cpc"
        assert resolver.resolve_alias("CPM") == "cpm"

    def test_non_alias_passes_through(self) -> None:
        """Names not in ALIAS_MAP should pass through unchanged."""
        resolver = MetricResolver()
        assert resolver.resolve_alias("spend") == "spend"
        assert resolver.resolve_alias("impressions") == "impressions"

    def test_mixed_aliases_and_canonical(self) -> None:
        """Mix of aliases and canonical names in one request."""
        rows = [
            _row(D1, "spend", 300.0),
            _row(D1, "clicks", 60.0),
            _row(D1, "impressions", 6000.0),
        ]
        resolver = MetricResolver()
        result = resolver.resolve_period_kpis(rows, ["spend", "CPC", "CTR"])
        assert result["spend"] == 300.0
        assert result["CPC"] == pytest.approx(5.0)
        assert result["CTR"] == pytest.approx(1.0)


# ── Daily Time Series tests ──────────────────────────────────────────────────


class TestResolveDailyTimeseries:
    """Daily time series: per-day values with derived recalculation."""

    def test_additive_returns_raw_daily_values(self) -> None:
        rows = [
            _row(D1, "spend", 100.0),
            _row(D2, "spend", 200.0),
            _row(D3, "spend", 150.0),
        ]
        resolver = MetricResolver()
        result = resolver.resolve_daily_timeseries(rows, ["spend"])
        assert result["spend"] == [(D1, 100.0), (D2, 200.0), (D3, 150.0)]

    def test_derived_recalculates_per_day(self) -> None:
        """CPC should be recalculated per day from spend and clicks."""
        rows = [
            _row(D1, "spend", 50.0),
            _row(D2, "spend", 100.0),
            _row(D3, "spend", 150.0),
            _row(D1, "clicks", 10.0),
            _row(D2, "clicks", 25.0),
            _row(D3, "clicks", 30.0),
        ]
        resolver = MetricResolver()
        result = resolver.resolve_daily_timeseries(rows, ["CPC"])
        expected = [
            (D1, pytest.approx(5.0)),
            (D2, pytest.approx(4.0)),
            (D3, pytest.approx(5.0)),
        ]
        assert len(result["CPC"]) == 3
        for (d_actual, v_actual), (d_expected, v_expected) in zip(
            result["CPC"], expected, strict=True
        ):
            assert d_actual == d_expected
            assert v_actual == v_expected

    def test_weighted_avg_recalculates_per_day(self) -> None:
        """CTR should be recalculated per day from clicks and impressions."""
        rows = [
            _row(D1, "clicks", 10.0),
            _row(D2, "clicks", 30.0),
            _row(D1, "impressions", 1000.0),
            _row(D2, "impressions", 2000.0),
        ]
        resolver = MetricResolver()
        result = resolver.resolve_daily_timeseries(rows, ["CTR"])
        assert len(result["CTR"]) == 2
        # Day 1 expected CTR: 1.0
        assert result["CTR"][0] == (D1, pytest.approx(1.0))
        # Day 2 expected CTR: 1.5
        assert result["CTR"][1] == (D2, pytest.approx(1.5))

    def test_daily_filters_account_level_only(self) -> None:
        """Campaign-level rows should be excluded from daily time series."""
        rows = [
            _row(D1, "spend", 100.0),
            _row(D1, "spend", 60.0, campaign_id="camp_1"),
            _row(D2, "spend", 200.0),
        ]
        resolver = MetricResolver()
        result = resolver.resolve_daily_timeseries(rows, ["spend"])
        assert result["spend"] == [(D1, 100.0), (D2, 200.0)]

    def test_daily_zero_denominator_skips_day(self) -> None:
        """Days where denominator is 0 should be excluded from time series."""
        rows = [
            _row(D1, "spend", 100.0),
            _row(D1, "clicks", 0.0),
            _row(D2, "spend", 200.0),
            _row(D2, "clicks", 40.0),
        ]
        resolver = MetricResolver()
        result = resolver.resolve_daily_timeseries(rows, ["CPC"])
        # D1 should be skipped (clicks=0), D2 should be present
        assert len(result["CPC"]) == 1
        assert result["CPC"][0] == (D2, pytest.approx(5.0))


# ── resolve_from_aggregated tests ──────────────────────────────────────────


class TestResolveFromAggregated:
    """Test resolve_from_aggregated() — works with pre-aggregated dicts.

    This is the method used by ChannelDashboardService to resolve aliases
    and recalculate derived metrics from the dict returned by
    get_channel_metrics_for_period().
    """

    def test_alias_resolved_to_existing_canonical(self) -> None:
        """ROAS alias should find meta_purchase_roas in the dict."""
        resolver = MetricResolver()
        aggregated = {"meta_purchase_roas": 3.5, "spend": 1000.0}
        result = resolver.resolve_from_aggregated(aggregated, ["ROAS"])
        assert result["ROAS"] == 3.5

    def test_canonical_name_passthrough(self) -> None:
        """Non-aliased names should be returned as-is from the dict."""
        resolver = MetricResolver()
        aggregated = {"spend": 1000.0, "impressions": 50000.0}
        result = resolver.resolve_from_aggregated(aggregated, ["spend"])
        assert result["spend"] == 1000.0

    def test_derived_cpc_recalculated(self) -> None:
        """CPC should be recalculated from spend/clicks when components exist."""
        resolver = MetricResolver()
        aggregated = {"spend": 300.0, "clicks": 60.0}
        result = resolver.resolve_from_aggregated(aggregated, ["CPC"])
        assert result["CPC"] == pytest.approx(5.0)

    def test_derived_roas_recalculated(self) -> None:
        """ROAS should be recalculated from meta_conversion_value/spend."""
        resolver = MetricResolver()
        aggregated = {"meta_conversion_value": 3000.0, "spend": 1000.0}
        result = resolver.resolve_from_aggregated(aggregated, ["ROAS"])
        assert result["ROAS"] == pytest.approx(3.0)

    def test_weighted_avg_ctr_recalculated(self) -> None:
        """CTR should be recalculated from clicks/impressions * 100."""
        resolver = MetricResolver()
        aggregated = {"clicks": 60.0, "impressions": 6000.0}
        result = resolver.resolve_from_aggregated(aggregated, ["CTR"])
        assert result["CTR"] == pytest.approx(1.0)

    def test_weighted_avg_cpm_recalculated(self) -> None:
        """CPM should be recalculated from spend/impressions * 1000."""
        resolver = MetricResolver()
        aggregated = {"spend": 300.0, "impressions": 6000.0}
        result = resolver.resolve_from_aggregated(aggregated, ["CPM"])
        assert result["CPM"] == pytest.approx(50.0)

    def test_derived_cpa_recalculated(self) -> None:
        """CPA should be recalculated from spend/conversions."""
        resolver = MetricResolver()
        aggregated = {"spend": 300.0, "conversions": 10.0}
        result = resolver.resolve_from_aggregated(aggregated, ["CPA"])
        assert result["CPA"] == pytest.approx(30.0)

    def test_derived_cpl_recalculated(self) -> None:
        """CPL should be recalculated from spend/meta_leads."""
        resolver = MetricResolver()
        aggregated = {"spend": 300.0, "meta_leads": 15.0}
        result = resolver.resolve_from_aggregated(aggregated, ["CPL"])
        assert result["CPL"] == pytest.approx(20.0)

    def test_zero_denominator_returns_none(self) -> None:
        """Zero denominator should return None."""
        resolver = MetricResolver()
        aggregated = {"spend": 300.0, "clicks": 0.0}
        result = resolver.resolve_from_aggregated(aggregated, ["CPC"])
        assert result["CPC"] is None

    def test_missing_components_returns_none(self) -> None:
        """Missing component metrics should return None."""
        resolver = MetricResolver()
        aggregated = {"spend": 300.0}  # no clicks
        result = resolver.resolve_from_aggregated(aggregated, ["CPC"])
        assert result["CPC"] is None

    def test_mixed_aliases_and_canonical(self) -> None:
        """Mix of aliased and non-aliased metrics."""
        resolver = MetricResolver()
        aggregated = {
            "spend": 300.0,
            "clicks": 60.0,
            "impressions": 6000.0,
            "conversions": 10.0,
        }
        result = resolver.resolve_from_aggregated(
            aggregated, ["spend", "CPC", "CTR", "CPA"]
        )
        assert result["spend"] == 300.0
        assert result["CPC"] == pytest.approx(5.0)
        assert result["CTR"] == pytest.approx(1.0)
        assert result["CPA"] == pytest.approx(30.0)

    def test_preexisting_canonical_value_used_for_non_derived(self) -> None:
        """For non-derived metrics, use existing value in dict (e.g., reach)."""
        resolver = MetricResolver()
        aggregated = {"reach": 50000.0}
        result = resolver.resolve_from_aggregated(aggregated, ["reach"])
        assert result["reach"] == 50000.0

    def test_does_not_mutate_input_dict(self) -> None:
        """resolve_from_aggregated should not modify the input dictionary."""
        resolver = MetricResolver()
        aggregated = {"spend": 300.0, "clicks": 60.0}
        original = dict(aggregated)
        resolver.resolve_from_aggregated(aggregated, ["CPC"])
        assert aggregated == original


# ── _resolve_daily_fetch_metrics tests ──────────────────────────────────────


class TestResolveDailyFetchMetrics:
    """Test that time series metric expansion includes component metrics."""

    def test_derived_cpc_includes_components(self) -> None:
        """CPC time series should trigger fetching spend and clicks."""
        from src.modules.analytics.application.services.channel_dashboard_service import (
            ChannelDashboardService,
        )

        resolver = MetricResolver()
        result = ChannelDashboardService._resolve_daily_fetch_metrics(resolver, ["CPC"])
        assert "spend" in result
        assert "clicks" in result
        assert "cpc" in result  # canonical name

    def test_weighted_avg_cpm_includes_components(self) -> None:
        """CPM time series should trigger fetching spend and impressions."""
        from src.modules.analytics.application.services.channel_dashboard_service import (
            ChannelDashboardService,
        )

        resolver = MetricResolver()
        result = ChannelDashboardService._resolve_daily_fetch_metrics(resolver, ["CPM"])
        assert "spend" in result
        assert "impressions" in result

    def test_additive_metric_no_extra_components(self) -> None:
        """Additive metrics (spend) should not add extra component metrics."""
        from src.modules.analytics.application.services.channel_dashboard_service import (
            ChannelDashboardService,
        )

        resolver = MetricResolver()
        result = ChannelDashboardService._resolve_daily_fetch_metrics(
            resolver, ["spend"]
        )
        assert "spend" in result
        assert len(result) == 1

    def test_meta_ads_full_timeseries_config(self) -> None:
        """Full meta-ads timeseries config should include all component metrics."""
        from src.modules.analytics.application.services.channel_dashboard_service import (
            ChannelDashboardService,
        )

        resolver = MetricResolver()
        timeseries = [
            "spend",
            "impressions",
            "clicks",
            "reach",
            "conversions",
            "ROAS",
            "CPC",
            "CPM",
            "CPL",
        ]
        result = ChannelDashboardService._resolve_daily_fetch_metrics(
            resolver, timeseries
        )
        # Must include base metrics
        for base in ["spend", "impressions", "clicks", "reach", "conversions"]:
            assert base in result, f"{base} should be in fetch list"
        # Must include components for ROAS (meta_conversion_value)
        assert "meta_conversion_value" in result
        # Must include components for CPL (meta_leads)
        assert "meta_leads" in result

    def test_conversions_resolves_to_itself(self) -> None:
        """'conversions' is a canonical metric name — should NOT be aliased."""
        resolver = MetricResolver()
        assert resolver.resolve_alias("conversions") == "conversions"
