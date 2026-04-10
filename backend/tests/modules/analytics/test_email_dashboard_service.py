"""Tests for EmailDashboardService pure functions."""

import json
import uuid
from collections import namedtuple
from unittest.mock import MagicMock

from src.modules.analytics.application.services.email_dashboard_service import (
    EmailDashboardService,
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


# ---------------------------------------------------------------------------
# get_automations — reads from official_metrics where source=automation
# ---------------------------------------------------------------------------

TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")

# Simulate rows from official_metrics grouped by campaign_id + metric_name
_AutoRow = namedtuple(
    "AutoRow", ["campaign_id", "metric_name", "total_value", "extra", "last_date"]
)


def _make_auto_rows():
    """Two automations with their metric rows."""
    extra_1 = json.dumps(
        {
            "source": "automation",
            "automation_name": "BIENVENIDA: nuevas inscritas",
            "automation_status": "active",
            "automation_type": "welcome",
            "completed_subscribers": 11,
            "subscribers_in_queue": 0,
            "steps_count": 2,
        }
    )
    extra_2 = json.dumps(
        {
            "source": "automation",
            "automation_name": "LISTA DE ESPERA WORKFLOW",
            "automation_status": "active",
            "automation_type": "workflow",
            "completed_subscribers": 0,
            "subscribers_in_queue": 9,
            "steps_count": 11,
        }
    )
    return [
        _AutoRow("auto_001", "emails_sent", 11.0, extra_1, "2026-04-10"),
        _AutoRow("auto_001", "open_rate", 100.0, extra_1, "2026-04-10"),
        _AutoRow("auto_001", "click_rate", 36.36, extra_1, "2026-04-10"),
        _AutoRow("auto_001", "click_to_open_rate", 36.36, extra_1, "2026-04-10"),
        _AutoRow("auto_001", "unsubscribes", 0.0, extra_1, "2026-04-10"),
        _AutoRow("auto_002", "emails_sent", 16.0, extra_2, "2026-04-10"),
        _AutoRow("auto_002", "open_rate", 62.5, extra_2, "2026-04-10"),
        _AutoRow("auto_002", "click_rate", 25.0, extra_2, "2026-04-10"),
        _AutoRow("auto_002", "click_to_open_rate", 40.0, extra_2, "2026-04-10"),
        _AutoRow("auto_002", "unsubscribes", 1.0, extra_2, "2026-04-10"),
    ]


def _make_service_with_rows(rows):
    """Create EmailDashboardService with mocked DB returning given rows."""
    mock_result = MagicMock()
    mock_result.all.return_value = rows

    mock_db = MagicMock()
    mock_db.execute.return_value = mock_result

    return EmailDashboardService(mock_db)


class TestGetAutomations:
    def test_returns_automation_list(self):
        service = _make_service_with_rows(_make_auto_rows())
        import asyncio

        result = asyncio.get_event_loop().run_until_complete(
            service.get_automations(TENANT_ID, "30d")
        )
        assert len(result.automations) == 2

    def test_automation_fields_populated(self):
        service = _make_service_with_rows(_make_auto_rows())
        import asyncio

        result = asyncio.get_event_loop().run_until_complete(
            service.get_automations(TENANT_ID, "30d")
        )
        auto = next(a for a in result.automations if a.automation_id == "auto_001")
        assert auto.name == "BIENVENIDA: nuevas inscritas"
        assert auto.automation_type == "welcome"
        assert auto.status == "active"
        assert auto.emails_sent == 11
        assert auto.open_rate == 100.0
        assert auto.click_rate == 36.4  # rounded to 1 decimal
        assert auto.completed == 11
        assert auto.active_subscribers == 0

    def test_kpis_computed(self):
        service = _make_service_with_rows(_make_auto_rows())
        import asyncio

        result = asyncio.get_event_loop().run_until_complete(
            service.get_automations(TENANT_ID, "30d")
        )
        assert len(result.kpis) > 0
        sent_kpi = next(
            (k for k in result.kpis if k.metric_name == "automation_emails_sent"), None
        )
        assert sent_kpi is not None
        assert sent_kpi.current_value == 27  # 11 + 16

    def test_empty_when_no_automation_rows(self):
        service = _make_service_with_rows([])
        import asyncio

        result = asyncio.get_event_loop().run_until_complete(
            service.get_automations(TENANT_ID, "30d")
        )
        assert result.automations == []
