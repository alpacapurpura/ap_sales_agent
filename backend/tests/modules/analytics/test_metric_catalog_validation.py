"""Tests for Metric Catalog structural validation.

Validates data integrity invariants that should never be broken:
- No duplicates, all required fields, minimum catalog size,
  unit/aggregation coherence, and presence of key aggregation types.

Pure Python tests: no DB, no async, no mocking required.
"""

from src.modules.analytics.domain.enums import AggregationType, MetricUnit
from src.modules.analytics.domain.metric_catalog import (
    _ADDITIVE,
    _DERIVED,
    _NON_AGGREGABLE,
    _SNAPSHOT,
    _WEIGHTED_AVERAGE,
    METRIC_CATALOG,
)


class TestNoDuplicateMetricNames:
    """The catalog must not contain duplicate metric names."""

    def test_no_duplicates_in_source_lists(self):
        """No name appears in more than one definition across all source lists."""
        all_metrics = [
            *_ADDITIVE,
            *_WEIGHTED_AVERAGE,
            *_DERIVED,
            *_NON_AGGREGABLE,
            *_SNAPSHOT,
        ]
        names = [m.name for m in all_metrics]
        duplicates = [name for name in set(names) if names.count(name) > 1]
        assert not duplicates, f"Duplicate metric names: {duplicates}"

    def test_catalog_size_matches_source_lists(self):
        """METRIC_CATALOG dict size matches total metrics across all source lists."""
        all_metrics = [
            *_ADDITIVE,
            *_WEIGHTED_AVERAGE,
            *_DERIVED,
            *_NON_AGGREGABLE,
            *_SNAPSHOT,
        ]
        assert len(METRIC_CATALOG) == len(all_metrics), (
            f"METRIC_CATALOG has {len(METRIC_CATALOG)} entries but source lists "
            f"have {len(all_metrics)} — likely duplicates collapsed"
        )


class TestRequiredFields:
    """Every MetricDefinition must have all required fields populated."""

    def test_all_have_name(self):
        for name, defn in METRIC_CATALOG.items():
            assert defn.name, f"Metric {name} has empty name"
            assert defn.name == name, f"Key '{name}' does not match defn.name '{defn.name}'"

    def test_all_have_unit(self):
        for name, defn in METRIC_CATALOG.items():
            assert isinstance(defn.unit, MetricUnit), f"{name} has invalid unit type: {type(defn.unit)}"

    def test_all_have_aggregation_type(self):
        for name, defn in METRIC_CATALOG.items():
            assert isinstance(defn.aggregation, AggregationType), (
                f"{name} has invalid aggregation type: {type(defn.aggregation)}"
            )

    def test_all_have_display_name(self):
        for name, defn in METRIC_CATALOG.items():
            assert defn.display_name, f"{name} has empty display_name"

    def test_all_have_description(self):
        for name, defn in METRIC_CATALOG.items():
            assert defn.description, f"{name} has empty description"

    def test_all_have_interpretation(self):
        for name, defn in METRIC_CATALOG.items():
            assert defn.interpretation, f"{name} has empty interpretation"


class TestCatalogMinimumSize:
    """The catalog must have a substantial number of metrics."""

    def test_at_least_50_metrics(self):
        """Catalog should have at least 50 metrics to cover all providers."""
        assert len(METRIC_CATALOG) >= 50, f"Catalog has only {len(METRIC_CATALOG)} metrics, expected >= 50"

    def test_has_additive_metrics(self):
        additive = [d for d in METRIC_CATALOG.values() if d.aggregation == AggregationType.ADDITIVE]
        assert len(additive) >= 20, f"Expected >= 20 ADDITIVE metrics, found {len(additive)}"


class TestAdditiveUnitCoherence:
    """ADDITIVE metrics should have summable units (COUNT or CURRENCY), not PERCENTAGE."""

    def test_additive_not_percentage(self):
        """No ADDITIVE metric should have unit=PERCENTAGE (percentages cannot be summed)."""
        violations = []
        for name, defn in METRIC_CATALOG.items():
            if defn.aggregation == AggregationType.ADDITIVE and defn.unit == MetricUnit.PERCENTAGE:
                violations.append(name)
        assert not violations, f"ADDITIVE metrics with PERCENTAGE unit (should be WEIGHTED_AVERAGE): {violations}"

    def test_additive_not_ratio(self):
        """No ADDITIVE metric should have unit=RATIO (ratios cannot be summed)."""
        violations = []
        for name, defn in METRIC_CATALOG.items():
            if defn.aggregation == AggregationType.ADDITIVE and defn.unit == MetricUnit.RATIO:
                violations.append(name)
        assert not violations, f"ADDITIVE metrics with RATIO unit (should be DERIVED): {violations}"


