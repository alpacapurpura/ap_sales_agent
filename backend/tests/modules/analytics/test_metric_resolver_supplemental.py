"""Supplemental tests for MetricResolver — covering uncovered branches."""

from datetime import date
from unittest.mock import MagicMock

import pytest

from src.modules.analytics.domain.metric_resolver import (
    MetricResolver,
    _extract_multiplier,
    _get_formula_components,
)

# ─── _extract_multiplier ─────────────────────────────────────────────────────


class TestExtractMultiplier:
    def test_none_formula_returns_1(self):
        assert _extract_multiplier(None) == 1.0

    def test_empty_formula_returns_1(self):
        assert _extract_multiplier("") == 1.0

    def test_formula_with_multiplier(self):
        assert _extract_multiplier("clicks / impressions * 100") == 100.0

    def test_formula_without_multiplier_returns_1(self):
        assert _extract_multiplier("spend / clicks") == 1.0


# ─── _get_formula_components ─────────────────────────────────────────────────


class TestGetFormulaComponents:
    def _derived_defn_short(self):
        from src.modules.analytics.domain.enums import AggregationType
        from src.modules.analytics.domain.metric_catalog import MetricDefinition

        defn = MagicMock()
        defn.aggregation = AggregationType.DERIVED
        defn.formula_components = ["only_one"]  # less than 2 → None
        return defn

    def _weighted_avg_no_weight(self):
        from src.modules.analytics.domain.enums import AggregationType

        defn = MagicMock()
        defn.aggregation = AggregationType.WEIGHTED_AVERAGE
        defn.formula = "clicks / impressions * 100"
        defn.weight_metric = None  # no weight_metric → None
        return defn

    def _weighted_avg_no_slash(self):
        from src.modules.analytics.domain.enums import AggregationType

        defn = MagicMock()
        defn.aggregation = AggregationType.WEIGHTED_AVERAGE
        defn.formula = "just_clicks"  # no "/" → None
        defn.weight_metric = "impressions"
        return defn

    def test_derived_too_few_components_returns_none(self):
        defn = self._derived_defn_short()
        assert _get_formula_components(defn) is None

    def test_weighted_avg_no_weight_returns_none(self):
        defn = self._weighted_avg_no_weight()
        assert _get_formula_components(defn) is None

    def test_weighted_avg_no_slash_returns_none(self):
        defn = self._weighted_avg_no_slash()
        assert _get_formula_components(defn) is None

    def test_additive_returns_none(self):
        from src.modules.analytics.domain.enums import AggregationType

        defn = MagicMock()
        defn.aggregation = AggregationType.ADDITIVE
        assert _get_formula_components(defn) is None


# ─── MetricResolver.resolve_period_kpis ───────────────────────────────────────


class TestResolvePeriodKpis:
    def _resolver(self):
        return MetricResolver()

    def _make_row(self, metric_name, value, campaign_id=None, ad_set_id=None, ad_id=None, d=None):
        d = d or date(2026, 3, 15)
        return (d, metric_name, value, campaign_id, ad_set_id, ad_id)

    def test_unknown_metric_with_data_returns_sum(self):
        resolver = self._resolver()
        rows = [self._make_row("nonexistent_metric_xyz", 42.0)]
        result = resolver.resolve_period_kpis(rows, ["nonexistent_metric_xyz"])
        assert result["nonexistent_metric_xyz"] == 42.0

    def test_unknown_metric_no_data_returns_none(self):
        resolver = self._resolver()
        result = resolver.resolve_period_kpis([], ["unknown_metric_abc"])
        assert result["unknown_metric_abc"] is None

    def test_campaign_rows_filtered_out(self):
        resolver = self._resolver()
        rows = [
            self._make_row("reach", 1000.0, campaign_id=None),
            self._make_row("reach", 500.0, campaign_id="campaign-123"),  # filtered
        ]
        result = resolver.resolve_period_kpis(rows, ["reach"])
        assert result["reach"] == 1000.0

    def test_alias_resolved_before_lookup(self):
        resolver = self._resolver()
        # "reach" has no alias, so just test that the alias map is applied
        rows = [self._make_row("reach", 500.0)]
        result = resolver.resolve_period_kpis(rows, ["reach"])
        assert result["reach"] is not None


