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
        # After bug fix: active_subscribers = completed + in_queue (was just in_queue)
        assert auto.active_subscribers == 11

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


# ---------------------------------------------------------------------------
# get_automations — bug fixes from UX redesign spec
# ---------------------------------------------------------------------------


def _make_rows_with_steps(
    automation_id: str = "auto-abc",
    completed_subs: int = 4,
    in_queue_subs: int = 5,
    status: str = "active",
    steps: list[dict] | None = None,
    emails_sent: float = 18.0,
    open_rate: float = 85.0,
    click_rate: float = 42.0,
    ctor: float = 49.0,
    unsubs: float = 1.0,
):
    """Build 5 metric rows for a single automation with custom extra.steps."""
    extra = json.dumps(
        {
            "source": "automation",
            "automation_name": "BIENVENIDA test",
            "automation_status": status,
            "automation_type": "welcome",
            "completed_subscribers": completed_subs,
            "subscribers_in_queue": in_queue_subs,
            "steps_count": len(steps) if steps else 0,
            "steps": steps or [],
        }
    )
    return [
        _AutoRow(automation_id, "emails_sent", emails_sent, extra, "2026-04-10"),
        _AutoRow(automation_id, "open_rate", open_rate, extra, "2026-04-10"),
        _AutoRow(automation_id, "click_rate", click_rate, extra, "2026-04-10"),
        _AutoRow(automation_id, "click_to_open_rate", ctor, extra, "2026-04-10"),
        _AutoRow(automation_id, "unsubscribes", unsubs, extra, "2026-04-10"),
    ]


class TestAutomationBugFixes:
    """Tests for the 3 data bugs fixed in the UX redesign + new fields."""

    def _run(self, service):
        import asyncio

        return asyncio.get_event_loop().run_until_complete(
            service.get_automations(TENANT_ID, "30d")
        )

    def test_active_subscribers_equals_completed_plus_queue(self):
        """Bug fix: active_subscribers was 0 because it only read in_queue."""
        rows = _make_rows_with_steps(completed_subs=4, in_queue_subs=5)
        service = _make_service_with_rows(rows)

        response = self._run(service)

        assert len(response.automations) == 1
        auto = response.automations[0]
        assert auto.active_subscribers == 9  # 4 completed + 5 in_queue

    def test_completion_rate_is_actual_completion_not_ctor(self):
        """Bug fix: completion_rate was mapping click_to_open_rate."""
        rows = _make_rows_with_steps(completed_subs=4, in_queue_subs=6, ctor=49.0)
        service = _make_service_with_rows(rows)

        response = self._run(service)

        auto = response.automations[0]
        # 4 / (4+6) * 100 = 40.0, NOT 49.0 (which was the CTOR)
        assert auto.completion_rate == 40.0
        assert auto.click_to_open_rate == 49.0  # CTOR lives in its own field

    def test_status_reads_from_extra_not_hardcoded(self):
        """Bug fix: status was always 'active' regardless of extra."""
        rows = _make_rows_with_steps(status="paused")
        service = _make_service_with_rows(rows)

        response = self._run(service)

        assert response.automations[0].status == "paused"

    def test_unsubscribes_populated(self):
        """New field: unsubscribes must come from the unsubscribes metric row."""
        rows = _make_rows_with_steps(unsubs=1.0)
        service = _make_service_with_rows(rows)

        response = self._run(service)

        assert response.automations[0].unsubscribes == 1

    def test_steps_populated_from_extra(self):
        """New field: steps must be parsed from extra.steps."""
        mock_steps = [
            {
                "step_id": "s1",
                "step_number": 1,
                "type": "email",
                "subject": "¡Hola!",
                "from_name": "Yo",
                "emails_sent": 9,
                "unique_opens": 9,
                "open_rate": 100.0,
                "unique_clicks": 5,
                "click_rate": 55.5,
                "unsubscribes": 0,
                "bounces": 0,
                "screenshot_url": "https://img/1.png",
                "preview_url": "https://preview/1",
                "delay_value": None,
                "delay_unit": None,
            },
            {
                "step_id": "s2",
                "step_number": 2,
                "type": "delay",
                "subject": None,
                "from_name": None,
                "emails_sent": 0,
                "unique_opens": 0,
                "open_rate": 0.0,
                "unique_clicks": 0,
                "click_rate": 0.0,
                "unsubscribes": 0,
                "bounces": 0,
                "screenshot_url": None,
                "preview_url": None,
                "delay_value": 2,
                "delay_unit": "days",
            },
        ]
        rows = _make_rows_with_steps(steps=mock_steps)
        service = _make_service_with_rows(rows)

        response = self._run(service)

        auto = response.automations[0]
        assert len(auto.steps) == 2
        assert auto.steps[0].subject == "¡Hola!"
        assert auto.steps[0].emails_sent == 9
        assert auto.steps[0].open_rate == 100.0
        assert auto.steps[0].screenshot_url == "https://img/1.png"
        assert auto.steps[1].type == "delay"
        assert auto.steps[1].delay_value == 2
        assert auto.steps[1].delay_unit == "days"

    def test_completion_rate_zero_when_no_ingresados(self):
        """Edge case: completion_rate returns 0.0 when no subscribers ingresaron."""
        rows = _make_rows_with_steps(
            completed_subs=0,
            in_queue_subs=0,
            emails_sent=0.0,
            open_rate=0.0,
            click_rate=0.0,
            ctor=0.0,
            unsubs=0.0,
        )
        service = _make_service_with_rows(rows)

        response = self._run(service)

        auto = response.automations[0]
        assert auto.active_subscribers == 0
        assert auto.completion_rate == 0.0
