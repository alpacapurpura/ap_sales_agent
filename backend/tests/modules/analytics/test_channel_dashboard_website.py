"""Tests for Website channel dashboard configuration and benchmarks."""

from src.modules.analytics.application.services.channel_dashboard_service import (
    _CHANNEL_CONFIGS,
    _CHANNEL_NAMES,
)
from src.modules.analytics.domain.industry_benchmarks import (
    IndustryCategory,
    get_benchmarks,
)


class TestWebsiteTotalConfig:
    """Verify website-total dashboard configuration."""

    def test_website_total_config_exists(self):
        assert "website-total" in _CHANNEL_CONFIGS

    def test_website_total_channel_name(self):
        config = _CHANNEL_CONFIGS["website-total"]
        assert config.channel_name == "Tu Sitio Web"

    def test_website_total_hero_metrics(self):
        config = _CHANNEL_CONFIGS["website-total"]
        assert config.hero_metrics == [
            "sessions",
            "engagementRate",
            "bounceRate",
            "conversions",
            "averageSessionDuration",
            "users",
        ]

    def test_website_total_timeseries_metrics(self):
        config = _CHANNEL_CONFIGS["website-total"]
        assert "sessions" in config.timeseries_metrics
        assert "engagedSessions" in config.timeseries_metrics
        assert "bounceRate" in config.timeseries_metrics
        assert "conversions" in config.timeseries_metrics

    def test_website_total_funnel_steps(self):
        config = _CHANNEL_CONFIGS["website-total"]
        labels = [label for label, _ in config.funnel_steps]
        metrics = [metric for _, metric in config.funnel_steps]
        assert labels == [
            "Sesiones",
            "Comprometidas",
            "Pág. Vistas",
            "Conversiones",
        ]
        assert metrics == [
            "sessions",
            "engagedSessions",
            "screenPageViews",
            "conversions",
        ]

    def test_website_total_no_frequency_alert(self):
        config = _CHANNEL_CONFIGS["website-total"]
        assert config.has_frequency_alert is False

    def test_website_total_in_channel_names(self):
        assert "website-total" in _CHANNEL_NAMES
        assert _CHANNEL_NAMES["website-total"] == "Tu Sitio Web"


class TestWebsiteBenchmarks:
    """Verify industry benchmarks exist for website metrics."""

    def test_engagement_rate_benchmark_exists(self):
        bench = get_benchmarks(IndustryCategory.GENERAL, "engagementRate")
        assert bench is not None
        assert bench.unit == "percentage"

    def test_engagement_rate_values(self):
        bench = get_benchmarks(IndustryCategory.GENERAL, "engagementRate")
        assert bench is not None
        assert bench.low == 45.0
        assert bench.median == 56.0
        assert bench.high == 70.0

    def test_bounce_rate_benchmark_exists(self):
        bench = get_benchmarks(IndustryCategory.GENERAL, "bounceRate")
        assert bench is not None
        assert bench.unit == "percentage"

    def test_bounce_rate_values(self):
        bench = get_benchmarks(IndustryCategory.GENERAL, "bounceRate")
        assert bench is not None
        # For bounceRate, lower is better, so low=25 (best), high=55 (worst)
        assert bench.low == 25.0
        assert bench.median == 40.0
        assert bench.high == 55.0

    def test_avg_session_duration_benchmark_exists(self):
        bench = get_benchmarks(IndustryCategory.GENERAL, "averageSessionDuration")
        assert bench is not None
        assert bench.unit == "seconds"

    def test_avg_session_duration_values(self):
        bench = get_benchmarks(IndustryCategory.GENERAL, "averageSessionDuration")
        assert bench is not None
        assert bench.low == 60.0
        assert bench.median == 137.0
        assert bench.high == 300.0
