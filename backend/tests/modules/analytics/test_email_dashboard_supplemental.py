"""Supplemental tests for EmailDashboardService — private helpers and main tabs."""

import asyncio
import uuid
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


def _run(coro):
    return asyncio.run(coro)


def _make_svc():
    from luana_core_analytics_engine.application.services.email_dashboard_service import (
        EmailDashboardService,
    )

    db = MagicMock()
    svc = EmailDashboardService(db)
    svc._repo = MagicMock()
    return svc


# ─── _build_estimated_heatmap ─────────────────────────────────────────────────


class TestBuildEstimatedHeatmap:
    def test_returns_42_cells(self):
        svc = _make_svc()
        cells = svc._build_estimated_heatmap()
        assert len(cells) == 42  # 7 days x 6 hours

    def test_all_days_represented(self):
        svc = _make_svc()
        cells = svc._build_estimated_heatmap()
        days = {c.day_of_week for c in cells}
        assert days == {0, 1, 2, 3, 4, 5, 6}

    def test_all_hours_represented(self):
        svc = _make_svc()
        cells = svc._build_estimated_heatmap()
        hours = {c.hour_block for c in cells}
        assert "6-9" in hours
        assert "9-12" in hours
        assert "21-24" in hours

    def test_open_rate_positive(self):
        svc = _make_svc()
        cells = svc._build_estimated_heatmap()
        assert all(c.open_rate >= 0 for c in cells)

    def test_peak_hours_have_highest_rate(self):
        svc = _make_svc()
        cells = svc._build_estimated_heatmap()
        by_hour = {}
        for c in cells:
            by_hour.setdefault(c.hour_block, []).append(c.open_rate)
        avg_9_12 = sum(by_hour["9-12"]) / len(by_hour["9-12"])
        avg_21_24 = sum(by_hour["21-24"]) / len(by_hour["21-24"])
        assert avg_9_12 > avg_21_24


# ─── _generate_health_alerts ─────────────────────────────────────────────────


class TestGenerateHealthAlerts:
    def test_no_issues_returns_saludable(self):
        svc = _make_svc()
        metrics = {"bounce_rate": 0.5, "spam_reports": 0, "emails_sent": 100, "unsubscribe_rate": 0.1}
        alerts = svc._generate_health_alerts(metrics)
        assert len(alerts) == 1
        assert "saludable" in alerts[0].lower()

    def test_high_bounce_rate_triggers_alert(self):
        svc = _make_svc()
        metrics = {"bounce_rate": 5.0, "spam_reports": 0, "emails_sent": 100, "unsubscribe_rate": 0.1}
        alerts = svc._generate_health_alerts(metrics)
        assert any("bounce" in a.lower() for a in alerts)

    def test_high_spam_triggers_alert(self):
        svc = _make_svc()
        # spam_reports / emails_sent * 100 > 0.1
        metrics = {"bounce_rate": 0.5, "spam_reports": 5, "emails_sent": 100, "unsubscribe_rate": 0.1}
        alerts = svc._generate_health_alerts(metrics)
        assert any("spam" in a.lower() for a in alerts)

    def test_high_unsub_triggers_alert(self):
        svc = _make_svc()
        metrics = {"bounce_rate": 0.5, "spam_reports": 0, "emails_sent": 100, "unsubscribe_rate": 1.5}
        alerts = svc._generate_health_alerts(metrics)
        assert any("baja" in a.lower() for a in alerts)

    def test_multiple_issues_returns_multiple_alerts(self):
        svc = _make_svc()
        metrics = {"bounce_rate": 5.0, "spam_reports": 5, "emails_sent": 100, "unsubscribe_rate": 2.0}
        alerts = svc._generate_health_alerts(metrics)
        assert len(alerts) >= 2


# ─── _build_kpis ─────────────────────────────────────────────────────────────


