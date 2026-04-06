"""Tests for YouTube Organic channel dashboard configuration and derived metrics."""

from unittest.mock import MagicMock

import pytest

from src.modules.analytics.application.services.channel_dashboard_service import (
    _CHANNEL_CONFIGS,
    ChannelDashboardService,
    _compute_derived_metrics,
)
from src.modules.analytics.domain.industry_benchmarks import (
    IndustryCategory,
    get_benchmarks,
)


@pytest.fixture
def mock_db():
    return MagicMock()


class TestYtOrganicChannelConfig:
    """Tests for yt-organic channel configuration."""

    def test_config_exists(self):
        assert "yt-organic" in _CHANNEL_CONFIGS

    def test_hero_metrics(self):
        config = _CHANNEL_CONFIGS["yt-organic"]
        assert config.hero_metrics == [
            "views",
            "watch_time_minutes",
            "subscribers_gained",
            "avg_view_percentage",
        ]

    def test_funnel_steps(self):
        config = _CHANNEL_CONFIGS["yt-organic"]
        assert len(config.funnel_steps) == 4
        labels = [s[0] for s in config.funnel_steps]
        assert labels == ["Vistas", "Engagement", "Suscriptores", "Clics Tarjetas"]

    def test_no_frequency_alert(self):
        config = _CHANNEL_CONFIGS["yt-organic"]
        assert config.has_frequency_alert is False

    def test_timeseries_metrics(self):
        config = _CHANNEL_CONFIGS["yt-organic"]
        assert "views" in config.timeseries_metrics
        assert "watch_time_minutes" in config.timeseries_metrics
        assert "avg_view_percentage" in config.timeseries_metrics


class TestDerivedMetrics:
    """Tests for _compute_derived_metrics -- YouTube card and end screen rates."""

    def test_card_click_rate(self):
        metrics: dict[str, float] = {
            "card_clicks": 30,
            "card_impressions": 1000,
        }
        _compute_derived_metrics(metrics)
        assert metrics["card_click_rate"] == 3.0

    def test_end_screen_click_rate(self):
        metrics: dict[str, float] = {
            "end_screen_clicks": 20,
            "end_screen_impressions": 1000,
        }
        _compute_derived_metrics(metrics)
        assert metrics["end_screen_click_rate"] == 2.0

    def test_division_by_zero_card(self):
        metrics: dict[str, float] = {"card_clicks": 10, "card_impressions": 0}
        _compute_derived_metrics(metrics)
        assert "card_click_rate" not in metrics

    def test_division_by_zero_end_screen(self):
        metrics: dict[str, float] = {
            "end_screen_clicks": 5,
            "end_screen_impressions": 0,
        }
        _compute_derived_metrics(metrics)
        assert "end_screen_click_rate" not in metrics

    def test_missing_components(self):
        metrics: dict[str, float] = {}
        _compute_derived_metrics(metrics)
        assert "card_click_rate" not in metrics
        assert "end_screen_click_rate" not in metrics

    def test_preserves_original_metrics(self):
        metrics: dict[str, float] = {
            "views": 5000,
            "card_clicks": 30,
            "card_impressions": 1000,
        }
        _compute_derived_metrics(metrics)
        assert metrics["views"] == 5000
        assert metrics["card_click_rate"] == 3.0


class TestYouTubeBenchmarks:
    """Tests for YouTube-specific benchmarks."""

    def test_avg_view_percentage_benchmark(self):
        entry = get_benchmarks(IndustryCategory.GENERAL, "avg_view_percentage")
        assert entry is not None
        assert entry.low == 30.0
        assert entry.median == 50.0
        assert entry.high == 70.0

    def test_card_click_rate_benchmark(self):
        entry = get_benchmarks(IndustryCategory.GENERAL, "card_click_rate")
        assert entry is not None
        assert entry.low == 1.0
        assert entry.median == 3.0

    def test_end_screen_click_rate_benchmark(self):
        entry = get_benchmarks(IndustryCategory.GENERAL, "end_screen_click_rate")
        assert entry is not None
        assert entry.median == 2.0


class TestYtOrganicKpisAndFunnel:
    """Test KPI and funnel building with yt-organic config."""

    def test_yt_organic_kpis_built_correctly(self, mock_db):
        service = ChannelDashboardService(mock_db)
        config = _CHANNEL_CONFIGS["yt-organic"]
        current = {
            "views": 50000.0,
            "watch_time_minutes": 12000.0,
            "subscribers_gained": 320.0,
            "avg_view_percentage": 55.0,
        }
        previous = {
            "views": 40000.0,
            "watch_time_minutes": 10000.0,
            "subscribers_gained": 250.0,
            "avg_view_percentage": 50.0,
        }
        kpis = service._build_kpis(current, previous, IndustryCategory.GENERAL, config)
        assert len(kpis) == 4
        names = [k.metric_name for k in kpis]
        assert names == [
            "views",
            "watch_time_minutes",
            "subscribers_gained",
            "avg_view_percentage",
        ]
        # Check delta on views: (50000 - 40000) / 40000 * 100 = 25.0%
        views_kpi = next(k for k in kpis if k.metric_name == "views")
        assert views_kpi.delta_percent == 25.0

    def test_yt_organic_funnel_built_correctly(self, mock_db):
        service = ChannelDashboardService(mock_db)
        config = _CHANNEL_CONFIGS["yt-organic"]
        metrics = {
            "views": 50000.0,
            "engagement": 3000.0,
            "subscribers_gained": 320.0,
            "card_clicks": 150.0,
        }
        funnel = service._build_funnel(metrics, config)
        assert len(funnel.steps) == 4
        assert funnel.steps[0].label == "Vistas"
        assert funnel.steps[0].value == 50000.0
        assert funnel.steps[0].conversion_rate_from_previous is None
        # Engagement / Vistas = 3000/50000 * 100 = 6.0%
        assert funnel.steps[1].conversion_rate_from_previous == 6.0


class TestMetaAdsConfigUnchanged:
    """Regression: Meta Ads config must not break."""

    def test_meta_ads_config_exists(self):
        assert "meta-ads" in _CHANNEL_CONFIGS

    def test_meta_ads_has_frequency_alert(self):
        config = _CHANNEL_CONFIGS["meta-ads"]
        assert config.has_frequency_alert is True

    def test_meta_ads_hero_metrics(self):
        config = _CHANNEL_CONFIGS["meta-ads"]
        assert "spend" in config.hero_metrics
        assert "ROAS" in config.hero_metrics

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
