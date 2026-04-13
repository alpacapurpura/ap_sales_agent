"""Tests for ETL aggregation logic — validates compute_aggregations behavior.

Tests cover:
- ADDITIVE metrics SUM across days into weekly/monthly rollups
- NON_AGGREGABLE metrics are excluded from multi-period rollups (daily only)
- SNAPSHOT metrics use last value in each period
- Empty input returns empty output
- Grouping by (channel_slug, metric_name) is correct
"""

import uuid
from datetime import date

from src.modules.analytics.domain.period_config import TenantPeriodConfig
from src.modules.analytics.infrastructure.etl.aggregations import compute_aggregations

TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


def _make_row(metric_name, value, metric_date, **overrides):
    """Build an official_metrics-shaped dict."""
    defaults = {
        "channel_slug": "meta-ads",
        "metric_name": metric_name,
        "value": value,
        "unit": "count",
        "currency": None,
        "cost_type": "investment",
        "metric_date": metric_date,
    }
    defaults.update(overrides)
    return defaults


class TestAdditiveAggregation:
    """ADDITIVE metrics should SUM across days into weekly/monthly/quarterly rollups."""

    def test_daily_aggregation_sums_same_day(self):
        """Multiple rows on same day → daily aggregation sums them."""
        rows = [
            _make_row("impressions", 500, date(2026, 3, 5)),
            _make_row("impressions", 300, date(2026, 3, 5)),
        ]
        result = compute_aggregations(rows, TENANT_ID)

        daily_records = [r for r in result if r["period_type"] == "daily"]
        assert len(daily_records) == 1
        assert daily_records[0]["value"] == 800

    def test_weekly_aggregation_sums_across_days(self):
        """ADDITIVE metric values across a week should be summed."""
        # 2026-03-02 (Mon) to 2026-03-06 (Fri) — same week
        rows = [
            _make_row("clicks", 100, date(2026, 3, 2)),
            _make_row("clicks", 150, date(2026, 3, 3)),
            _make_row("clicks", 200, date(2026, 3, 4)),
        ]
        result = compute_aggregations(rows, TENANT_ID)

        weekly = [r for r in result if r["period_type"] == "weekly"]
        assert len(weekly) == 1
        assert weekly[0]["value"] == 450

    def test_monthly_aggregation_sums_across_days(self):
        """ADDITIVE metric values within a month should be summed."""
        rows = [
            _make_row("spend", 100.0, date(2026, 3, 1), unit="currency"),
            _make_row("spend", 200.0, date(2026, 3, 15), unit="currency"),
            _make_row("spend", 300.0, date(2026, 3, 31), unit="currency"),
        ]
        result = compute_aggregations(rows, TENANT_ID)

        monthly = [r for r in result if r["period_type"] == "monthly"]
        assert len(monthly) == 1
        assert monthly[0]["value"] == 600.0

    def test_quarterly_aggregation_created(self):
        """ADDITIVE metric should produce quarterly aggregation records."""
        rows = [
            _make_row("sessions", 500, date(2026, 1, 15)),
            _make_row("sessions", 600, date(2026, 2, 15)),
            _make_row("sessions", 700, date(2026, 3, 15)),
        ]
        result = compute_aggregations(rows, TENANT_ID)

        quarterly = [r for r in result if r["period_type"] == "quarterly"]
        assert len(quarterly) == 1
        assert quarterly[0]["value"] == 1800

    def test_last_30_days_aggregation_created(self):
        """ADDITIVE metric should produce a last_30_days aggregation record."""
        rows = [
            _make_row("clicks", 100, date(2026, 3, 1)),
            _make_row("clicks", 200, date(2026, 3, 14)),
        ]
        result = compute_aggregations(rows, TENANT_ID)

        l30 = [r for r in result if r["period_type"] == "last_30_days"]
        assert len(l30) == 1
        assert l30[0]["value"] == 300


class TestNonAggregableExcluded:
    """NON_AGGREGABLE metrics should only have daily records, no multi-period rollups."""

    def test_reach_has_only_daily_records(self):
        """reach is NON_AGGREGABLE — should not have weekly/monthly/quarterly."""
        rows = [
            _make_row("reach", 5000, date(2026, 3, 2)),
            _make_row("reach", 6000, date(2026, 3, 3)),
            _make_row("reach", 4000, date(2026, 3, 4)),
        ]
        result = compute_aggregations(rows, TENANT_ID)

        period_types = {r["period_type"] for r in result}
        assert period_types == {"daily"}, f"NON_AGGREGABLE 'reach' should only have daily, got {period_types}"

    def test_users_has_only_daily_records(self):
        """users is NON_AGGREGABLE — should not produce multi-period rollups."""
        rows = [
            _make_row("users", 1000, date(2026, 3, 5)),
            _make_row("users", 1200, date(2026, 3, 6)),
        ]
        result = compute_aggregations(rows, TENANT_ID)

        period_types = {r["period_type"] for r in result}
        assert period_types == {"daily"}

    def test_daily_count_matches_input_days(self):
        """NON_AGGREGABLE daily records should match unique input dates."""
        rows = [
            _make_row("reach", 5000, date(2026, 3, 2)),
            _make_row("reach", 6000, date(2026, 3, 3)),
        ]
        result = compute_aggregations(rows, TENANT_ID)
        assert len(result) == 2


