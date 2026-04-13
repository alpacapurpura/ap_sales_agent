"""MetricResolver — pure domain class for correct metric aggregation.

Fixes three interrelated bugs in the channel dashboard:
1. Double-counting: filters to account-level rows only (campaign_id=None)
2. DERIVED/WEIGHTED_AVG period KPIs: recalculates from component sums
3. Alias mapping: bridges hero_metrics names to catalog canonical names

This is a pure Python domain class with no SQLAlchemy or FastAPI imports.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import date

from src.modules.analytics.domain.enums import AggregationType
from src.modules.analytics.domain.metric_catalog import MetricDefinition, get_metric_def

# ---------------------------------------------------------------------------
# Alias map: hero_metrics names → metric_catalog canonical names
# ---------------------------------------------------------------------------

ALIAS_MAP: dict[str, str] = {
    "ROAS": "meta_purchase_roas",
    "CPA": "meta_cost_per_purchase",
    "CPL": "meta_cost_per_lead",
    "CTR": "ctr",
    "CPC": "cpc",
    "CPM": "cpm",
}

# Type alias for raw daily rows from the repository
RawDailyRow = tuple[date, str, float, str | None, str | None, str | None]


def _extract_multiplier(formula: str | None) -> float:
    """Extract trailing multiplier from a formula string.

    Examples:
        "clicks / impressions x 100" → 100.0
        "spend / impressions x 1000" → 1000.0
        "spend / clicks" → 1.0
        "meta_conversion_value / spend" → 1.0
    """
    if not formula:
        return 1.0
    # Match multiplication sign (unicode or ascii) followed by number at end of formula
    match = re.search(r"[\u00d7*]\s*(\d+(?:\.\d+)?)\s*$", formula)
    if match:
        return float(match.group(1))
    return 1.0


def _get_formula_components(
    defn: MetricDefinition,
) -> tuple[str, str] | None:
    """Extract (numerator, denominator) from a metric definition.

    For DERIVED metrics: uses formula_components directly (numerator, denominator).
    For WEIGHTED_AVERAGE metrics: parses the formula to find numerator and denominator.
    """
    if defn.aggregation == AggregationType.DERIVED:
        if len(defn.formula_components) >= 2:
            return (defn.formula_components[0], defn.formula_components[1])
        return None

    if defn.aggregation == AggregationType.WEIGHTED_AVERAGE:
        # For weighted averages the formula follows "numerator / denominator [* multiplier]"
        # where weight_metric is the denominator
        if defn.formula and defn.weight_metric:
            # Parse "clicks / impressions * 100" to extract numerator="clicks"
            parts = defn.formula.split("/")
            if len(parts) >= 2:
                numerator = parts[0].strip()
                return (numerator, defn.weight_metric)
        return None

    return None


class MetricResolver:
    """Pure domain resolver for metric aggregation with correct semantics.

    Handles:
    - Account-level filtering (excludes campaign/ad_set/ad rows)
    - ADDITIVE: SUM across period
    - DERIVED: recalculate from component sums (e.g., CPC = SUM(spend)/SUM(clicks))
    - WEIGHTED_AVERAGE: recalculate from formula (e.g., CTR = SUM(clicks)/SUM(impressions)*100)
    - NON_AGGREGABLE: latest date's value
    - SNAPSHOT: latest date's value
    """

    def resolve_alias(self, name: str) -> str:
        """Resolve a metric alias to its canonical catalog name."""
        return ALIAS_MAP.get(name, name)

    def resolve_period_kpis(
        self,
        daily_rows: list[RawDailyRow],
        requested_metrics: list[str],
    ) -> dict[str, float | None]:
        """Resolve period-level KPI values from raw daily rows.

        Args:
            daily_rows: Raw rows (date, metric_name, value, campaign_id, ad_set_id, ad_id)
            requested_metrics: Metric names (may include aliases like "ROAS", "CTR")

        Returns:
            Dict mapping requested metric name → aggregated value (or None if not computable)
        """
        # Step 1: Filter to account-level only
        account_rows = self._filter_account_level(daily_rows)

        # Step 2: Group by metric_name → list of (date, value)
        grouped = self._group_by_metric(account_rows)

        # Step 3: Resolve each requested metric
        result: dict[str, float | None] = {}
        for requested_name in requested_metrics:
            canonical = self.resolve_alias(requested_name)
            defn = get_metric_def(canonical)

            if defn is None:
                # Unknown metric — try direct lookup in grouped data
                entries = grouped.get(canonical, [])
                if entries:
                    result[requested_name] = sum(v for _, v in entries)
                else:
                    result[requested_name] = None
                continue

            value = self._aggregate_metric(defn, grouped)
            result[requested_name] = value

        return result

    def resolve_daily_timeseries(
        self,
        daily_rows: list[RawDailyRow],
        requested_metrics: list[str],
    ) -> dict[str, list[tuple[date, float]]]:
        """Resolve daily time series values from raw daily rows.

        For ADDITIVE/NON_AGGREGABLE: returns raw daily values.
        For DERIVED/WEIGHTED_AVERAGE: recalculates per-day from component values.

        Args:
            daily_rows: Raw rows (date, metric_name, value, campaign_id, ad_set_id, ad_id)
            requested_metrics: Metric names (may include aliases)

        Returns:
            Dict mapping requested metric name → sorted list of (date, value) tuples
        """
        # Step 1: Filter to account-level only
        account_rows = self._filter_account_level(daily_rows)

        # Step 2: Group by metric_name → {date → value}
        daily_by_metric: dict[str, dict[date, float]] = defaultdict(dict)
        for d, metric_name, value, *_ in account_rows:
            daily_by_metric[metric_name][d] = value

        # Step 3: Build time series for each requested metric
        result: dict[str, list[tuple[date, float]]] = {}
        for requested_name in requested_metrics:
            canonical = self.resolve_alias(requested_name)
            defn = get_metric_def(canonical)

            if defn is None:
                # Unknown metric — return raw values if available
                daily_vals = daily_by_metric.get(canonical, {})
                result[requested_name] = sorted(daily_vals.items())
                continue

            if defn.aggregation in (
                AggregationType.ADDITIVE,
                AggregationType.NON_AGGREGABLE,
                AggregationType.SNAPSHOT,
            ):
                daily_vals = daily_by_metric.get(canonical, {})
                result[requested_name] = sorted(daily_vals.items())

            elif defn.aggregation in (
                AggregationType.DERIVED,
                AggregationType.WEIGHTED_AVERAGE,
            ):
                components = _get_formula_components(defn)
                if components is None:
                    # Cannot recalculate — fall back to raw stored values
                    daily_vals = daily_by_metric.get(canonical, {})
                    result[requested_name] = sorted(daily_vals.items())
                    continue

                numerator_name, denominator_name = components
                multiplier = _extract_multiplier(defn.formula)

                numerator_daily = daily_by_metric.get(numerator_name, {})
                denominator_daily = daily_by_metric.get(denominator_name, {})

                # Get all dates where both components exist
                common_dates = sorted(
                    set(numerator_daily.keys()) & set(denominator_daily.keys()),
                )

                series: list[tuple[date, float]] = []
                for d in common_dates:
                    denom = denominator_daily[d]
                    if denom == 0:
                        continue  # Skip days with zero denominator
                    value = (numerator_daily[d] / denom) * multiplier
                    series.append((d, value))

                result[requested_name] = series
            else:
                # Fallback
                daily_vals = daily_by_metric.get(canonical, {})
                result[requested_name] = sorted(daily_vals.items())

        return result

    def resolve_from_aggregated(
        self,
        aggregated: dict[str, float],
        requested_metrics: list[str],
    ) -> dict[str, float | None]:
        """Resolve metric values from a pre-aggregated dict.

        Used by ChannelDashboardService when raw daily rows are not available.
        The input dict comes from get_channel_metrics_for_period() which already
        aggregated values by metric name (SUM for additive, latest for others).

        For each requested metric:
        1. Resolve alias (e.g., ROAS → meta_purchase_roas)
        2. If DERIVED/WEIGHTED_AVERAGE: recalculate from component sums in dict
        3. Otherwise: look up the canonical name directly in the dict

        This does NOT mutate the input dict.

        Args:
            aggregated: Pre-aggregated {metric_name: value} from repository
            requested_metrics: Metric names (may include aliases)

        Returns:
            Dict mapping requested metric name → resolved value (or None)
        """
        result: dict[str, float | None] = {}

        for requested_name in requested_metrics:
            canonical = self.resolve_alias(requested_name)
            defn = get_metric_def(canonical)

            if defn is None:
                # Unknown metric — direct lookup
                val = aggregated.get(canonical)
                result[requested_name] = val
                continue

            if defn.aggregation in (
                AggregationType.DERIVED,
                AggregationType.WEIGHTED_AVERAGE,
            ):
                # Recalculate from components
                value = self._recalculate_from_aggregated(defn, aggregated)
                result[requested_name] = value
            else:
                # ADDITIVE, NON_AGGREGABLE, SNAPSHOT: use existing value
                val = aggregated.get(canonical)
                result[requested_name] = val

        return result

    def _recalculate_from_aggregated(
        self,
        defn: MetricDefinition,
        aggregated: dict[str, float],
    ) -> float | None:
        """Recalculate a derived/weighted metric from pre-aggregated component values.

        Falls back to the stored value in the dict if components are missing.
        """
        components = _get_formula_components(defn)
        if components is None:
            # No formula info — try direct lookup
            return aggregated.get(defn.name)

        numerator_name, denominator_name = components
        multiplier = _extract_multiplier(defn.formula)

        numerator_val = aggregated.get(numerator_name)
        denominator_val = aggregated.get(denominator_name)

        if numerator_val is None or denominator_val is None:
            # Components not available — fall back to stored value
            return aggregated.get(defn.name)

        if denominator_val == 0:
            return None

        return (numerator_val / denominator_val) * multiplier

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _filter_account_level(
        rows: list[RawDailyRow],
    ) -> list[RawDailyRow]:
        """Keep only account-level rows (campaign_id, ad_set_id, ad_id all None)."""
        return [
            row for row in rows if row[3] is None and row[4] is None and row[5] is None
        ]

    @staticmethod
    def _group_by_metric(
        rows: list[RawDailyRow],
    ) -> dict[str, list[tuple[date, float]]]:
        """Group rows by metric_name → list of (date, value)."""
        grouped: dict[str, list[tuple[date, float]]] = defaultdict(list)
        for d, metric_name, value, *_ in rows:
            grouped[metric_name].append((d, value))
        return grouped

    def _aggregate_metric(
        self,
        defn: MetricDefinition,
        grouped: dict[str, list[tuple[date, float]]],
    ) -> float | None:
        """Aggregate a single metric according to its AggregationType."""
        if defn.aggregation in (
            AggregationType.DERIVED,
            AggregationType.WEIGHTED_AVERAGE,
        ):
            return self._recalculate_from_components(defn, grouped)

        entries = grouped.get(defn.name, [])
        if not entries:
            return None

        if defn.aggregation in (
            AggregationType.NON_AGGREGABLE,
            AggregationType.SNAPSHOT,
        ):
            return max(entries, key=lambda x: x[0])[1]

        # ADDITIVE or unknown — sum as fallback
        return sum(v for _, v in entries)

    def _recalculate_from_components(
        self,
        defn: MetricDefinition,
        grouped: dict[str, list[tuple[date, float]]],
    ) -> float | None:
        """Recalculate a derived/weighted metric from its component sums."""
        components = _get_formula_components(defn)
        if components is None:
            # No formula info — fall back to latest value
            entries = grouped.get(defn.name, [])
            if entries:
                latest = max(entries, key=lambda x: x[0])
                return latest[1]
            return None

        numerator_name, denominator_name = components
        multiplier = _extract_multiplier(defn.formula)

        numerator_entries = grouped.get(numerator_name, [])
        denominator_entries = grouped.get(denominator_name, [])

        if not numerator_entries or not denominator_entries:
            return None

        numerator_sum = sum(v for _, v in numerator_entries)
        denominator_sum = sum(v for _, v in denominator_entries)

        if denominator_sum == 0:
            return None

        return (numerator_sum / denominator_sum) * multiplier