# ─── MetricResolver.resolve_daily_timeseries ─────────────────────────────────


class TestResolveDailyTimeseries:
    def _resolver(self):
        return MetricResolver()

    def _make_row(self, metric_name, value, d=None, campaign_id=None):
        d = d or date(2026, 3, 15)
        return (d, metric_name, value, campaign_id, None, None)

    def test_unknown_metric_returns_raw_values(self):
        resolver = self._resolver()
        d = date(2026, 3, 1)
        rows = [self._make_row("totally_unknown_xyz", 99.0, d=d)]
        result = resolver.resolve_daily_timeseries(rows, ["totally_unknown_xyz"])
        assert "totally_unknown_xyz" in result
        assert result["totally_unknown_xyz"] == [(d, 99.0)]

    def test_additive_metric_returns_daily_values(self):
        resolver = self._resolver()
        d = date(2026, 3, 1)
        rows = [self._make_row("reach", 1000.0, d=d)]
        result = resolver.resolve_daily_timeseries(rows, ["reach"])
        assert "reach" in result
        assert len(result["reach"]) == 1

    def test_derived_metric_zero_denom_skipped(self):
        resolver = self._resolver()
        d = date(2026, 3, 1)
        # cpc = spend / clicks; clicks = 0 → skip that day
        rows = [
            self._make_row("spend", 100.0, d=d),
            self._make_row("link_clicks", 0.0, d=d),
        ]
        result = resolver.resolve_daily_timeseries(rows, ["cpc"])
        assert "cpc" in result
        assert result["cpc"] == []  # zero denom skipped

    def test_campaign_rows_excluded_from_daily(self):
        resolver = self._resolver()
        d = date(2026, 3, 1)
        rows = [
            self._make_row("reach", 1000.0, d=d, campaign_id=None),  # account level
            self._make_row("reach", 200.0, d=d, campaign_id="camp-1"),  # filtered
        ]
        result = resolver.resolve_daily_timeseries(rows, ["reach"])
        assert result["reach"] == [(d, 1000.0)]

    def test_fallback_when_defn_none(self):
        resolver = self._resolver()
        d = date(2026, 3, 10)
        rows = [self._make_row("xyz_metric_nonexistent", 5.0, d=d)]
        result = resolver.resolve_daily_timeseries(rows, ["xyz_metric_nonexistent"])
        assert result["xyz_metric_nonexistent"] == [(d, 5.0)]


# ─── MetricResolver.resolve_from_aggregated ──────────────────────────────────


class TestResolveFromAggregated:
    def _resolver(self):
        return MetricResolver()

    def test_unknown_metric_returns_direct_value(self):
        resolver = self._resolver()
        aggregated = {"some_weird_metric": 42.0}
        result = resolver.resolve_from_aggregated(aggregated, ["some_weird_metric"])
        assert result["some_weird_metric"] == 42.0

    def test_unknown_metric_absent_returns_none(self):
        resolver = self._resolver()
        result = resolver.resolve_from_aggregated({}, ["another_missing"])
        assert result["another_missing"] is None

    def test_additive_metric_returns_direct_value(self):
        resolver = self._resolver()
        result = resolver.resolve_from_aggregated({"reach": 5000.0}, ["reach"])
        assert result["reach"] == 5000.0


# ─── MetricResolver._recalculate_from_components ─────────────────────────────


class TestRecalculateFromComponents:
    def _resolver(self):
        return MetricResolver()

    def test_no_formula_components_returns_none(self):
        resolver = self._resolver()
        from src.modules.analytics.domain.enums import AggregationType

        defn = MagicMock()
        defn.aggregation = AggregationType.DERIVED
        defn.formula_components = []
        defn.formula = None
        defn.name = "derived_no_formula"
        defn.weight_metric = None
        result = resolver._recalculate_from_components(defn, {})
        assert result is None

    def test_zero_denominator_returns_none(self):
        resolver = self._resolver()
        from src.modules.analytics.domain.enums import AggregationType

        defn = MagicMock()
        defn.aggregation = AggregationType.DERIVED
        defn.formula_components = ["spend", "clicks"]
        defn.formula = "spend / clicks"
        defn.weight_metric = None
        result = resolver._recalculate_from_components(defn, {"spend": 100.0, "clicks": 0.0})
        assert result is None
