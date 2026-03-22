import pytest


class TestCALCalculation:
    """Tests for Cost of Acquisition per Lead formula."""

    @pytest.mark.skip(reason="Wave 0 stub -- implement after Task 1")
    def test_cal_basic_division(self):
        """CAL = total_costs / total_leads, rounded to 2 decimals."""
        pass

    @pytest.mark.skip(reason="Wave 0 stub -- implement after Task 1")
    def test_cal_zero_leads_returns_none(self):
        """CAL returns None when total_leads == 0 (avoid division by zero)."""
        pass

    @pytest.mark.skip(reason="Wave 0 stub -- implement after Task 1")
    def test_cal_zero_costs_returns_zero(self):
        """CAL returns 0.0 when costs are zero but leads exist."""
        pass
