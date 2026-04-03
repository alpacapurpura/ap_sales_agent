"""ETL aggregations — computes rollup metrics for dashboard performance.

Pre-computes daily, weekly, monthly, and last_30_days aggregations
so dashboard queries hit pre-computed data instead of scanning official_metrics.

Aggregation strategy by metric type (from METRIC_CATALOG):
- ADDITIVE:          SUM across days (clicks, spend, sessions)
- WEIGHTED_AVERAGE:  Daily only — multi-period computed in service layer
- DERIVED:           Daily only — multi-period computed from components in service layer
- NON_AGGREGABLE:    Daily only — persons unique, cannot sum cross-day (reach, users)
- SNAPSHOT:          Last value in period (active_subscribers)
- Unknown:           SUM with warning (backward compatibility)
"""

import structlog
from collections import defaultdict
from datetime import date, timedelta
from typing import Dict, List, Optional
from uuid import UUID

from src.modules.analytics.domain.enums import AggregationType
from src.modules.analytics.domain.metric_catalog import get_metric_def
from src.modules.analytics.domain.period_config import TenantPeriodConfig

logger = structlog.get_logger(__name__)


def compute_aggregations(
    official_rows: List[Dict],
    tenant_id: UUID,
    weekly_cutoff_day: int = 0,
    extraction_run_id: Optional[UUID] = None,
    period_config: Optional[TenantPeriodConfig] = None,
) -> List[Dict]:
    """Compute daily, weekly, monthly, quarterly, and last_30_days aggregations.

    Uses METRIC_CATALOG to determine the correct aggregation strategy per metric.
    NON_AGGREGABLE, WEIGHTED_AVERAGE, and DERIVED metrics only get daily records.
    SNAPSHOT metrics use the last value in each period instead of SUM.

    Args:
        official_rows: List of dicts from transform_staging_to_official().
        tenant_id: The tenant UUID.
        weekly_cutoff_day: ISO weekday for week start (0=Monday per user decision).
            Deprecated — use period_config instead.
        extraction_run_id: UUID of the current extraction run.
        period_config: Tenant period configuration. If None, uses default config.

    Returns:
        List of dicts ready for MetricAggregationModel bulk insert.
    """
    if period_config is None:
        period_config = TenantPeriodConfig(weekly_start_day=weekly_cutoff_day)
    if not official_rows:
        return []

    aggregations = []

    # Group by (channel_slug, metric_name, unit, currency, cost_type)
    groups: Dict[tuple, List[Dict]] = defaultdict(list)
    for row in official_rows:
        key = (
            row["channel_slug"],
            row["metric_name"],
            row["unit"],
            row.get("currency"),
            row.get("cost_type"),
        )
        groups[key].append(row)

    for (channel_slug, metric_name, unit, currency, cost_type), rows in groups.items():
        sorted_rows = sorted(rows, key=lambda r: r["metric_date"])

        # Look up metric in catalog to determine aggregation strategy
        defn = get_metric_def(metric_name)
        if defn is None:
            logger.warning(
                "Metric '%s' not in METRIC_CATALOG — using SUM (backward compat). "
                "Add to metric_catalog.py to fix.",
                metric_name,
            )
            agg_type = AggregationType.ADDITIVE
        else:
            agg_type = defn.aggregation

        # Daily aggregations (always compute — intra-day SUM is always correct)
        daily_by_date: Dict[date, float] = defaultdict(float)
        for row in sorted_rows:
            metric_date = row["metric_date"]
            if isinstance(metric_date, str):
                metric_date = date.fromisoformat(metric_date)
            daily_by_date[metric_date] += row["value"]

        for d, total in daily_by_date.items():
            aggregations.append(_agg_dict(
                tenant_id=tenant_id,
                channel_slug=channel_slug,
                metric_name=metric_name,
                period_type="daily",
                period_start=d,
                period_end=d,
                value=total,
                unit=unit,
                currency=currency,
                cost_type=cost_type,
                extraction_run_id=extraction_run_id,
            ))

        # Multi-period aggregations: only for ADDITIVE and SNAPSHOT.
        # NON_AGGREGABLE, WEIGHTED_AVERAGE, DERIVED: skip (computed elsewhere or unsafe).
        if agg_type not in (AggregationType.ADDITIVE, AggregationType.SNAPSHOT):
            continue

        if not sorted_rows:
            continue

        all_dates = sorted(daily_by_date.keys())

        def _aggregate_period(period_values: Dict[date, float]) -> float:
            """Aggregate values for a period based on metric type."""
            if agg_type == AggregationType.SNAPSHOT:
                # Last value in the period (snapshot = state, not flow)
                last_date = max(period_values.keys())
                return period_values[last_date]
            # ADDITIVE: SUM
            return sum(period_values.values())

        # Weekly aggregations
        weeks = _group_by_week(all_dates, daily_by_date, period_config)
        for (ws, we), week_daily in weeks.items():
            aggregations.append(_agg_dict(
                tenant_id=tenant_id,
                channel_slug=channel_slug,
                metric_name=metric_name,
                period_type="weekly",
                period_start=ws,
                period_end=we,
                value=_aggregate_period(week_daily),
                unit=unit,
                currency=currency,
                cost_type=cost_type,
                extraction_run_id=extraction_run_id,
            ))

        # Monthly aggregations
        months = _group_by_month(daily_by_date)
        for (ms, me), month_daily in months.items():
            aggregations.append(_agg_dict(
                tenant_id=tenant_id,
                channel_slug=channel_slug,
                metric_name=metric_name,
                period_type="monthly",
                period_start=ms,
                period_end=me,
                value=_aggregate_period(month_daily),
                unit=unit,
                currency=currency,
                cost_type=cost_type,
                extraction_run_id=extraction_run_id,
            ))

        # Quarterly aggregations
        quarters = _group_by_quarter(daily_by_date, period_config)
        for (qs, qe), quarter_daily in quarters.items():
            aggregations.append(_agg_dict(
                tenant_id=tenant_id,
                channel_slug=channel_slug,
                metric_name=metric_name,
                period_type="quarterly",
                period_start=qs,
                period_end=qe,
                value=_aggregate_period(quarter_daily),
                unit=unit,
                currency=currency,
                cost_type=cost_type,
                extraction_run_id=extraction_run_id,
            ))

        # Last 30 days aggregation
        aggregations.append(_agg_dict(
            tenant_id=tenant_id,
            channel_slug=channel_slug,
            metric_name=metric_name,
            period_type="last_30_days",
            period_start=all_dates[0],
            period_end=all_dates[-1],
            value=_aggregate_period(daily_by_date),
            unit=unit,
            currency=currency,
            cost_type=cost_type,
            extraction_run_id=extraction_run_id,
        ))

    logger.info(
        "Computed %d aggregation records for tenant %s",
        len(aggregations),
        tenant_id,
    )
    return aggregations


