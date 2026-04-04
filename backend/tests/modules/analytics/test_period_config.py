"""Tests for TenantPeriodConfig — validates period boundary calculations.

Pure Python tests: no DB, no async, no mocking required.
"""

from datetime import date

from src.modules.analytics.domain.period_config import TenantPeriodConfig


class TestWeekBoundariesDefaultMonday:
    """Week boundaries with default Monday start (weekly_start_day=0)."""

    def test_monday_returns_same_week(self):
        """A Monday should be the start of its own week."""
        cfg = TenantPeriodConfig()
        # 2026-03-02 is a Monday
        ws, we = cfg.get_week_boundaries(date(2026, 3, 2))
        assert ws == date(2026, 3, 2)
        assert we == date(2026, 3, 8)

    def test_wednesday_returns_week_containing_it(self):
        """Mid-week should return the Monday-Sunday range containing it."""
        cfg = TenantPeriodConfig()
        # 2026-03-04 is a Wednesday
        ws, we = cfg.get_week_boundaries(date(2026, 3, 4))
        assert ws == date(2026, 3, 2)
        assert we == date(2026, 3, 8)

    def test_sunday_returns_week_containing_it(self):
        """Sunday should be the last day of the Monday-start week."""
        cfg = TenantPeriodConfig()
        # 2026-03-08 is a Sunday
        ws, we = cfg.get_week_boundaries(date(2026, 3, 8))
        assert ws == date(2026, 3, 2)
        assert we == date(2026, 3, 8)

    def test_week_is_always_7_days(self):
        """Every week boundary span must be exactly 7 days."""
        cfg = TenantPeriodConfig()
        for day_offset in range(14):
            d = date(2026, 3, 1) + __import__("datetime").timedelta(days=day_offset)
            ws, we = cfg.get_week_boundaries(d)
            assert (we - ws).days == 6


class TestWeekBoundariesSundayStart:
    """Week boundaries with custom Sunday start (weekly_start_day=6)."""

    def test_sunday_is_start(self):
        """Sunday start means Sunday should be the first day of the week."""
        cfg = TenantPeriodConfig(weekly_start_day=6)
        # 2026-03-01 is a Sunday
        ws, we = cfg.get_week_boundaries(date(2026, 3, 1))
        assert ws == date(2026, 3, 1)
        assert we == date(2026, 3, 7)

    def test_saturday_is_end(self):
        """With Sunday start, Saturday should be the last day of the week."""
        cfg = TenantPeriodConfig(weekly_start_day=6)
        # 2026-03-07 is a Saturday
        ws, we = cfg.get_week_boundaries(date(2026, 3, 7))
        assert ws == date(2026, 3, 1)
        assert we == date(2026, 3, 7)

    def test_wednesday_mid_week(self):
        """Wednesday falls in a Sunday-start week."""
        cfg = TenantPeriodConfig(weekly_start_day=6)
        # 2026-03-04 is a Wednesday
        ws, we = cfg.get_week_boundaries(date(2026, 3, 4))
        assert ws == date(2026, 3, 1)
        assert we == date(2026, 3, 7)


class TestMonthBoundaries:
    """Month boundary calculations including edge cases."""

    def test_march_2026(self):
        """March has 31 days."""
        cfg = TenantPeriodConfig()
        ms, me = cfg.get_month_boundaries(date(2026, 3, 15))
        assert ms == date(2026, 3, 1)
        assert me == date(2026, 3, 31)

    def test_february_non_leap_year(self):
        """February 2026 has 28 days (not a leap year)."""
        cfg = TenantPeriodConfig()
        ms, me = cfg.get_month_boundaries(date(2026, 2, 10))
        assert ms == date(2026, 2, 1)
        assert me == date(2026, 2, 28)

    def test_february_leap_year(self):
        """February 2028 has 29 days (leap year)."""
        cfg = TenantPeriodConfig()
        ms, me = cfg.get_month_boundaries(date(2028, 2, 15))
        assert ms == date(2028, 2, 1)
        assert me == date(2028, 2, 29)

    def test_first_day_of_month(self):
        """Querying the first day still returns the full month."""
        cfg = TenantPeriodConfig()
        ms, me = cfg.get_month_boundaries(date(2026, 1, 1))
        assert ms == date(2026, 1, 1)
        assert me == date(2026, 1, 31)

    def test_last_day_of_month(self):
        """Querying the last day still returns the full month."""
        cfg = TenantPeriodConfig()
        ms, me = cfg.get_month_boundaries(date(2026, 4, 30))
        assert ms == date(2026, 4, 1)
        assert me == date(2026, 4, 30)