class TestNonAggregableMetricsExist:
    """Key unique-person metrics should be classified as NON_AGGREGABLE."""

    def test_reach_is_non_aggregable(self):
        assert "reach" in METRIC_CATALOG
        assert METRIC_CATALOG["reach"].aggregation == AggregationType.NON_AGGREGABLE

    def test_users_is_non_aggregable(self):
        assert "users" in METRIC_CATALOG
        assert METRIC_CATALOG["users"].aggregation == AggregationType.NON_AGGREGABLE

    def test_frequency_is_non_aggregable(self):
        assert "frequency" in METRIC_CATALOG
        assert METRIC_CATALOG["frequency"].aggregation == AggregationType.NON_AGGREGABLE

    def test_non_aggregable_have_is_unique_or_not(self):
        """NON_AGGREGABLE metrics should not have weight_metric set."""
        for name, defn in METRIC_CATALOG.items():
            if defn.aggregation == AggregationType.NON_AGGREGABLE:
                assert defn.weight_metric is None, (
                    f"{name} is NON_AGGREGABLE but has weight_metric='{defn.weight_metric}'"
                )


class TestSnapshotMetricsExist:
    """Key state-based metrics should be classified as SNAPSHOT."""

    def test_active_subscribers_is_snapshot(self):
        assert "active_subscribers" in METRIC_CATALOG
        assert METRIC_CATALOG["active_subscribers"].aggregation == AggregationType.SNAPSHOT

    def test_top_pages_is_snapshot(self):
        assert "top_pages" in METRIC_CATALOG
        assert METRIC_CATALOG["top_pages"].aggregation == AggregationType.SNAPSHOT

    def test_ig_followers_count_is_snapshot(self):
        assert "ig_followers_count" in METRIC_CATALOG
        assert METRIC_CATALOG["ig_followers_count"].aggregation == AggregationType.SNAPSHOT

    def test_snapshot_count(self):
        """There should be several SNAPSHOT metrics."""
        snapshots = [d for d in METRIC_CATALOG.values() if d.aggregation == AggregationType.SNAPSHOT]
        assert len(snapshots) >= 5, f"Expected >= 5 SNAPSHOT metrics, found {len(snapshots)}"


class TestWeightedAverageIntegrity:
    """WEIGHTED_AVERAGE metrics must reference valid weight metrics."""

    def test_all_have_weight_metric(self):
        for name, defn in METRIC_CATALOG.items():
            if defn.aggregation == AggregationType.WEIGHTED_AVERAGE:
                assert defn.weight_metric is not None, f"{name} is WEIGHTED_AVERAGE but has no weight_metric"

    def test_weight_metrics_exist_in_catalog(self):
        for name, defn in METRIC_CATALOG.items():
            if defn.aggregation == AggregationType.WEIGHTED_AVERAGE and defn.weight_metric:
                assert defn.weight_metric in METRIC_CATALOG, (
                    f"{name}.weight_metric '{defn.weight_metric}' not found in catalog"
                )

    def test_weight_metrics_are_additive(self):
        for name, defn in METRIC_CATALOG.items():
            if defn.aggregation == AggregationType.WEIGHTED_AVERAGE and defn.weight_metric:
                wm = METRIC_CATALOG[defn.weight_metric]
                assert wm.aggregation == AggregationType.ADDITIVE, (
                    f"{name}.weight_metric '{defn.weight_metric}' has aggregation {wm.aggregation}, expected ADDITIVE"
                )


class TestDerivedIntegrity:
    """DERIVED metrics must have formula and valid component references."""

    def test_all_have_formula(self):
        for name, defn in METRIC_CATALOG.items():
            if defn.aggregation == AggregationType.DERIVED:
                assert defn.formula is not None, f"{name} is DERIVED but has no formula"

    def test_formula_components_exist_in_catalog(self):
        for name, defn in METRIC_CATALOG.items():
            if defn.aggregation == AggregationType.DERIVED:
                for comp in defn.formula_components:
                    assert comp in METRIC_CATALOG, f"{name}.formula_components includes '{comp}' not in catalog"


class TestBenchmarksField:
    """Benchmarks field must be well-formed and have minimum coverage."""

    def test_benchmarks_field_type(self):
        """benchmarks must be None or a non-empty string."""
        for name, defn in METRIC_CATALOG.items():
            if defn.benchmarks is not None:
                assert isinstance(defn.benchmarks, str), f"{name}.benchmarks is {type(defn.benchmarks)}, expected str"
                assert len(defn.benchmarks.strip()) > 0, f"{name}.benchmarks is an empty string"

    def test_minimum_benchmark_coverage(self):
        """At least 40 metrics must have benchmarks populated (ratchet)."""
        with_benchmarks = [name for name, defn in METRIC_CATALOG.items() if defn.benchmarks is not None]
        assert len(with_benchmarks) >= 40, (
            f"Only {len(with_benchmarks)} metrics have benchmarks, expected >= 40. "
            f"Missing benchmarks is OK for niche metrics, but core metrics need them."
        )