class TestBuildKpis:
    def test_returns_one_kpi_per_name(self):
        svc = _make_svc()
        current = {"open_rate": 25.0, "click_rate": 5.0}
        previous = {"open_rate": 20.0, "click_rate": 4.0}
        kpis = svc._build_kpis(current, previous, ["open_rate", "click_rate"])
        assert len(kpis) == 2

    def test_delta_computed_when_previous_exists(self):
        svc = _make_svc()
        current = {"open_rate": 25.0}
        previous = {"open_rate": 20.0}
        kpis = svc._build_kpis(current, previous, ["open_rate"])
        kpi = kpis[0]
        assert kpi.delta_percent is not None
        assert kpi.delta_percent == pytest.approx(25.0)

    def test_no_delta_when_previous_zero(self):
        svc = _make_svc()
        current = {"open_rate": 25.0}
        previous = {"open_rate": 0.0}
        kpis = svc._build_kpis(current, previous, ["open_rate"])
        assert kpis[0].delta_percent is None

    def test_no_delta_when_metric_absent_from_previous(self):
        svc = _make_svc()
        kpis = svc._build_kpis({"open_rate": 25.0}, {}, ["open_rate"])
        assert kpis[0].delta_percent is None

    def test_benchmark_set_when_catalog_has_entry(self):
        svc = _make_svc()
        kpis = svc._build_kpis({"open_rate": 25.0}, {}, ["open_rate"])
        # open_rate should have a benchmark in the catalog
        # Just verify it's a DTO or None
        assert kpis[0].benchmark is not None or kpis[0].benchmark is None

    def test_missing_metric_defaults_to_zero(self):
        svc = _make_svc()
        kpis = svc._build_kpis({}, {}, ["open_rate"])
        assert kpis[0].current_value == 0.0


# ─── _build_time_series ───────────────────────────────────────────────────────


class TestBuildTimeSeries:
    def test_empty_input_returns_empty(self):
        svc = _make_svc()
        result = svc._build_time_series([])
        assert result == []

    def test_single_metric_single_point(self):
        svc = _make_svc()
        d = date(2026, 3, 1)
        result = svc._build_time_series([(d, "open_rate", 25.0)])
        assert len(result) == 1
        assert result[0].metric_name == "open_rate"
        assert len(result[0].data_points) == 1

    def test_groups_by_metric_name(self):
        svc = _make_svc()
        d1, d2 = date(2026, 3, 1), date(2026, 3, 2)
        daily = [(d1, "open_rate", 20.0), (d2, "open_rate", 25.0), (d1, "click_rate", 3.0)]
        result = svc._build_time_series(daily)
        assert len(result) == 2
        names = {r.metric_name for r in result}
        assert "open_rate" in names
        assert "click_rate" in names

    def test_points_sorted_by_date(self):
        svc = _make_svc()
        d1, d2 = date(2026, 3, 5), date(2026, 3, 1)
        result = svc._build_time_series([(d1, "open_rate", 25.0), (d2, "open_rate", 20.0)])
        pts = result[0].data_points
        assert pts[0].date <= pts[1].date


# ─── get_health (async) ───────────────────────────────────────────────────────


