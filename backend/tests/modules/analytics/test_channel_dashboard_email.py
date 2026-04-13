"""Tests for Email Marketing (email-nurture) channel dashboard configuration and derived metrics."""

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


class TestEmailNurtureChannelConfig:
    """Verify the email-nurture entry in _CHANNEL_CONFIGS."""

    def test_config_exists(self) -> None:
        assert "email-nurture" in _CHANNEL_CONFIGS

    def test_hero_metrics(self) -> None:
        config = _CHANNEL_CONFIGS["email-nurture"]
        assert config.hero_metrics == [
            "open_rate",
            "click_rate",
            "emails_sent",
            "active_subscribers",
        ]

    def test_funnel_steps(self) -> None:
        config = _CHANNEL_CONFIGS["email-nurture"]
        expected = [
            ("Enviados", "emails_sent"),
            ("Aperturas", "unique_opens"),
            ("Clics", "unique_clicks"),
            ("Conversiones", "form_conversions"),
        ]
        assert config.funnel_steps == expected

    def test_no_frequency_alert(self) -> None:
        config = _CHANNEL_CONFIGS["email-nurture"]
        assert config.has_frequency_alert is False

    def test_timeseries_metrics_include_key_email_metrics(self) -> None:
        config = _CHANNEL_CONFIGS["email-nurture"]
        for metric in [
            "emails_sent",
            "unique_opens",
            "unique_clicks",
            "open_rate",
            "click_rate",
            "hard_bounces",
            "soft_bounces",
            "unsubscribes",
            "new_subscribers",
            "automation_completed",
        ]:
            assert metric in config.timeseries_metrics, f"{metric} missing from timeseries"

    def test_channel_name(self) -> None:
        config = _CHANNEL_CONFIGS["email-nurture"]
        assert config.channel_name == "Email Marketing"


class TestEmailDerivedMetrics:
    """Test _compute_derived_metrics for email-specific calculations."""

    def test_click_to_open_rate_when_missing(self) -> None:
        metrics: dict[str, float] = {
            "emails_sent": 1000,
            "unique_opens": 200,
            "unique_clicks": 30,
        }
        result = _compute_derived_metrics(metrics)
        assert result["click_to_open_rate"] == 15.0  # (30/200)*100

    def test_click_to_open_rate_not_overwritten(self) -> None:
        metrics: dict[str, float] = {
            "emails_sent": 1000,
            "unique_opens": 200,
            "unique_clicks": 30,
            "click_to_open_rate": 12.5,  # pre-existing from ETL
        }
        result = _compute_derived_metrics(metrics)
        assert result["click_to_open_rate"] == 12.5  # not overwritten

    def test_bounce_rate_computed(self) -> None:
        metrics: dict[str, float] = {
            "emails_sent": 1000,
            "hard_bounces": 5,
            "soft_bounces": 10,
            "unique_opens": 0,
            "unique_clicks": 0,
        }
        result = _compute_derived_metrics(metrics)
        assert result["bounce_rate"] == 1.5  # (15/1000)*100

    def test_unsubscribe_rate_computed(self) -> None:
        metrics: dict[str, float] = {
            "emails_sent": 2000,
            "unsubscribes": 4,
            "hard_bounces": 0,
            "soft_bounces": 0,
            "unique_opens": 0,
            "unique_clicks": 0,
        }
        result = _compute_derived_metrics(metrics)
        assert result["unsubscribe_rate"] == 0.2  # (4/2000)*100

    def test_no_division_by_zero_when_no_sends(self) -> None:
        metrics: dict[str, float] = {
            "emails_sent": 0,
            "unique_opens": 0,
            "unique_clicks": 0,
            "hard_bounces": 0,
            "soft_bounces": 0,
        }
        result = _compute_derived_metrics(metrics)
        assert "bounce_rate" not in result
        assert "unsubscribe_rate" not in result

    def test_no_ctor_when_no_opens(self) -> None:
        metrics: dict[str, float] = {
            "emails_sent": 100,
            "unique_opens": 0,
            "unique_clicks": 0,
        }
        result = _compute_derived_metrics(metrics)
        assert "click_to_open_rate" not in result


class TestEmailBenchmarks:
    """Test email benchmarks exist in industry_benchmarks.py."""

    @pytest.mark.parametrize(
        "metric_name,expected_median",
        [
            ("open_rate", 18.0),
            ("click_rate", 2.6),
            ("click_to_open_rate", 14.1),
            ("bounce_rate", 0.7),
            ("unsubscribe_rate", 0.1),
            ("completion_rate", 45.0),
        ],
    )
    def test_benchmark_exists_and_median(
        self,
        metric_name: str,
        expected_median: float,
    ) -> None:
        entry = get_benchmarks(IndustryCategory.GENERAL, metric_name)
        assert entry is not None, f"No benchmark for {metric_name}"
        assert entry.median == expected_median
        assert entry.unit == "percentage"


class TestEmailKpisAndFunnel:
    """Test KPI and funnel building for email-nurture channel."""

    def test_build_kpis_with_email_metrics(self) -> None:
        db = MagicMock()
        service = ChannelDashboardService(db)

        current = {
            "open_rate": 22.5,
            "click_rate": 3.1,
            "emails_sent": 5000,
            "active_subscribers": 12000,
        }
        previous = {
            "open_rate": 20.0,
            "click_rate": 2.8,
            "emails_sent": 4500,
            "active_subscribers": 11500,
        }

        config = _CHANNEL_CONFIGS["email-nurture"]
        kpis = service._build_kpis(current, previous, IndustryCategory.GENERAL, config)

        assert len(kpis) == 4
        names = [k.metric_name for k in kpis]
        assert names == ["open_rate", "click_rate", "emails_sent", "active_subscribers"]

    def test_build_funnel_with_email_steps(self) -> None:
        db = MagicMock()
        service = ChannelDashboardService(db)

        metrics = {
            "emails_sent": 5000,
            "unique_opens": 1000,
            "unique_clicks": 150,
            "form_conversions": 30,
        }
        config = _CHANNEL_CONFIGS["email-nurture"]
        funnel = service._build_funnel(metrics, config)

        assert len(funnel.steps) == 4
        assert funnel.steps[0].label == "Enviados"
        assert funnel.steps[0].value == 5000
        assert funnel.steps[1].label == "Aperturas"
        assert funnel.steps[1].value == 1000
        assert funnel.steps[1].conversion_rate_from_previous == 20.0  # 1000/5000*100
        assert funnel.steps[2].label == "Clics"
        assert funnel.steps[3].label == "Conversiones"


class TestMetaAdsRegressionAfterEmail:
    """Ensure Meta Ads config unchanged after adding email-nurture."""

    def test_meta_ads_still_exists(self) -> None:
        assert "meta-ads" in _CHANNEL_CONFIGS

    def test_meta_ads_hero_metrics_unchanged(self) -> None:
        config = _CHANNEL_CONFIGS["meta-ads"]
        assert "spend" in config.hero_metrics
        assert "ROAS" in config.hero_metrics

    def test_ig_organic_still_exists(self) -> None:
        assert "ig-organic" in _CHANNEL_CONFIGS

    def test_yt_organic_still_exists(self) -> None:
        assert "yt-organic" in _CHANNEL_CONFIGS
