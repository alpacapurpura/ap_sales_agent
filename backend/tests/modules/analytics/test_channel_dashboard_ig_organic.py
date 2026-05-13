"""Tests for IG Organic channel dashboard configuration and derived metrics."""

from unittest.mock import MagicMock

import pytest

from luana_core_analytics_engine.application.services.channel_dashboard_service import (
    _CHANNEL_CONFIGS,
    ChannelDashboardService,
    _compute_derived_metrics,
)
from luana_core_analytics_engine.domain.industry_benchmarks import (
    IndustryCategory,
    get_benchmarks,
)


@pytest.fixture
def mock_db():
    return MagicMock()


class TestIgOrganicConfig:
    """Verify IG Organic dashboard configuration."""

    def test_ig_organic_config_uses_correct_hero_metrics(self):
        config = _CHANNEL_CONFIGS["ig-organic"]
        assert config.hero_metrics == [
            "total_interactions",
            "ig_views",
            "ig_follows_and_unfollows",
            "ig_follows_gained",
            "ig_follows_lost",
            "ig_engagement_rate",
        ]

    def test_ig_organic_funnel_steps(self):
        config = _CHANNEL_CONFIGS["ig-organic"]
        labels = [label for label, _ in config.funnel_steps]
        metrics = [metric for _, metric in config.funnel_steps]
        assert labels == ["Vistas", "Interacciones", "Compartidos", "Taps en Perfil"]
        assert metrics == [
            "ig_views",
            "total_interactions",
            "ig_shares",
            "ig_profile_links_taps",
        ]

    def test_ig_organic_no_frequency_alert(self):
        config = _CHANNEL_CONFIGS["ig-organic"]
        assert config.has_frequency_alert is False


class TestComputedEngagementRate:
    """Verify ig_engagement_rate derived metric computation."""

    def test_computed_engagement_rate(self):
        metrics: dict[str, float] = {
            "total_interactions": 500.0,
            "ig_views": 10000.0,
        }
        _compute_derived_metrics(metrics)
        assert metrics["ig_engagement_rate"] == 5.0

    def test_computed_engagement_rate_zero_views(self):
        metrics: dict[str, float] = {
            "total_interactions": 100.0,
            "ig_views": 0.0,
        }
        _compute_derived_metrics(metrics)
        assert metrics["ig_engagement_rate"] == 0.0

    def test_computed_engagement_rate_no_data(self):
        metrics: dict[str, float] = {}
        _compute_derived_metrics(metrics)
        assert metrics["ig_engagement_rate"] == 0.0


class TestIgOrganicBenchmarks:
    """Verify IG Organic benchmarks are registered."""

    def test_ig_organic_benchmarks_exist(self):
        entry = get_benchmarks(IndustryCategory.GENERAL, "ig_engagement_rate")
        assert entry is not None
        assert entry.low == 0.30
        assert entry.median == 0.50
        assert entry.high == 1.20


class TestIgOrganicKpisAndFunnel:
    """Test KPI and funnel building with IG Organic config."""

    def test_ig_organic_kpis_built_correctly(self, mock_db):
        service = ChannelDashboardService(mock_db)
        config = _CHANNEL_CONFIGS["ig-organic"]
        current = {
            "total_interactions": 2450.0,
            "ig_views": 485000.0,
            "ig_follows_and_unfollows": 127.0,
            "ig_follows_gained": 150.0,
            "ig_follows_lost": 23.0,
            "ig_engagement_rate": 0.51,
        }
        previous = {
            "total_interactions": 2000.0,
            "ig_views": 400000.0,
            "ig_follows_and_unfollows": 100.0,
            "ig_follows_gained": 118.0,
            "ig_follows_lost": 18.0,
            "ig_engagement_rate": 0.50,
        }
        kpis = service._build_kpis(current, previous, IndustryCategory.GENERAL, config)
        assert len(kpis) == 6
        names = [k.metric_name for k in kpis]
        assert names == [
            "total_interactions",
            "ig_views",
            "ig_follows_and_unfollows",
            "ig_follows_gained",
            "ig_follows_lost",
            "ig_engagement_rate",
        ]
        gained = next(k for k in kpis if k.metric_name == "ig_follows_gained")
        assert gained.current_value == 150.0
        assert gained.display_name == "Seguidores Ganados"
        lost = next(k for k in kpis if k.metric_name == "ig_follows_lost")
        assert lost.current_value == 23.0
        assert lost.display_name == "Seguidores Perdidos"
        assert lost.higher_is_better is False
        net = next(k for k in kpis if k.metric_name == "ig_follows_and_unfollows")
        # Sanity: the net metric must equal gained - lost in the same period
        assert net.current_value == pytest.approx(
            gained.current_value - lost.current_value,
        )

    def test_ig_organic_funnel_built_correctly(self, mock_db):
        service = ChannelDashboardService(mock_db)
        config = _CHANNEL_CONFIGS["ig-organic"]
        metrics = {
            "ig_views": 485000.0,
            "total_interactions": 2450.0,
            "ig_shares": 380.0,
            "ig_profile_links_taps": 95.0,
        }
        funnel = service._build_funnel(metrics, config)
        assert len(funnel.steps) == 4
        assert funnel.steps[0].label == "Vistas"
        assert funnel.steps[0].value == 485000.0
        assert funnel.steps[0].conversion_rate_from_previous is None
        # Interacciones / Vistas
        assert funnel.steps[1].conversion_rate_from_previous == pytest.approx(
            0.51,
            abs=0.01,
        )


class TestMetaAdsRegression:
    """Ensure Meta Ads still works after IG Organic additions."""

    def test_meta_ads_config_unchanged(self):
        config = _CHANNEL_CONFIGS["meta-ads"]
        assert config.channel_name == "Meta Ads"
        assert "spend" in config.hero_metrics
        assert "ROAS" in config.hero_metrics
        assert config.has_frequency_alert is True

    def test_meta_ads_kpis_still_work(self, mock_db):
        service = ChannelDashboardService(mock_db)
        config = _CHANNEL_CONFIGS["meta-ads"]
        current = {"spend": 1000.0, "ROAS": 2.5}
        previous = {"spend": 800.0, "ROAS": 2.0}
        kpis = service._build_kpis(current, previous, IndustryCategory.GENERAL, config)
        spend_kpi = next((k for k in kpis if k.metric_name == "spend"), None)
        assert spend_kpi is not None
        assert spend_kpi.current_value == 1000.0
        assert spend_kpi.delta_percent == 25.0
