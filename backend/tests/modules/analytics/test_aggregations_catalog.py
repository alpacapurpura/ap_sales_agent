"""Tests for catalog-aware aggregation behavior."""

from datetime import date
from uuid import uuid4

from src.modules.analytics.infrastructure.etl.aggregations import compute_aggregations

TENANT = uuid4()


def _row(channel, metric, value, d, unit="count"):
    return {
        "channel_slug": channel,
        "metric_name": metric,
        "value": value,
        "metric_date": d,
        "unit": unit,
        "currency": None,
        "cost_type": None,
    }


def test_additive_metric_sums_correctly():
    """ADDITIVE: clicks across 3 days should sum to 600."""
    rows = [
        _row("meta-ads", "clicks", 100, date(2026, 1, 1)),
        _row("meta-ads", "clicks", 200, date(2026, 1, 2)),
        _row("meta-ads", "clicks", 300, date(2026, 1, 3)),
    ]
    result = compute_aggregations(rows, TENANT)
    weekly = [r for r in result if r["period_type"] == "weekly"]
    assert len(weekly) == 1
    assert weekly[0]["value"] == 600.0


def test_non_aggregable_metric_only_has_daily():
    """NON_AGGREGABLE: reach should only generate daily records, no weekly/monthly."""
    rows = [
        _row("ig-organic", "reach", 1000, date(2026, 1, 1)),
        _row("ig-organic", "reach", 1200, date(2026, 1, 2)),
        _row("ig-organic", "reach", 900, date(2026, 1, 8)),  # next week
    ]
    result = compute_aggregations(rows, TENANT)
    daily = [r for r in result if r["period_type"] == "daily"]
    weekly = [r for r in result if r["period_type"] == "weekly"]
    monthly = [r for r in result if r["period_type"] == "monthly"]
    last_30d = [r for r in result if r["period_type"] == "last_30_days"]
    assert len(daily) == 3
    assert len(weekly) == 0
    assert len(monthly) == 0
    assert len(last_30d) == 0


def test_weighted_average_metric_only_has_daily():
    """WEIGHTED_AVERAGE: bounceRate should only generate daily records."""
    rows = [
        _row("google-organic", "bounceRate", 0.5, date(2026, 1, 1), unit="percentage"),
        _row("google-organic", "bounceRate", 0.3, date(2026, 1, 2), unit="percentage"),
    ]
    result = compute_aggregations(rows, TENANT)
    weekly = [r for r in result if r["period_type"] == "weekly"]
    assert len(weekly) == 0


def test_derived_metric_only_has_daily():
    """DERIVED: cpc should only generate daily records."""
    rows = [
        _row("google-ads", "cpc", 1.5, date(2026, 1, 1), unit="currency"),
        _row("google-ads", "cpc", 2.0, date(2026, 1, 2), unit="currency"),
    ]
    result = compute_aggregations(rows, TENANT)
    weekly = [r for r in result if r["period_type"] == "weekly"]
    assert len(weekly) == 0


def test_snapshot_metric_uses_last_value():
    """SNAPSHOT: active_subscribers weekly should be the last value, not sum.

    Dates 2026-06-01 (Mon), 2026-06-03 (Wed), 2026-06-05 (Fri) all fall in the
    same ISO week (week starting Monday 2026-06-01), so there is exactly 1 weekly record.
    """
    rows = [
        _row("email-capture", "active_subscribers", 1000, date(2026, 6, 1)),
        _row("email-capture", "active_subscribers", 1050, date(2026, 6, 3)),
        _row("email-capture", "active_subscribers", 1100, date(2026, 6, 5)),
    ]
    result = compute_aggregations(rows, TENANT)
    weekly = [r for r in result if r["period_type"] == "weekly"]
    assert len(weekly) == 1
    assert weekly[0]["value"] == 1100.0  # last value, NOT 3150 (sum)