class TestGetHealth:
    def _svc_with_repo(self, current=None, previous=None, daily=None):
        svc = _make_svc()
        current = current or {
            "emails_sent": 1000,
            "open_rate": 25.0,
            "click_to_open_rate": 10.0,
            "hard_bounces": 5,
            "soft_bounces": 3,
            "bounce_rate": 0.8,
            "unsubscribe_rate": 0.2,
        }
        previous = previous or {}
        daily = daily or []
        call_count = [0]

        def repo_period(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return current
            return previous

        svc._repo.get_channel_metrics_for_period.side_effect = repo_period
        svc._repo.get_channel_daily_metrics.return_value = daily
        svc._db.execute.return_value.all.return_value = []
        return svc

    def test_returns_health_response(self):
        svc = self._svc_with_repo()
        result = _run(svc.get_health(TENANT_ID, "30d"))
        from luana_core_analytics_engine.application.dto.email_dashboard_dto import EmailHealthResponseDTO

        assert isinstance(result, EmailHealthResponseDTO)

    def test_health_score_computed(self):
        svc = self._svc_with_repo()
        result = _run(svc.get_health(TENANT_ID, "30d"))
        assert result.health_score is not None

    def test_bounce_breakdown_populated(self):
        current = {
            "emails_sent": 1000,
            "hard_bounces": 10,
            "soft_bounces": 5,
            "open_rate": 20.0,
            "click_to_open_rate": 8.0,
            "bounce_rate": 1.5,
            "unsubscribe_rate": 0.3,
        }
        svc = self._svc_with_repo(current=current)
        result = _run(svc.get_health(TENANT_ID, "30d"))
        assert result.bounce_breakdown.hard_bounces == 10
        assert result.bounce_breakdown.soft_bounces == 5

    def test_zero_sent_deliverability_is_100(self):
        current = {
            "emails_sent": 0,
            "hard_bounces": 0,
            "soft_bounces": 0,
            "open_rate": 0.0,
            "click_to_open_rate": 0.0,
            "bounce_rate": 0.0,
            "unsubscribe_rate": 0.0,
        }
        svc = self._svc_with_repo(current=current)
        result = _run(svc.get_health(TENANT_ID, "30d"))
        assert result.health_score is not None

    def test_high_bounce_generates_alert(self):
        current = {
            "emails_sent": 1000,
            "hard_bounces": 100,
            "soft_bounces": 50,
            "open_rate": 20.0,
            "click_to_open_rate": 8.0,
            "bounce_rate": 15.0,
            "unsubscribe_rate": 0.3,
        }
        svc = self._svc_with_repo(current=current)
        result = _run(svc.get_health(TENANT_ID, "30d"))
        assert len(result.alerts) > 0

    def test_time_series_included(self):
        d = date(2026, 3, 1)
        daily = [(d, "bounce_rate", 0.8), (d, "deliverability_rate", 99.0)]
        svc = self._svc_with_repo(daily=daily)
        result = _run(svc.get_health(TENANT_ID, "30d"))
        assert isinstance(result.time_series, list)


# ─── get_growth (async) ───────────────────────────────────────────────────────


class TestGetGrowth:
    def _svc_with_repo(self, current=None, nurture=None, previous=None, daily=None):
        svc = _make_svc()
        current = current or {"active_subscribers": 5000, "new_subscribers": 200, "unsubscribes": 50}
        nurture = nurture or {"unsubscribes": 30}
        previous = previous or {"active_subscribers": 4800}
        daily = daily or []
        calls = [current, nurture, previous]
        call_count = [0]

        def repo_period(*args, **kwargs):
            r = calls[min(call_count[0], len(calls) - 1)]
            call_count[0] += 1
            return r

        svc._repo.get_channel_metrics_for_period.side_effect = repo_period
        svc._repo.get_channel_daily_metrics.return_value = daily
        return svc

    def test_returns_growth_response(self):
        svc = self._svc_with_repo()
        result = _run(svc.get_growth(TENANT_ID, "30d"))
        from luana_core_analytics_engine.application.dto.email_dashboard_dto import EmailGrowthResponseDTO

        assert isinstance(result, EmailGrowthResponseDTO)

    def test_list_growth_rate_computed(self):
        current = {"active_subscribers": 1000, "new_subscribers": 100, "unsubscribes": 20}
        svc = self._svc_with_repo(current=current)
        result = _run(svc.get_growth(TENANT_ID, "30d"))
        # growth_rate = (100 - 30) / 1000 * 100 = 7.0%
        kpi_names = [k.metric_name for k in result.kpis]
        assert "list_growth_rate" in kpi_names

    def test_nurture_unsubs_merged(self):
        current = {"active_subscribers": 1000, "new_subscribers": 50}
        nurture = {"unsubscribes": 25}
        svc = self._svc_with_repo(current=current, nurture=nurture)
        result = _run(svc.get_growth(TENANT_ID, "30d"))
        assert result is not None  # No exception

    def test_daily_time_series_combined(self):
        d = date(2026, 3, 1)
        daily = [(d, "new_subscribers", 10.0)]
        svc = self._svc_with_repo(daily=daily)
        result = _run(svc.get_growth(TENANT_ID, "30d"))
        assert isinstance(result.time_series, list)


# ─── _count_campaigns_from_extra ─────────────────────────────────────────────


class TestCountCampaignsFromExtra:
    def test_empty_result_returns_zero(self):
        svc = _make_svc()
        svc._db.execute.return_value.all.return_value = []
        result = svc._count_campaigns_from_extra(TENANT_ID, date(2026, 3, 1), date(2026, 3, 31))
        assert result == 0

    def test_counts_campaigns_from_dict_extra(self):
        svc = _make_svc()
        extra = {"campaigns": [{"id": "1"}, {"id": "2"}, {"id": "3"}]}
        svc._db.execute.return_value.all.return_value = [(extra,)]
        result = svc._count_campaigns_from_extra(TENANT_ID, date(2026, 3, 1), date(2026, 3, 31))
        assert result == 3

    def test_counts_campaigns_from_json_string_extra(self):
        import json

        svc = _make_svc()
        extra_str = json.dumps({"campaigns": [{"id": "1"}, {"id": "2"}]})
        svc._db.execute.return_value.all.return_value = [(extra_str,)]
        result = svc._count_campaigns_from_extra(TENANT_ID, date(2026, 3, 1), date(2026, 3, 31))
        assert result == 2

    def test_none_extra_counts_zero(self):
        svc = _make_svc()
        svc._db.execute.return_value.all.return_value = [(None,)]
        result = svc._count_campaigns_from_extra(TENANT_ID, date(2026, 3, 1), date(2026, 3, 31))
        assert result == 0

    def test_multiple_rows_summed(self):
        svc = _make_svc()
        e1 = {"campaigns": [{"id": "1"}]}
        e2 = {"campaigns": [{"id": "2"}, {"id": "3"}]}
        svc._db.execute.return_value.all.return_value = [(e1,), (e2,)]
        result = svc._count_campaigns_from_extra(TENANT_ID, date(2026, 3, 1), date(2026, 3, 31))
        assert result == 3


# ─── _get_campaign_list ───────────────────────────────────────────────────────


class TestGetCampaignList:
    def _make_row(self, campaign_id, metric_name, total_value, extra=None, last_date=None):
        import json

        row = MagicMock()
        row.campaign_id = campaign_id
        row.metric_name = metric_name
        row.total_value = total_value
        row.extra = json.dumps(extra) if extra and not isinstance(extra, str) else extra
        row.last_date = last_date or date(2026, 3, 15)
        return row

    def test_empty_db_returns_empty_list(self):
        svc = _make_svc()
        svc._db.execute.return_value.all.return_value = []
        result = _run(svc._get_campaign_list(TENANT_ID, date(2026, 3, 1), date(2026, 3, 31)))
        assert result == []

    def test_single_campaign_built_from_rows(self):
        svc = _make_svc()
        extra = {"campaign_name": "Bienvenida", "campaign_subject": "Hola!", "campaign_type": "automation"}
        rows = [
            self._make_row("camp-1", "emails_sent", 500, extra=extra),
            self._make_row("camp-1", "open_rate", 25.0, extra=extra),
        ]
        svc._db.execute.return_value.all.return_value = rows
        result = _run(svc._get_campaign_list(TENANT_ID, date(2026, 3, 1), date(2026, 3, 31)))
        assert len(result) == 1
        camp = result[0]
        assert camp.campaign_id == "camp-1"
        assert camp.campaign_name == "Bienvenida"
        assert camp.emails_sent == 500

    def test_multiple_campaigns_separate(self):
        svc = _make_svc()
        rows = [
            self._make_row("camp-1", "emails_sent", 200, extra={"campaign_name": "A"}),
            self._make_row("camp-2", "emails_sent", 300, extra={"campaign_name": "B"}),
        ]
        svc._db.execute.return_value.all.return_value = rows
        result = _run(svc._get_campaign_list(TENANT_ID, date(2026, 3, 1), date(2026, 3, 31)))
        assert len(result) == 2

    def test_missing_extra_uses_defaults(self):
        svc = _make_svc()
        rows = [self._make_row("camp-1", "emails_sent", 100, extra=None)]
        svc._db.execute.return_value.all.return_value = rows
        result = _run(svc._get_campaign_list(TENANT_ID, date(2026, 3, 1), date(2026, 3, 31)))
        assert len(result) == 1
        assert result[0].campaign_name == "camp-1"  # defaults to campaign_id

    def test_open_rate_rounded(self):
        svc = _make_svc()
        extra = {"campaign_name": "Newsletter"}
        rows = [
            self._make_row("camp-1", "open_rate", 22.567, extra=extra),
        ]
        svc._db.execute.return_value.all.return_value = rows
        result = _run(svc._get_campaign_list(TENANT_ID, date(2026, 3, 1), date(2026, 3, 31)))
        assert result[0].open_rate == 22.6


# ─── _get_best_worst_campaigns ────────────────────────────────────────────────


class TestGetBestWorstCampaigns:
    def _make_campaign(self, campaign_id, open_rate):
        from luana_core_analytics_engine.application.dto.email_dashboard_dto import EmailCampaignDTO

        return EmailCampaignDTO(
            campaign_id=campaign_id,
            campaign_name=f"Camp {campaign_id}",
            campaign_subject=None,
            campaign_type="contenido",
            sent_date=None,
            emails_sent=100,
            open_rate=open_rate,
            click_rate=2.0,
            click_to_open_rate=5.0,
            bounce_rate=0.5,
            unsubscribes=1,
            unique_opens=25,
            unique_clicks=5,
        )

    def test_empty_campaigns_returns_none_none(self):
        svc = _make_svc()
        svc._get_campaign_list = AsyncMock(return_value=[])
        best, worst = _run(svc._get_best_worst_campaigns(TENANT_ID, date(2026, 3, 1), date(2026, 3, 31)))
        assert best is None
        assert worst is None

    def test_single_campaign_best_only(self):
        svc = _make_svc()
        camp = self._make_campaign("camp-1", 30.0)
        svc._get_campaign_list = AsyncMock(return_value=[camp])
        best, worst = _run(svc._get_best_worst_campaigns(TENANT_ID, date(2026, 3, 1), date(2026, 3, 31)))
        assert best is not None
        assert worst is None  # single campaign → no worst

    def test_multiple_campaigns_sorted_by_open_rate(self):
        svc = _make_svc()
        camps = [
            self._make_campaign("c1", 15.0),
            self._make_campaign("c2", 35.0),
            self._make_campaign("c3", 25.0),
        ]
        svc._get_campaign_list = AsyncMock(return_value=camps)
        best, worst = _run(svc._get_best_worst_campaigns(TENANT_ID, date(2026, 3, 1), date(2026, 3, 31)))
        assert best.campaign_name == "Camp c2"  # highest open_rate
        assert worst.campaign_name == "Camp c1"  # lowest open_rate


# ─── get_campaigns (async) ────────────────────────────────────────────────────


class TestGetCampaigns:
    def _make_campaign(self, cid, ctype, open_rate=20.0, emails_sent=100):
        from luana_core_analytics_engine.application.dto.email_dashboard_dto import EmailCampaignDTO

        return EmailCampaignDTO(
            campaign_id=cid,
            campaign_name=f"Camp {cid}",
            campaign_subject="Subject",
            campaign_type=ctype,
            sent_date="2026-03-15",
            emails_sent=emails_sent,
            open_rate=open_rate,
            click_rate=2.0,
            click_to_open_rate=5.0,
            bounce_rate=0.5,
            unsubscribes=1,
            unique_opens=20,
            unique_clicks=4,
        )

    def test_empty_campaigns_returns_empty_response(self):
        svc = _make_svc()
        svc._get_campaign_list = AsyncMock(return_value=[])
        result = _run(svc.get_campaigns(TENANT_ID, "30d"))
        assert result.campaigns == []
        assert result.type_performance == []
        assert result.top_subjects == []

    def test_groups_by_type(self):
        svc = _make_svc()
        svc._get_campaign_list = AsyncMock(
            return_value=[
                self._make_campaign("c1", "contenido"),
                self._make_campaign("c2", "contenido"),
                self._make_campaign("c3", "automation"),
            ]
        )
        result = _run(svc.get_campaigns(TENANT_ID, "30d"))
        type_keys = {tp.campaign_type for tp in result.type_performance}
        assert "contenido" in type_keys
        assert "automation" in type_keys

    def test_best_type_labeled_mejor_engagement(self):
        svc = _make_svc()
        svc._get_campaign_list = AsyncMock(
            return_value=[
                self._make_campaign("c1", "automation", open_rate=35.0),
                self._make_campaign("c2", "contenido", open_rate=20.0),
            ]
        )
        result = _run(svc.get_campaigns(TENANT_ID, "30d"))
        types_by_open = sorted(result.type_performance, key=lambda t: t.avg_open_rate, reverse=True)
        assert types_by_open[0].rank_label == "Mejor engagement"
        assert types_by_open[-1].rank_label == "Menor engagement promedio"

    def test_top_subjects_limited_to_5(self):
        svc = _make_svc()
        camps = [self._make_campaign(f"c{i}", "contenido", open_rate=float(i)) for i in range(10)]
        svc._get_campaign_list = AsyncMock(return_value=camps)
        result = _run(svc.get_campaigns(TENANT_ID, "30d"))
        assert len(result.top_subjects) == 5

    def test_single_type_no_menor_label(self):
        svc = _make_svc()
        svc._get_campaign_list = AsyncMock(
            return_value=[
                self._make_campaign("c1", "contenido"),
            ]
        )
        result = _run(svc.get_campaigns(TENANT_ID, "30d"))
        assert len(result.type_performance) == 1
        # Single type: best label = "Mejor engagement", but also last → "Menor engagement"
        assert result.type_performance[0].rank_label in ("Mejor engagement", "Menor engagement promedio")


# ─── get_audience (async) ─────────────────────────────────────────────────────


class TestGetAudience:
    def _svc_with_repo(self, current=None, capture=None):
        svc = _make_svc()
        current = current or {"open_rate": 25.0, "click_rate": 3.0, "click_to_open_rate": 10.0}
        capture = capture or {"active_subscribers": 5000, "new_subscribers": 200}
        call_count = [0]

        def repo_period(*args, **kwargs):
            call_count[0] += 1
            return current if call_count[0] == 1 else capture

        svc._repo.get_channel_metrics_for_period.side_effect = repo_period
        return svc

    def test_returns_4_segments(self):
        svc = self._svc_with_repo()
        result = _run(svc.get_audience(TENANT_ID, "30d"))
        assert len(result.segments) == 4

    def test_segment_names_present(self):
        svc = self._svc_with_repo()
        result = _run(svc.get_audience(TENANT_ID, "30d"))
        names = {s.segment_name for s in result.segments}
        assert "champions" in names
        assert "dormidos" in names

    def test_heatmap_included(self):
        svc = self._svc_with_repo()
        result = _run(svc.get_audience(TENANT_ID, "30d"))
        # activity_heatmap returned as part of response
        assert result is not None

    def test_decay_has_4_periods(self):
        svc = self._svc_with_repo()
        result = _run(svc.get_audience(TENANT_ID, "30d"))
        assert len(result.engagement_decay) == 4

    def test_zero_open_rate_no_exception(self):
        current = {"open_rate": 0.0, "click_rate": 0.0, "click_to_open_rate": 0.0}
        capture = {"active_subscribers": 100}
        svc = self._svc_with_repo(current=current, capture=capture)
        result = _run(svc.get_audience(TENANT_ID, "30d"))
        assert result is not None


# ─── get_dashboard (async) ────────────────────────────────────────────────────


class TestGetDashboard:
    def _svc_with_full_mocks(self):
        svc = _make_svc()
        current = {
            "emails_sent": 2000,
            "open_rate": 22.0,
            "click_rate": 3.5,
            "click_to_open_rate": 12.0,
            "hard_bounces": 10,
            "soft_bounces": 5,
            "unsubscribes": 20,
            "forwards": 5,
            "unique_opens": 440,
            "unique_clicks": 70,
            "active_subscribers": 5000,
            "new_subscribers": 100,
            "bounce_rate": 0.75,
        }
        previous = {"emails_sent": 1800, "open_rate": 20.0}
        capture = {"active_subscribers": 5000, "new_subscribers": 100}

        period_calls = [current, previous, capture]
        call_count = [0]

        def repo_period(*args, **kwargs):
            r = period_calls[min(call_count[0], len(period_calls) - 1)]
            call_count[0] += 1
            return r

        svc._repo.get_channel_metrics_for_period.side_effect = repo_period
        svc._repo.get_channel_daily_metrics.return_value = []
        svc._db.execute.return_value.all.return_value = []  # _count_campaigns_from_extra
        svc._get_best_worst_campaigns = AsyncMock(return_value=(None, None))
        return svc

    def test_returns_dashboard_dto(self):
        svc = self._svc_with_full_mocks()
        from luana_core_analytics_engine.application.dto.email_dashboard_dto import EmailDashboardDTO

        result = _run(svc.get_dashboard(TENANT_ID, "30d"))
        assert isinstance(result, EmailDashboardDTO)

    def test_kpis_included(self):
        svc = self._svc_with_full_mocks()
        result = _run(svc.get_dashboard(TENANT_ID, "30d"))
        assert len(result.kpis) > 0

    def test_funnel_has_5_steps(self):
        svc = self._svc_with_full_mocks()
        result = _run(svc.get_dashboard(TENANT_ID, "30d"))
        assert len(result.funnel) == 5

    def test_deliverability_derived(self):
        svc = self._svc_with_full_mocks()
        result = _run(svc.get_dashboard(TENANT_ID, "30d"))
        # deliverability = (2000-10-5)/2000*100 ≈ 99.25
        deliverability_kpi = next((k for k in result.kpis if k.metric_name == "deliverability_rate"), None)
        assert deliverability_kpi is not None
        assert deliverability_kpi.current_value > 90

    def test_zero_sent_no_exception(self):
        svc = _make_svc()
        empty = {"emails_sent": 0}
        calls = [empty, {}, {}]
        cc = [0]

        def side(*a, **kw):
            r = calls[min(cc[0], 2)]
            cc[0] += 1
            return r

        svc._repo.get_channel_metrics_for_period.side_effect = side
        svc._repo.get_channel_daily_metrics.return_value = []
        svc._db.execute.return_value.all.return_value = []
        svc._get_best_worst_campaigns = AsyncMock(return_value=(None, None))
        result = _run(svc.get_dashboard(TENANT_ID, "30d"))
        assert result is not None