class TestSnapshotAggregation:
    """SNAPSHOT metrics should use the last value in each period."""

    def test_weekly_uses_last_value(self):
        """SNAPSHOT metric's weekly aggregation should use last day's value."""
        # 2026-03-02 (Mon) to 2026-03-06 (Fri) — same week
        rows = [
            _make_row("active_subscribers", 100, date(2026, 3, 2)),
            _make_row("active_subscribers", 150, date(2026, 3, 4)),
            _make_row("active_subscribers", 200, date(2026, 3, 6)),
        ]
        result = compute_aggregations(rows, TENANT_ID)

        weekly = [r for r in result if r["period_type"] == "weekly"]
        assert len(weekly) == 1
        # Last value in the week is 200 (March 6)
        assert weekly[0]["value"] == 200

    def test_monthly_uses_last_value(self):
        """SNAPSHOT metric's monthly aggregation should use last day's value."""
        rows = [
            _make_row("active_subscribers", 100, date(2026, 3, 1)),
            _make_row("active_subscribers", 300, date(2026, 3, 15)),
            _make_row("active_subscribers", 250, date(2026, 3, 31)),
        ]
        result = compute_aggregations(rows, TENANT_ID)

        monthly = [r for r in result if r["period_type"] == "monthly"]
        assert len(monthly) == 1
        assert monthly[0]["value"] == 250

    def test_snapshot_still_has_daily_records(self):
        """SNAPSHOT metrics should still have daily aggregation records."""
        rows = [
            _make_row("active_subscribers", 100, date(2026, 3, 1)),
            _make_row("active_subscribers", 200, date(2026, 3, 2)),
        ]
        result = compute_aggregations(rows, TENANT_ID)

        daily = [r for r in result if r["period_type"] == "daily"]
        assert len(daily) == 2


class TestEmptyInput:
    """Empty input should return empty output."""

    def test_empty_rows_returns_empty(self):
        """compute_aggregations([]) returns []."""
        result = compute_aggregations([], TENANT_ID)
        assert result == []


class TestGroupingByMetric:
    """Different metrics in the same channel should be aggregated independently."""

    def test_two_metrics_produce_separate_aggregations(self):
        """clicks and spend should produce independent daily + rollup records."""
        rows = [
            _make_row("clicks", 100, date(2026, 3, 5)),
            _make_row("spend", 50.0, date(2026, 3, 5), unit="currency"),
        ]
        result = compute_aggregations(rows, TENANT_ID)

        clicks_daily = [r for r in result if r["metric_name"] == "clicks" and r["period_type"] == "daily"]
        spend_daily = [r for r in result if r["metric_name"] == "spend" and r["period_type"] == "daily"]
        assert len(clicks_daily) == 1
        assert clicks_daily[0]["value"] == 100
        assert len(spend_daily) == 1
        assert spend_daily[0]["value"] == 50.0


class TestPeriodConfigPropagation:
    """compute_aggregations should use provided period_config."""

    def test_custom_week_start_day(self):
        """Sunday-start week groups days differently than default Monday."""
        cfg = TenantPeriodConfig(weekly_start_day=6)
        # 2026-03-01 is a Sunday → with Sunday start, this is the first day of the week
        # 2026-03-07 is a Saturday → last day of that week
        rows = [
            _make_row("clicks", 100, date(2026, 3, 1)),  # Sunday
            _make_row("clicks", 200, date(2026, 3, 7)),  # Saturday
        ]
        result = compute_aggregations(rows, TENANT_ID, period_config=cfg)

        weekly = [r for r in result if r["period_type"] == "weekly"]
        assert len(weekly) == 1
        assert weekly[0]["value"] == 300
        assert weekly[0]["period_start"] == date(2026, 3, 1)
        assert weekly[0]["period_end"] == date(2026, 3, 7)


class TestAggregationRecordShape:
    """Each aggregation record should carry all required fields."""

    def test_record_has_required_fields(self):
        """Every aggregation record dict should have the expected keys."""
        rows = [_make_row("clicks", 100, date(2026, 3, 5))]
        result = compute_aggregations(rows, TENANT_ID)

        assert len(result) > 0
        record = result[0]
        required_keys = {
            "tenant_id",
            "channel_slug",
            "metric_name",
            "period_type",
            "period_start",
            "period_end",
            "value",
            "unit",
        }
        for key in required_keys:
            assert key in record, f"Aggregation record missing key '{key}'"
