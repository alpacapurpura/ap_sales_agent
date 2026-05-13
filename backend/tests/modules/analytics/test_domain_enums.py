"""Tests for analytics domain enums — validates enum members and values.

Pure Python tests: no DB, no async, no mocking required.
"""

from luana_core_analytics_engine.domain.enums import (
    AggregationType,
    CostType,
    ExtractionStatus,
    ExtractionType,
    MetricUnit,
    PeriodType,
)


class TestCostType:
    """CostType enum has all expected financial classification members."""

    def test_has_neutral(self):
        assert CostType.NEUTRAL.value == "neutral"

    def test_has_expense(self):
        assert CostType.EXPENSE.value == "expense"

    def test_has_investment(self):
        assert CostType.INVESTMENT.value == "investment"

    def test_has_revenue(self):
        assert CostType.REVENUE.value == "revenue"

    def test_member_count(self):
        assert len(CostType) == 4

    def test_is_str_enum(self):
        """CostType members are also strings (str, Enum)."""
        assert isinstance(CostType.NEUTRAL, str)
        assert CostType.NEUTRAL == "neutral"


class TestMetricUnit:
    """MetricUnit enum has all expected measurement unit members."""

    def test_has_count(self):
        assert MetricUnit.COUNT.value == "count"

    def test_has_currency(self):
        assert MetricUnit.CURRENCY.value == "currency"

    def test_has_percentage(self):
        assert MetricUnit.PERCENTAGE.value == "percentage"

    def test_has_ratio(self):
        assert MetricUnit.RATIO.value == "ratio"

    def test_has_seconds(self):
        assert MetricUnit.SECONDS.value == "seconds"

    def test_has_json(self):
        assert MetricUnit.JSON.value == "json"

    def test_member_count(self):
        assert len(MetricUnit) == 6


class TestExtractionStatus:
    """ExtractionStatus enum has all ETL lifecycle states."""

    def test_has_pending(self):
        assert ExtractionStatus.PENDING.value == "pending"

    def test_has_running(self):
        assert ExtractionStatus.RUNNING.value == "running"

    def test_has_success(self):
        assert ExtractionStatus.SUCCESS.value == "success"

    def test_has_failed(self):
        assert ExtractionStatus.FAILED.value == "failed"

    def test_has_partial_success(self):
        assert ExtractionStatus.PARTIAL_SUCCESS.value == "partial_success"

    def test_has_retrying(self):
        assert ExtractionStatus.RETRYING.value == "retrying"

    def test_member_count(self):
        assert len(ExtractionStatus) == 6


class TestAggregationType:
    """AggregationType enum has all metric aggregation strategies."""

    def test_has_additive(self):
        assert AggregationType.ADDITIVE.value == "additive"

    def test_has_weighted_average(self):
        assert AggregationType.WEIGHTED_AVERAGE.value == "weighted_avg"

    def test_has_derived(self):
        assert AggregationType.DERIVED.value == "derived"

    def test_has_non_aggregable(self):
        assert AggregationType.NON_AGGREGABLE.value == "non_aggregable"

    def test_has_snapshot(self):
        assert AggregationType.SNAPSHOT.value == "snapshot"

    def test_member_count(self):
        assert len(AggregationType) == 5


class TestPeriodType:
    """PeriodType enum has all time granularity levels."""

    def test_has_daily(self):
        assert PeriodType.DAILY.value == "daily"

    def test_has_weekly(self):
        assert PeriodType.WEEKLY.value == "weekly"

    def test_has_monthly(self):
        assert PeriodType.MONTHLY.value == "monthly"

    def test_has_quarterly(self):
        assert PeriodType.QUARTERLY.value == "quarterly"

    def test_has_last_30_days(self):
        assert PeriodType.LAST_30_DAYS.value == "last_30_days"

    def test_member_count(self):
        assert len(PeriodType) == 5


class TestExtractionType:
    """ExtractionType enum has daily and period members."""

    def test_has_daily(self):
        assert ExtractionType.DAILY.value == "daily"

    def test_has_period(self):
        assert ExtractionType.PERIOD.value == "period"

    def test_member_count(self):
        assert len(ExtractionType) == 2