def _agg_dict(**kwargs) -> Dict:
    """Build a dict matching MetricAggregationModel columns."""
    return kwargs


def _group_by_week(
    dates: List[date],
    daily_values: Dict[date, float],
    period_config: TenantPeriodConfig,
) -> Dict[tuple, Dict[date, float]]:
    """Group daily values by week using tenant-specific week start day.

    Returns dict of (week_start, week_end) -> {date: value} for that week.
    """
    weeks: Dict[tuple, Dict[date, float]] = defaultdict(dict)
    for d in dates:
        ws, we = period_config.get_week_boundaries(d)
        weeks[(ws, we)][d] = daily_values[d]
    return dict(weeks)


def _group_by_month(
    daily_values: Dict[date, float],
) -> Dict[tuple, Dict[date, float]]:
    """Group daily values by calendar month.

    Returns dict of (month_start, month_end) -> {date: value} for that month.
    """
    months: Dict[tuple, Dict[date, float]] = defaultdict(dict)
    for d, val in daily_values.items():
        month_start = d.replace(day=1)
        if d.month == 12:
            month_end = d.replace(month=12, day=31)
        else:
            month_end = d.replace(month=d.month + 1, day=1) - timedelta(days=1)
        months[(month_start, month_end)][d] = val
    return dict(months)


def _group_by_quarter(
    daily_values: Dict[date, float],
    period_config: TenantPeriodConfig,
) -> Dict[tuple, Dict[date, float]]:
    """Group daily values by quarter using tenant fiscal year config.

    Returns dict of (quarter_start, quarter_end) -> {date: value}.
    """
    quarters: Dict[tuple, Dict[date, float]] = defaultdict(dict)
    for d, val in daily_values.items():
        qs, qe = period_config.get_quarter_boundaries(d)
        quarters[(qs, qe)][d] = val
    return dict(quarters)
