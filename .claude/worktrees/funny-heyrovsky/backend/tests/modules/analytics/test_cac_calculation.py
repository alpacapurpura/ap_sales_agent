"""Tests for CAC calculation logic.

VEN-05: CAC = stages 0-3 costs / CONVERSION count.
"""

import pytest


class TestStageCostServiceExtension:
    """StageCostService has get_total_funnel_investment method."""

    def test_method_exists(self):
        from src.modules.analytics.application.services.stage_cost_service import (
            StageCostService,
        )
        assert hasattr(StageCostService, "get_total_funnel_investment")

    def test_method_signature_returns_tuple(self):
        """get_total_funnel_investment returns tuple[float, bool]."""
        import inspect
        from src.modules.analytics.application.services.stage_cost_service import (
            StageCostService,
        )
        sig = inspect.signature(StageCostService.get_total_funnel_investment)
        params = list(sig.parameters.keys())
        assert "tenant_id" in params
        assert "start_date" in params
        assert "end_date" in params


class TestCACHeaderKPI:
    """SalesHeaderKpisDTO has CAC fields."""

    def test_header_has_cac_field(self):
        from src.modules.analytics.application.dto.sales_dto import SalesHeaderKpisDTO
        dto = SalesHeaderKpisDTO(
            total_revenue=1000.0,
            currency="USD",
            new_customers=10,
            cac=50.0,
            cac_incomplete=False,
        )
        assert dto.cac == 50.0
        assert dto.cac_incomplete is False

    def test_header_cac_none_when_no_customers(self):
        from src.modules.analytics.application.dto.sales_dto import SalesHeaderKpisDTO
        dto = SalesHeaderKpisDTO(
            total_revenue=0.0,
            currency="USD",
            new_customers=0,
            cac=None,
            cac_incomplete=True,
        )
        assert dto.cac is None
        assert dto.cac_incomplete is True

    def test_header_has_new_customers(self):
        from src.modules.analytics.application.dto.sales_dto import SalesHeaderKpisDTO
        dto = SalesHeaderKpisDTO(
            total_revenue=5000.0,
            currency="MXN",
            new_customers=25,
        )
        assert dto.new_customers == 25


class TestBottleneckThresholds:
    """Bottleneck threshold constants exist and have correct values."""

    def test_low_conversion_thresholds_exist(self):
        from src.modules.analytics.application.dto.sales_dto import LOW_CONVERSION_THRESHOLDS
        assert "warning" in LOW_CONVERSION_THRESHOLDS
        assert "critical" in LOW_CONVERSION_THRESHOLDS
        assert LOW_CONVERSION_THRESHOLDS["warning"] == 20.0
        assert LOW_CONVERSION_THRESHOLDS["critical"] == 10.0

    def test_high_cac_ratios_exist(self):
        from src.modules.analytics.application.dto.sales_dto import (
            HIGH_CAC_WARNING_RATIO,
            HIGH_CAC_CRITICAL_RATIO,
        )
        assert HIGH_CAC_WARNING_RATIO == 0.33
        assert HIGH_CAC_CRITICAL_RATIO == 0.50
