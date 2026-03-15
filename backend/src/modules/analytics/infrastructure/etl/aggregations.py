"""ETL aggregations — computes rollup metrics for dashboard performance.

Pre-computes daily, weekly, monthly, and last_30_days aggregations
so dashboard queries hit pre-computed data instead of scanning official_metrics.
"""

import logging
from collections import defaultdict
from datetime import date, timedelta
from typing import Dict, List, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


def compute_aggregations(
    official_rows: List[Dict],
    tenant_id: UUID,
    weekly_cutoff_day: int = 0,
    extraction_run_id: Optional[UUID] = None,
) -> List[Dict]:
    """Compute daily, weekly, monthly, and last_30_days aggregations.

    Args:
        official_rows: List of dicts from transform_staging_to_official().
        tenant_id: The tenant UUID.
        weekly_cutoff_day: ISO weekday for week start (0=Monday per user decision).
        extraction_run_id: UUID of the current extraction run.

    Returns:
        List of dicts ready for MetricAggregationModel bulk insert.
    """
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
        # Sort rows by date for period calculations
        sorted_rows = sorted(rows, key=lambda r: r["metric_date"])

        # Daily aggregations (one per unique date)
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

        # Weekly aggregations
        if sorted_rows:
            all_dates = sorted(daily_by_date.keys())
            weeks = _group_by_week(all_dates, daily_by_date, weekly_cutoff_day)
            for (ws, we), total in weeks.items():
                aggregations.append(_agg_dict(
                    tenant_id=tenant_id,
                    channel_slug=channel_slug,
                    metric_name=metric_name,
                    period_type="weekly",
                    period_start=ws,
                    period_end=we,
                    value=total,
                    unit=unit,
                    currency=currency,
                    cost_type=cost_type,
                    extraction_run_id=extraction_run_id,
                ))

        # Monthly aggregations
        if sorted_rows:
            months = _group_by_month(daily_by_date)
            for (ms, me), total in months.items():
                aggregations.append(_agg_dict(
                    tenant_id=tenant_id,
                    channel_slug=channel_slug,
                    metric_name=metric_name,
                    period_type="monthly",
                    period_start=ms,
                    period_end=me,
                    value=total,
                    unit=unit,
                    currency=currency,
                    cost_type=cost_type,
                    extraction_run_id=extraction_run_id,
                ))

        # Last 30 days aggregation
        if sorted_rows:
            total_30d = sum(daily_by_date.values())
            all_dates = sorted(daily_by_date.keys())
            aggregations.append(_agg_dict(
                tenant_id=tenant_id,
                channel_slug=channel_slug,
                metric_name=metric_name,
                period_type="last_30_days",
                period_start=all_dates[0],
                period_end=all_dates[-1],
                value=total_30d,
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
    cutoff_day: int,
) -> Dict[tuple, float]:
    """Group daily values by ISO week."""
    weeks: Dict[tuple, float] = defaultdict(float)
    for d in dates:
        # Find the week start (cutoff_day: 0=Monday)
        days_since_cutoff = (d.weekday() - cutoff_day) % 7
        week_start = d - timedelta(days=days_since_cutoff)
        week_end = week_start + timedelta(days=6)
        weeks[(week_start, week_end)] += daily_values[d]
    return dict(weeks)


def _group_by_month(
    daily_values: Dict[date, float],
) -> Dict[tuple, float]:
    """Group daily values by calendar month."""
    months: Dict[tuple, float] = defaultdict(float)
    for d, val in daily_values.items():
        month_start = d.replace(day=1)
        # Last day of month
        if d.month == 12:
            month_end = d.replace(month=12, day=31)
        else:
            month_end = d.replace(month=d.month + 1, day=1) - timedelta(days=1)
        months[(month_start, month_end)] += val
    return dict(months)
