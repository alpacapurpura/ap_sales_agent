"""Tests for StageCostService per-group and combined cost calculations."""
import pytest


class TestStageCostService:
    """Tests for StageCostService."""

    @pytest.mark.skip(reason="Stub -- implement after Task 1")
    def test_calculate_cost_per_mql_with_costs_and_mqls(self):
        """cost_per_mql = total_costs / total_mqls."""
        pass

    @pytest.mark.skip(reason="Stub -- implement after Task 1")
    def test_calculate_cost_per_mql_returns_none_when_zero_mqls(self):
        """cost_per_mql returns None when total_mqls == 0."""
        pass

    @pytest.mark.skip(reason="Stub -- implement after Task 1")
    def test_get_retargeting_spend_from_metric_aggregation(self):
        """get_retargeting_spend returns spend per retargeting channel slug."""
        pass

    @pytest.mark.skip(reason="Stub -- implement after Task 1")
    def test_get_group_cost_per_mql_retargeting(self):
        """get_group_cost_per_mql('retargeting') returns cost/MQL for retargeting only."""
        pass

    @pytest.mark.skip(reason="Stub -- implement after Task 1")
    def test_get_group_cost_per_mql_automation(self):
        """get_group_cost_per_mql('automation') returns cost/MQL for automation only."""
        pass
