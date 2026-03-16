"""Tests for K-Factor calculation logic."""
import pytest


class TestKFactorCalculation:
    """K-Factor formula: (referrals_sent / evangelists) * (conversions / referrals_sent)."""

    @pytest.mark.skip(reason="Wave 0 stub — implement after Plan 10-02 Task 1")
    def test_k_factor_basic_calculation(self):
        """K = (total_referrals / evangelists) * (conversions / total_referrals)."""
        pass

    @pytest.mark.skip(reason="Wave 0 stub — implement after Plan 10-02 Task 1")
    def test_k_factor_zero_evangelists_returns_zero(self):
        """Division by zero when no evangelists returns 0.0."""
        pass

    @pytest.mark.skip(reason="Wave 0 stub — implement after Plan 10-02 Task 1")
    def test_k_factor_zero_referrals_returns_zero(self):
        """Division by zero when no referrals sent returns 0.0."""
        pass

    @pytest.mark.skip(reason="Wave 0 stub — implement after Plan 10-02 Task 1")
    def test_k_factor_above_one_indicates_viral_growth(self):
        """K > 1.0 means each evangelist generates more than one new customer."""
        pass
