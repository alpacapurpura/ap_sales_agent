"""Tests for ChannelDashboardService -- delta computation, funnel rates, frequency alerts."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from luana_core_analytics_engine.application.services.channel_dashboard_service import (
    _CHANNEL_CONFIGS,
    ChannelDashboardService,
)


@pytest.fixture
def mock_db():
    """Minimal mock DB session."""
    return MagicMock()


@pytest.fixture
def mock_brand_port():
    """BrandReadPort returning 'education' industry."""
    port = AsyncMock()
    port.get_industry.return_value = "educación"
    return port


class TestBuildKpis:
    """Test KPI computation with deltas."""

    def test_delta_computation(self, mock_db):
        service = ChannelDashboardService(mock_db)
        current = {"spend": 1000.0, "ROAS": 2.5}
        previous = {"spend": 800.0, "ROAS": 2.0}
        from luana_core_analytics_engine.domain.industry_benchmarks import IndustryCategory

        kpis = service._build_kpis(current, previous, IndustryCategory.GENERAL)
        spend_kpi = next((k for k in kpis if k.metric_name == "spend"), None)
        assert spend_kpi is not None
        assert spend_kpi.current_value == 1000.0
        assert spend_kpi.delta_percent == 25.0

    def test_missing_previous_gives_null_delta(self, mock_db):
        service = ChannelDashboardService(mock_db)
        current = {"spend": 500.0}
        previous = {}
        from luana_core_analytics_engine.domain.industry_benchmarks import IndustryCategory

        kpis = service._build_kpis(current, previous, IndustryCategory.GENERAL)
        spend_kpi = next((k for k in kpis if k.metric_name == "spend"), None)
        assert spend_kpi is not None
        assert spend_kpi.delta_percent is None

    def test_benchmarks_attached(self, mock_db):
        service = ChannelDashboardService(mock_db)
        current = {"CTR": 1.8}
        previous = {}
        from luana_core_analytics_engine.domain.industry_benchmarks import IndustryCategory

        kpis = service._build_kpis(current, previous, IndustryCategory.GENERAL)
        ctr_kpi = next((k for k in kpis if k.metric_name == "CTR"), None)
        assert ctr_kpi is not None
        assert ctr_kpi.benchmark is not None
        assert ctr_kpi.benchmark.low == 0.9


class TestBuildFunnel:
    """Test funnel step conversion rates."""

    def test_conversion_rates(self, mock_db):
        service = ChannelDashboardService(mock_db)
        metrics = {
            "impressions": 10000.0,
            "clicks": 200.0,
            "meta_landing_page_views": 150.0,
            "meta_leads": 30.0,
            "conversions": 10.0,
        }
        funnel = service._build_funnel(metrics)
        assert len(funnel.steps) == 5
        # First step has no conversion rate
        assert funnel.steps[0].conversion_rate_from_previous is None
        # clicks / impressions
        assert funnel.steps[1].conversion_rate_from_previous == 2.0
        # conversions / leads
        assert funnel.steps[4].conversion_rate_from_previous == pytest.approx(
            33.33,
            abs=0.01,
        )

    def test_zero_previous_gives_none(self, mock_db):
        service = ChannelDashboardService(mock_db)
        metrics = {"impressions": 0.0, "clicks": 5.0}
        funnel = service._build_funnel(metrics)
        # clicks step: prev=0, should be None
        assert funnel.steps[1].conversion_rate_from_previous is None


class TestFrequencyAlert:
    """Test frequency fatigue detection."""

    def test_no_frequency_data(self, mock_db):
        service = ChannelDashboardService(mock_db)
        assert service._check_frequency({}) is None

    def test_normal_frequency(self, mock_db):
        service = ChannelDashboardService(mock_db)
        assert service._check_frequency({"frequency": 2.0}) is None

    def test_warning_frequency(self, mock_db):
        service = ChannelDashboardService(mock_db)
        alert = service._check_frequency({"frequency": 3.5})
        assert alert is not None
        assert alert.severity == "warning"

    def test_critical_frequency(self, mock_db):
        service = ChannelDashboardService(mock_db)
        alert = service._check_frequency({"frequency": 6.0})
        assert alert is not None
        assert alert.severity == "critical"


class TestMetricResolverIntegration:
    """Test MetricResolver integration in _build_kpis.

    Verifies that aliases like ROAS, CTR, CPC are properly resolved
    to get display_name, unit, benchmarks from the metric catalog.
    """

    def test_alias_kpi_gets_catalog_metadata(self, mock_db):
        """ROAS alias should get display_name, unit, benchmarks from catalog."""
        from luana_core_analytics_engine.domain.industry_benchmarks import IndustryCategory

        service = ChannelDashboardService(mock_db)
        config = _CHANNEL_CONFIGS["meta-ads"]
        # Provide ROAS by alias key (as resolver will put it) and also spend
        current = {"spend": 1000.0, "ROAS": 3.0}
        previous = {"spend": 800.0, "ROAS": 2.5}

        kpis = service._build_kpis(current, previous, IndustryCategory.GENERAL, config)
        roas_kpi = next((k for k in kpis if k.metric_name == "ROAS"), None)
        assert roas_kpi is not None
        assert roas_kpi.current_value == 3.0
        # Catalog should provide "ROAS" as display_name for meta_purchase_roas
        assert roas_kpi.display_name == "ROAS"
        assert roas_kpi.unit == "ratio"

    def test_ctr_alias_gets_benchmark(self, mock_db):
        """CTR alias should get benchmark from catalog."""
        from luana_core_analytics_engine.domain.industry_benchmarks import IndustryCategory

        service = ChannelDashboardService(mock_db)
        config = _CHANNEL_CONFIGS["meta-ads"]
        current = {"spend": 1000.0, "CTR": 1.5}
        previous = {}

        kpis = service._build_kpis(current, previous, IndustryCategory.GENERAL, config)
        ctr_kpi = next((k for k in kpis if k.metric_name == "CTR"), None)
        assert ctr_kpi is not None
        assert ctr_kpi.benchmark is not None
        assert ctr_kpi.display_name == "CTR"
        assert ctr_kpi.unit == "percentage"

    def test_cpc_alias_higher_is_better_false(self, mock_db):
        """CPC alias should resolve higher_is_better=False from catalog."""
        from luana_core_analytics_engine.domain.industry_benchmarks import IndustryCategory

        service = ChannelDashboardService(mock_db)
        config = _CHANNEL_CONFIGS["meta-ads"]
        current = {"spend": 1000.0, "CPC": 2.5}
        previous = {}

        kpis = service._build_kpis(current, previous, IndustryCategory.GENERAL, config)
        cpc_kpi = next((k for k in kpis if k.metric_name == "CPC"), None)
        assert cpc_kpi is not None
        assert cpc_kpi.higher_is_better is False