class TestQuarterBoundariesDefault:
    """Quarter boundaries with default calendar year (fiscal_year_start_month=1)."""

    def test_q1_default(self):
        """Q1 = January-March for default fiscal year."""
        cfg = TenantPeriodConfig()
        qs, qe = cfg.get_quarter_boundaries(date(2026, 2, 15))
        assert qs == date(2026, 1, 1)
        assert qe == date(2026, 3, 31)

    def test_q2_default(self):
        """Q2 = April-June for default fiscal year."""
        cfg = TenantPeriodConfig()
        qs, qe = cfg.get_quarter_boundaries(date(2026, 5, 10))
        assert qs == date(2026, 4, 1)
        assert qe == date(2026, 6, 30)

    def test_q3_default(self):
        """Q3 = July-September for default fiscal year."""
        cfg = TenantPeriodConfig()
        qs, qe = cfg.get_quarter_boundaries(date(2026, 8, 20))
        assert qs == date(2026, 7, 1)
        assert qe == date(2026, 9, 30)

    def test_q4_default(self):
        """Q4 = October-December for default fiscal year."""
        cfg = TenantPeriodConfig()
        qs, qe = cfg.get_quarter_boundaries(date(2026, 11, 1))
        assert qs == date(2026, 10, 1)
        assert qe == date(2026, 12, 31)

    def test_quarter_number_q1(self):
        """get_quarter_number returns 1 for Jan-Mar."""
        cfg = TenantPeriodConfig()
        assert cfg.get_quarter_number(date(2026, 1, 15)) == 1
        assert cfg.get_quarter_number(date(2026, 3, 31)) == 1

    def test_quarter_number_q4(self):
        """get_quarter_number returns 4 for Oct-Dec."""
        cfg = TenantPeriodConfig()
        assert cfg.get_quarter_number(date(2026, 10, 1)) == 4
        assert cfg.get_quarter_number(date(2026, 12, 31)) == 4


class TestQuarterBoundariesFiscalOffset:
    """Quarter boundaries with fiscal year starting in April."""

    def test_fiscal_q1_starts_april(self):
        """With fiscal year starting April, Q1 = April-June."""
        cfg = TenantPeriodConfig(fiscal_year_start_month=4)
        assert cfg.get_quarter_number(date(2026, 4, 15)) == 1
        qs, qe = cfg.get_quarter_boundaries(date(2026, 4, 15))
        assert qs == date(2026, 4, 1)
        assert qe == date(2026, 6, 30)

    def test_fiscal_q4_ends_march(self):
        """With fiscal year starting April, Q4 = January-March."""
        cfg = TenantPeriodConfig(fiscal_year_start_month=4)
        assert cfg.get_quarter_number(date(2026, 2, 15)) == 4
        qs, qe = cfg.get_quarter_boundaries(date(2026, 2, 15))
        assert qs == date(2026, 1, 1)
        assert qe == date(2026, 3, 31)


class TestPeriodKeyComputation:
    """compute_period_keys returns correct period keys."""

    def test_iso_week_start_key(self):
        """iso_week_start should be the Monday of the week (default config)."""
        cfg = TenantPeriodConfig()
        # 2026-03-04 is a Wednesday, Monday is 2026-03-02
        keys = cfg.compute_period_keys(date(2026, 3, 4))
        assert keys["iso_week_start"] == date(2026, 3, 2)

    def test_month_key_format(self):
        """month_key should be YYYY-MM format."""
        cfg = TenantPeriodConfig()
        keys = cfg.compute_period_keys(date(2026, 3, 15))
        assert keys["month_key"] == "2026-03"

    def test_quarter_key_format(self):
        """quarter_key should be YYYY-QN format."""
        cfg = TenantPeriodConfig()
        keys = cfg.compute_period_keys(date(2026, 3, 15))
        assert keys["quarter_key"] == "2026-Q1"

    def test_quarter_key_q3(self):
        """quarter_key for August should be Q3."""
        cfg = TenantPeriodConfig()
        keys = cfg.compute_period_keys(date(2026, 8, 10))
        assert keys["quarter_key"] == "2026-Q3"

    def test_all_keys_present(self):
        """compute_period_keys returns all three keys."""
        cfg = TenantPeriodConfig()
        keys = cfg.compute_period_keys(date(2026, 3, 1))
        assert "iso_week_start" in keys
        assert "month_key" in keys
        assert "quarter_key" in keys


class TestBoundaryDetection:
    """is_period_boundary detects last day of periods for scheduler."""

    def test_sunday_is_weekly_boundary_monday_start(self):
        """Sunday is the last day of a Monday-start week."""
        cfg = TenantPeriodConfig()
        # 2026-03-08 is a Sunday
        assert cfg.is_period_boundary(date(2026, 3, 8), "weekly") is True

    def test_monday_is_not_weekly_boundary_monday_start(self):
        """Monday is not the last day of a Monday-start week."""
        cfg = TenantPeriodConfig()
        assert cfg.is_period_boundary(date(2026, 3, 2), "weekly") is False

    def test_last_day_of_month_is_monthly_boundary(self):
        """March 31 is a monthly boundary."""
        cfg = TenantPeriodConfig()
        assert cfg.is_period_boundary(date(2026, 3, 31), "monthly") is True

    def test_mid_month_is_not_monthly_boundary(self):
        """March 15 is not a monthly boundary."""
        cfg = TenantPeriodConfig()
        assert cfg.is_period_boundary(date(2026, 3, 15), "monthly") is False

    def test_last_day_of_quarter_is_quarterly_boundary(self):
        """March 31 is a quarterly boundary (default fiscal year)."""
        cfg = TenantPeriodConfig()
        assert cfg.is_period_boundary(date(2026, 3, 31), "quarterly") is True

    def test_mid_quarter_is_not_quarterly_boundary(self):
        """February 15 is not a quarterly boundary."""
        cfg = TenantPeriodConfig()
        assert cfg.is_period_boundary(date(2026, 2, 15), "quarterly") is False

    def test_unknown_period_type_returns_false(self):
        """Unknown period type should return False."""
        cfg = TenantPeriodConfig()
        assert cfg.is_period_boundary(date(2026, 3, 31), "yearly") is False
