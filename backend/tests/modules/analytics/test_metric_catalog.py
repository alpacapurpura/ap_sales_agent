"""Tests for the Metric Catalog — validates semantic integrity of METRIC_CATALOG.

These are pure Python unit tests: no DB, no async, no mocking required.
"""

from src.modules.analytics.domain.enums import AggregationType
from src.modules.analytics.domain.metric_catalog import (
    METRIC_CATALOG,
    get_metric_def,
    is_additive,
)


def test_all_metrics_have_valid_aggregation_type():
    """Every metric in METRIC_CATALOG has a valid AggregationType."""
    for name, defn in METRIC_CATALOG.items():
        assert isinstance(defn.aggregation, AggregationType), (
            f"{name} has invalid aggregation: {defn.aggregation!r}"
        )


def test_weighted_average_weight_metrics_are_additive():
    """Every WEIGHTED_AVERAGE metric's weight_metric must exist in catalog and be ADDITIVE."""
    for name, defn in METRIC_CATALOG.items():
        if defn.aggregation == AggregationType.WEIGHTED_AVERAGE:
            assert defn.weight_metric is not None, (
                f"{name} is WEIGHTED_AVERAGE but has no weight_metric"
            )
            wm = METRIC_CATALOG.get(defn.weight_metric)
            assert wm is not None, (
                f"{name}.weight_metric '{defn.weight_metric}' not in catalog"
            )
            assert wm.aggregation == AggregationType.ADDITIVE, (
                f"{name}.weight_metric '{defn.weight_metric}' must be ADDITIVE, "
                f"got {wm.aggregation}"
            )


def test_derived_formula_components_exist_in_catalog():
    """Every DERIVED metric's formula_components must reference metrics that exist in catalog."""
    for name, defn in METRIC_CATALOG.items():
        if defn.aggregation == AggregationType.DERIVED:
            assert defn.formula is not None, f"{name} is DERIVED but has no formula"
            for component in defn.formula_components:
                assert component in METRIC_CATALOG, (
                    f"{name}.formula_components includes '{component}' "
                    f"which is not in catalog"
                )


def test_non_aggregable_have_no_aggregation_params():
    """NON_AGGREGABLE metrics must not have weight_metric or formula_components."""
    for name, defn in METRIC_CATALOG.items():
        if defn.aggregation == AggregationType.NON_AGGREGABLE:
            assert defn.weight_metric is None, (
                f"{name} is NON_AGGREGABLE but has weight_metric='{defn.weight_metric}'"
            )


def test_is_additive_helper():
    """is_additive() correctly identifies additive vs non-additive metrics."""
    assert is_additive("clicks") is True
    assert is_additive("reach") is False
    assert is_additive("ctr") is False
    assert is_additive("nonexistent_metric") is False


def test_get_metric_def_helper():
    """get_metric_def() returns the correct definition or None for unknowns."""
    defn = get_metric_def("spend")
    assert defn is not None
    assert defn.name == "spend"
    assert defn.aggregation == AggregationType.ADDITIVE
    assert get_metric_def("nonexistent") is None


def test_key_metric_classifications():
    """Spot-check that key metrics have the correct aggregation type."""
    # NON_AGGREGABLE (personas únicas — no summable cross-day)
    assert METRIC_CATALOG["reach"].aggregation == AggregationType.NON_AGGREGABLE
    assert METRIC_CATALOG["users"].aggregation == AggregationType.NON_AGGREGABLE
    assert METRIC_CATALOG["frequency"].aggregation == AggregationType.NON_AGGREGABLE

    # ADDITIVE
    assert METRIC_CATALOG["clicks"].aggregation == AggregationType.ADDITIVE
    assert METRIC_CATALOG["sessions"].aggregation == AggregationType.ADDITIVE
    assert METRIC_CATALOG["revenue"].aggregation == AggregationType.ADDITIVE

    # WEIGHTED_AVERAGE
    assert METRIC_CATALOG["bounceRate"].aggregation == AggregationType.WEIGHTED_AVERAGE
    assert METRIC_CATALOG["ctr"].aggregation == AggregationType.WEIGHTED_AVERAGE
    assert METRIC_CATALOG["open_rate"].aggregation == AggregationType.WEIGHTED_AVERAGE

    # DERIVED
    assert METRIC_CATALOG["cpc"].aggregation == AggregationType.DERIVED
    assert METRIC_CATALOG["avg_order_value"].aggregation == AggregationType.DERIVED

    # SNAPSHOT
    assert METRIC_CATALOG["active_subscribers"].aggregation == AggregationType.SNAPSHOT


def test_compute_channel_totals_excludes_non_additive():
    """compute_channel_totals must NEVER include NON_AGGREGABLE, WEIGHTED_AVERAGE, or DERIVED metrics."""
    from src.modules.analytics.application.services.aggregation_helpers import compute_channel_totals
    from src.modules.analytics.application.dto.attraction_dto import ChannelMetricDTO, MetricValueDTO

    channels = [
        ChannelMetricDTO(
            slug="meta-ads",
            name="Meta Ads",
            channel_type="paid",
            connected=True,
            source_label="Meta",
            metrics=[
                MetricValueDTO(name="impressions", value=10000),  # ADDITIVE → include
                MetricValueDTO(name="clicks", value=500),          # ADDITIVE → include
                MetricValueDTO(name="spend", value=750, unit="currency"),  # ADDITIVE → include
                MetricValueDTO(name="reach", value=8000),          # NON_AGGREGABLE → exclude
                MetricValueDTO(name="ctr", value=0.05, unit="percentage"),  # WEIGHTED_AVERAGE → exclude
                MetricValueDTO(name="cpc", value=1.5, unit="currency"),     # DERIVED → exclude
            ],
        ),
    ]

    totals = compute_channel_totals(channels)

    assert totals["impressions"] == 10000
    assert totals["clicks"] == 500
    assert totals["spend"] == 750
    assert "reach" not in totals, "reach is NON_AGGREGABLE and must not appear in totals"
    assert "ctr" not in totals, "ctr is WEIGHTED_AVERAGE and must not appear in totals"
    assert "cpc" not in totals, "cpc is DERIVED and must not appear in totals"


def test_no_duplicate_metric_names():
    """METRIC_CATALOG is built from a list — verify no name appears twice."""
    from src.modules.analytics.domain.metric_catalog import (
        _ADDITIVE,
        _DERIVED,
        _NON_AGGREGABLE,
        _SNAPSHOT,
        _WEIGHTED_AVERAGE,
    )

    all_metrics = [*_ADDITIVE, *_WEIGHTED_AVERAGE, *_DERIVED, *_NON_AGGREGABLE, *_SNAPSHOT]
    names = [m.name for m in all_metrics]
    duplicates = [name for name in set(names) if names.count(name) > 1]
    assert not duplicates, f"Duplicate metric names found: {set(duplicates)}"
