"""Tests for EmailDashboardService pure functions."""

from src.modules.analytics.application.services.email_dashboard_service import (
    classify_engagement_segment,
    compute_health_score,
)


class TestHealthScore:
    """Health score computation from metric values."""

    def test_excellent_health(self):
        score = compute_health_score(
            open_rate=28.0,
            benchmark_open_rate=21.5,
            ctor=14.0,
            benchmark_ctor=10.5,
            deliverability_rate=98.0,
            list_growth_rate=5.0,
        )
        assert score.total >= 80
        assert all(s.color == "green" for s in score.sub_scores)

    def test_poor_engagement(self):
        score = compute_health_score(
            open_rate=10.0,
            benchmark_open_rate=21.5,
            ctor=4.0,
            benchmark_ctor=10.5,
            deliverability_rate=97.0,
            list_growth_rate=3.0,
        )
        engagement = next(s for s in score.sub_scores if s.area == "engagement")
        assert engagement.color == "red"
        assert score.total < 70

    def test_negative_growth(self):
        score = compute_health_score(
            open_rate=22.0,
            benchmark_open_rate=21.5,
            ctor=11.0,
            benchmark_ctor=10.5,
            deliverability_rate=97.0,
            list_growth_rate=-2.0,
        )
        growth = next(s for s in score.sub_scores if s.area == "crecimiento")
        assert growth.color == "red"

    def test_zero_values_no_division_error(self):
        """Health score must not crash when all inputs are zero."""
        score = compute_health_score(
            open_rate=0.0,
            benchmark_open_rate=21.5,
            ctor=0.0,
            benchmark_ctor=10.5,
            deliverability_rate=0.0,
            list_growth_rate=0.0,
        )
        assert 0 <= score.total <= 100
        assert len(score.sub_scores) == 4

    def test_low_deliverability(self):
        score = compute_health_score(
            open_rate=22.0,
            benchmark_open_rate=21.5,
            ctor=11.0,
            benchmark_ctor=10.5,
            deliverability_rate=88.0,
            list_growth_rate=3.0,
        )
        delivery = next(s for s in score.sub_scores if s.area == "entregabilidad")
        assert delivery.color in ("yellow", "red")


class TestEngagementSegmentation:
    """Segment classification based on engagement metrics."""

    def test_champion(self):
        seg = classify_engagement_segment(
            open_rate=65.0, click_rate=8.0, days_inactive=0
        )
        assert seg == "champions"

    def test_active(self):
        seg = classify_engagement_segment(
            open_rate=30.0, click_rate=2.0, days_inactive=5
        )
        assert seg == "activos"

    def test_at_risk(self):
        seg = classify_engagement_segment(
            open_rate=8.0, click_rate=0.3, days_inactive=45
        )
        assert seg == "en_riesgo"

    def test_dormant(self):
        seg = classify_engagement_segment(
            open_rate=0.5, click_rate=0.0, days_inactive=90
        )
        assert seg == "dormidos"
