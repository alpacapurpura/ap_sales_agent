"""Supplemental tests for CampaignService.get_performance — uncovered health branches."""

import uuid
from unittest.mock import MagicMock

TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


def _row(**kwargs):
    row = MagicMock()
    row._mapping = kwargs
    return row


def _make_svc_with_db():
    from luana_core_analytics_engine.application.services.campaign_service import CampaignService

    db = MagicMock()
    return CampaignService(db), db


def _camp_row(ext_id, effective_status="ACTIVE"):
    return _row(
        external_id=ext_id,
        name=f"Camp {ext_id}",
        objective=None,
        status="ACTIVE",
        effective_status=effective_status,
        bid_strategy=None,
        daily_budget=None,
        lifetime_budget=None,
        budget_remaining=None,
        start_time=None,
        stop_time=None,
        ad_sets_count=0,
        ads_count=0,
    )


def _metric_row(campaign_id, metric_name, value):
    return _row(campaign_id=campaign_id, metric_name=metric_name, total_value=value)


def _setup_db(db, camp_rows, metric_rows):
    currency_row = MagicMock()
    currency_row._mapping = {"currency": "USD"}
    last_synced_row = MagicMock()
    last_synced_row._mapping = {"last_synced": None}

    results = [
        MagicMock(fetchall=MagicMock(return_value=camp_rows)),  # camps
        MagicMock(fetchall=MagicMock(return_value=metric_rows)),  # metrics
        MagicMock(fetchall=MagicMock(return_value=[])),  # recs
        MagicMock(fetchone=MagicMock(return_value=currency_row)),  # currency
        MagicMock(fetchone=MagicMock(return_value=last_synced_row)),  # last_synced
    ]
    call_count = [0]

    def side_effect(*args, **kwargs):
        r = results[min(call_count[0], len(results) - 1)]
        call_count[0] += 1
        return r

    db.execute.side_effect = side_effect


class TestGetPerformanceHealthBranches:
    def test_health_warning_when_ratio_between_1_8_and_3(self):
        # 3 camps: two with cpa=5, one with cpa=20
        # avg = (5+5+20)/3 = 10; ratio_camp3 = 20/10 = 2.0 → "warning"
        svc, db = _make_svc_with_db()
        camp_rows = [
            _camp_row("c1"),
            _camp_row("c2"),
            _camp_row("c3"),
        ]
        metric_rows = [
            _metric_row("c1", "spend", 5.0),
            _metric_row("c1", "conversions", 1.0),
            _metric_row("c2", "spend", 5.0),
            _metric_row("c2", "conversions", 1.0),
            _metric_row("c3", "spend", 20.0),
            _metric_row("c3", "conversions", 1.0),
        ]
        _setup_db(db, camp_rows, metric_rows)
        result = svc.get_performance(TENANT_ID)
        health_values = {c.external_id: c.health for c in result.campaigns}
        assert health_values["c3"] == "warning"
        assert health_values["c1"] == "good"
        assert health_values["c2"] == "good"

    def test_health_critical_when_effective_status_with_issues(self):
        # Camp with no CPA (conversions=0) and effective_status="WITH_ISSUES"
        svc, db = _make_svc_with_db()
        camp_rows = [_camp_row("c_issues", effective_status="WITH_ISSUES")]
        metric_rows = []  # no metrics → no CPA
        _setup_db(db, camp_rows, metric_rows)
        result = svc.get_performance(TENANT_ID)
        assert result.campaigns[0].health == "critical"

    def test_health_good_when_no_cpa_and_not_with_issues(self):
        # Camp with no metrics, no WITH_ISSUES → health stays "good" (placeholder)
        svc, db = _make_svc_with_db()
        camp_rows = [_camp_row("c_plain", effective_status="PAUSED")]
        metric_rows = []
        _setup_db(db, camp_rows, metric_rows)
        result = svc.get_performance(TENANT_ID)
        assert result.campaigns[0].health == "good"
