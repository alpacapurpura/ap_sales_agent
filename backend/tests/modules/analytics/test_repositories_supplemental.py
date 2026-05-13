"""Tests for CaptureMetricsRepository, NurtureMetricsRepository,
PeriodMetricsRepository, and OfficialMetricsRepository — uncovered methods."""

import uuid
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, call

import pytest

TENANT_ID = uuid.uuid4()


def _dt(y: int, m: int, d: int) -> datetime:
    return datetime(y, m, d, tzinfo=timezone.utc)


def _d(y: int, m: int, d: int) -> date:
    return date(y, m, d)


# ─── CaptureMetricsRepository ─────────────────────────────────────────────────


def _make_capture_repo() -> tuple:
    from luana_core_analytics_engine.infrastructure.repositories.capture_repository import (
        CaptureMetricsRepository,
    )

    db = MagicMock()
    db.execute.return_value.all.return_value = []
    return CaptureMetricsRepository(db), db


class TestCaptureCountLeadsBySource:
    def test_empty_rows_returns_empty_dict(self):
        repo, db = _make_capture_repo()
        db.execute.return_value.all.return_value = []
        result = repo.count_leads_by_source(TENANT_ID, _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result == {}

    def test_rows_mapped_by_lead_source(self):
        repo, db = _make_capture_repo()
        row1 = MagicMock(lead_source="ig-dm", lead_count=10)
        row2 = MagicMock(lead_source="landing-form", lead_count=5)
        db.execute.return_value.all.return_value = [row1, row2]
        result = repo.count_leads_by_source(TENANT_ID, _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result["ig-dm"] == 10
        assert result["landing-form"] == 5

    def test_manychat_ig_consolidated_into_ig_dm(self):
        repo, db = _make_capture_repo()
        row1 = MagicMock(lead_source="ig-dm", lead_count=10)
        row2 = MagicMock(lead_source="manychat-ig", lead_count=5)
        db.execute.return_value.all.return_value = [row1, row2]
        result = repo.count_leads_by_source(TENANT_ID, _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result["ig-dm"] == 15
        assert "manychat-ig" not in result

    def test_manychat_wa_consolidated_into_whatsapp_inbound(self):
        repo, db = _make_capture_repo()
        row1 = MagicMock(lead_source="manychat-wa", lead_count=7)
        db.execute.return_value.all.return_value = [row1]
        result = repo.count_leads_by_source(TENANT_ID, _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result["whatsapp-inbound"] == 7
        assert "manychat-wa" not in result

    def test_manychat_ig_only_no_ig_dm_base(self):
        repo, db = _make_capture_repo()
        row1 = MagicMock(lead_source="manychat-ig", lead_count=3)
        db.execute.return_value.all.return_value = [row1]
        result = repo.count_leads_by_source(TENANT_ID, _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result["ig-dm"] == 3


class TestCaptureCountLeadsBySourceDetailed:
    def test_empty_rows_returns_empty_dict(self):
        repo, db = _make_capture_repo()
        db.execute.return_value.all.return_value = []
        result = repo.count_leads_by_source_detailed(TENANT_ID, _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result == {}

    def test_no_consolidation_in_detailed(self):
        repo, db = _make_capture_repo()
        row1 = MagicMock(lead_source="manychat-ig", lead_count=5)
        row2 = MagicMock(lead_source="ig-dm", lead_count=10)
        db.execute.return_value.all.return_value = [row1, row2]
        result = repo.count_leads_by_source_detailed(TENANT_ID, _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result["manychat-ig"] == 5
        assert result["ig-dm"] == 10


class TestCaptureCountConversationsByChannel:
    def test_empty_returns_empty_dict(self):
        repo, db = _make_capture_repo()
        db.execute.return_value.all.return_value = []
        result = repo.count_conversations_by_channel(TENANT_ID, _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result == {}

    def test_rows_with_channel_mapped(self):
        repo, db = _make_capture_repo()
        row1 = MagicMock(channel="ig-dm", conv_count=50)
        row2 = MagicMock(channel="whatsapp-inbound", conv_count=30)
        db.execute.return_value.all.return_value = [row1, row2]
        result = repo.count_conversations_by_channel(TENANT_ID, _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result["ig-dm"] == 50
        assert result["whatsapp-inbound"] == 30

    def test_none_channel_filtered_out(self):
        repo, db = _make_capture_repo()
        row1 = MagicMock(channel=None, conv_count=10)
        row2 = MagicMock(channel="ig-dm", conv_count=5)
        db.execute.return_value.all.return_value = [row1, row2]
        result = repo.count_conversations_by_channel(TENANT_ID, _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert None not in result
        assert result["ig-dm"] == 5


# ─── NurtureMetricsRepository ─────────────────────────────────────────────────


def _make_nurture_repo() -> tuple:
    from luana_core_analytics_engine.infrastructure.repositories.nurture_repository import (
        NurtureMetricsRepository,
    )

    db = MagicMock()
    db.execute.return_value.scalar.return_value = 0
    db.execute.return_value.all.return_value = []
    return NurtureMetricsRepository(db), db


class TestNurtureCountNewMqls:
    def test_returns_zero_when_no_data(self):
        repo, db = _make_nurture_repo()
        db.execute.return_value.scalar.return_value = None
        result = repo.count_new_mqls(TENANT_ID, _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result == 0

    def test_returns_int_count(self):
        repo, db = _make_nurture_repo()
        db.execute.return_value.scalar.return_value = 15
        result = repo.count_new_mqls(TENANT_ID, _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result == 15


class TestNurtureCountLeadsInPeriod:
    def test_returns_zero_when_none(self):
        repo, db = _make_nurture_repo()
        db.execute.return_value.scalar.return_value = None
        result = repo.count_leads_in_period(TENANT_ID, _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result == 0

    def test_returns_count(self):
        repo, db = _make_nurture_repo()
        db.execute.return_value.scalar.return_value = 42
        result = repo.count_leads_in_period(TENANT_ID, _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result == 42


class TestNurtureGetMqlSources:
    def test_empty_returns_empty_dict(self):
        repo, db = _make_nurture_repo()
        db.execute.return_value.all.return_value = []
        result = repo.get_mql_sources(TENANT_ID, _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result == {}

    def test_rows_mapped(self):
        repo, db = _make_nurture_repo()
        row1 = MagicMock(lead_source="mailerlite", count=5)
        row2 = MagicMock(lead_source="ig-dm", count=3)
        db.execute.return_value.all.return_value = [row1, row2]
        result = repo.get_mql_sources(TENANT_ID, _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result["mailerlite"] == 5
        assert result["ig-dm"] == 3


class TestNurtureCountFollowupEvents:
    def test_returns_sent_and_replied(self):
        repo, db = _make_nurture_repo()
        db.execute.return_value.scalar.side_effect = [8, 3]
        result = repo.count_followup_events(TENANT_ID, _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result["sent"] == 8
        assert result["replied"] == 3

    def test_zero_when_none_returned(self):
        repo, db = _make_nurture_repo()
        db.execute.return_value.scalar.side_effect = [None, None]
        result = repo.count_followup_events(TENANT_ID, _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result["sent"] == 0
        assert result["replied"] == 0


class TestNurtureCountEmailEvents:
    def test_returns_all_event_types(self):
        repo, db = _make_nurture_repo()
        db.execute.return_value.scalar.side_effect = [20, 5, 100]
        result = repo.count_email_events(TENANT_ID, _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result["opens"] == 20
        assert result["clicks"] == 5
        assert result["emails_sent"] == 100

    def test_zero_fallback(self):
        repo, db = _make_nurture_repo()
        db.execute.return_value.scalar.side_effect = [None, None, None]
        result = repo.count_email_events(TENANT_ID, _dt(2026, 3, 1), _dt(2026, 3, 31))
        assert result["opens"] == 0
        assert result["clicks"] == 0
        assert result["emails_sent"] == 0


# ─── PeriodMetricsRepository ──────────────────────────────────────────────────


def _make_period_repo() -> tuple:
    from luana_core_analytics_engine.infrastructure.repositories.period_metrics_repository import (
        PeriodMetricsRepository,
    )

    db = MagicMock()
    db.execute.return_value.scalars.return_value.all.return_value = []
    db.execute.return_value.first.return_value = None
    db.flush = MagicMock()
    return PeriodMetricsRepository(db), db


class TestPeriodUpsertMetrics:
    def test_empty_list_returns_zero(self):
        repo, db = _make_period_repo()
        result = repo.upsert_period_metrics([])
        assert result == 0
        db.execute.assert_not_called()

    def test_single_metric_returns_one(self):
        repo, db = _make_period_repo()
        metric = {
            "tenant_id": TENANT_ID,
            "provider": "meta",
            "channel_slug": "meta-ads",
            "metric_name": "impressions",
            "value": 1000.0,
            "unit": "count",
            "period_type": "last_30_days",
            "period_start": _d(2026, 3, 1),
            "period_end": _d(2026, 3, 31),
        }
        result = repo.upsert_period_metrics([metric])
        assert result == 1
        db.execute.assert_called_once()
        db.flush.assert_called_once()

    def test_auto_assigns_id_if_missing(self):
        repo, _db = _make_period_repo()
        metric = {
            "tenant_id": TENANT_ID,
            "provider": "meta",
            "channel_slug": "meta-ads",
            "metric_name": "reach",
            "value": 500.0,
            "unit": "count",
            "period_type": "last_30_days",
            "period_start": _d(2026, 3, 1),
            "period_end": _d(2026, 3, 31),
        }
        assert "id" not in metric
        repo.upsert_period_metrics([metric])
        assert "id" in metric

    def test_multiple_metrics_returns_count(self):
        repo, _db = _make_period_repo()
        metrics = [
            {
                "tenant_id": TENANT_ID,
                "provider": "meta",
                "channel_slug": "meta-ads",
                "metric_name": f"metric_{i}",
                "value": float(i),
                "unit": "count",
                "period_type": "last_30_days",
                "period_start": _d(2026, 3, 1),
                "period_end": _d(2026, 3, 31),
            }
            for i in range(3)
        ]
        result = repo.upsert_period_metrics(metrics)
        assert result == 3


class TestPeriodGetMetrics:
    def test_no_filters_executes_query(self):
        repo, db = _make_period_repo()
        repo.get_period_metrics(TENANT_ID)
        db.execute.assert_called_once()

    def test_all_filters_applied(self):
        repo, db = _make_period_repo()
        repo.get_period_metrics(
            TENANT_ID,
            channel_slug="meta-ads",
            metric_name="impressions",
            period_type="last_30_days",
            start_date=_d(2026, 3, 1),
            end_date=_d(2026, 3, 31),
        )
        db.execute.assert_called_once()

    def test_returns_list(self):
        repo, db = _make_period_repo()
        row = MagicMock()
        db.execute.return_value.scalars.return_value.all.return_value = [row]
        result = repo.get_period_metrics(TENANT_ID)
        assert len(result) == 1


class TestPeriodGetBestMetric:
    def test_no_match_returns_none(self):
        repo, db = _make_period_repo()
        db.execute.return_value.first.return_value = None
        result = repo.get_best_period_metric(TENANT_ID, "meta-ads", "impressions", _d(2026, 3, 1), _d(2026, 3, 31))
        assert result is None

    def test_match_returns_float(self):
        repo, db = _make_period_repo()
        row = MagicMock(value=5000)
        db.execute.return_value.first.return_value = row
        result = repo.get_best_period_metric(TENANT_ID, "meta-ads", "impressions", _d(2026, 3, 1), _d(2026, 3, 31))
        assert result == 5000.0


class TestPeriodGetExistingPeriods:
    def test_returns_set_of_dates(self):
        repo, db = _make_period_repo()
        d1 = _d(2026, 3, 1)
        d2 = _d(2026, 3, 8)
        db.execute.return_value.scalars.return_value.all.return_value = [d1, d2]
        result = repo.get_existing_periods(TENANT_ID, "meta", "weekly", _d(2026, 3, 1), _d(2026, 3, 31))
        assert isinstance(result, set)
        assert d1 in result
        assert d2 in result

    def test_empty_returns_empty_set(self):
        repo, db = _make_period_repo()
        db.execute.return_value.scalars.return_value.all.return_value = []
        result = repo.get_existing_periods(TENANT_ID, "meta", "weekly", _d(2026, 3, 1), _d(2026, 3, 31))
        assert result == set()


# ─── OfficialMetricsRepository ────────────────────────────────────────────────


def _make_official_repo() -> tuple:
    from luana_core_analytics_engine.infrastructure.repositories.official_metrics_repository import (
        OfficialMetricsRepository,
    )

    db = MagicMock()
    db.execute.return_value.all.return_value = []
    db.execute.return_value.scalars.return_value.all.return_value = []
    db.execute.return_value.first.return_value = None
    db.flush = MagicMock()
    return OfficialMetricsRepository(db), db


class TestOfficialUpsertFromStaging:
    def test_empty_returns_zero(self):
        repo, db = _make_official_repo()
        result = repo.upsert_from_staging([])
        assert result == 0
        db.execute.assert_not_called()

    def test_single_metric_returns_one(self):
        repo, db = _make_official_repo()
        metric = {
            "tenant_id": TENANT_ID,
            "provider": "meta",
            "channel_slug": "meta-ads",
            "metric_name": "impressions",
            "metric_date": _d(2026, 3, 15),
        }
        result = repo.upsert_from_staging([metric])
        assert result == 1
        db.flush.assert_called_once()

    def test_auto_assigns_id(self):
        repo, _db = _make_official_repo()
        metric = {
            "tenant_id": TENANT_ID,
            "provider": "meta",
            "channel_slug": "meta-ads",
            "metric_name": "impressions",
            "metric_date": _d(2026, 3, 15),
        }
        assert "id" not in metric
        repo.upsert_from_staging([metric])
        assert "id" in metric


class TestOfficialGetMetrics:
    def test_no_filters_queries(self):
        repo, db = _make_official_repo()
        repo.get_metrics(TENANT_ID)
        db.execute.assert_called_once()

    def test_with_all_filters(self):
        repo, db = _make_official_repo()
        repo.get_metrics(
            TENANT_ID,
            channel_slug="meta-ads",
            metric_name="impressions",
            start_date=_d(2026, 3, 1),
            end_date=_d(2026, 3, 31),
        )
        db.execute.assert_called_once()

    def test_returns_list(self):
        repo, db = _make_official_repo()
        row = MagicMock()
        db.execute.return_value.scalars.return_value.all.return_value = [row]
        result = repo.get_metrics(TENANT_ID)
        assert len(result) == 1


class TestOfficialGetExistingDates:
    def test_returns_set(self):
        repo, db = _make_official_repo()
        d1 = _d(2026, 3, 1)
        db.execute.return_value.scalars.return_value.all.return_value = [d1]
        result = repo.get_existing_dates(TENANT_ID, "meta", _d(2026, 3, 1), _d(2026, 3, 31))
        assert isinstance(result, set)
        assert d1 in result


class TestOfficialGetChannelSummary:
    def test_returns_list(self):
        repo, db = _make_official_repo()
        db.execute.return_value.scalars.return_value.all.return_value = []
        result = repo.get_channel_summary(TENANT_ID, "attraction")
        assert isinstance(result, list)


class TestOfficialUpsertIncrement:
    def test_executes_and_flushes(self):
        repo, db = _make_official_repo()
        repo.upsert_increment(
            tenant_id=TENANT_ID,
            provider="manychat",
            channel_slug="manychat-ig",
            metric_name="leads",
            value=1.0,
            unit="count",
            metric_date=_d(2026, 3, 15),
        )
        db.execute.assert_called_once()
        db.flush.assert_called_once()


class TestOfficialGetChannelMetrics:
    def test_empty_rows_returns_empty_dict(self):
        repo, db = _make_official_repo()
        db.execute.return_value.all.return_value = []
        result = repo.get_channel_metrics(TENANT_ID, "meta", "meta-ads", _d(2026, 3, 1), _d(2026, 3, 31))
        assert result == {}

    def test_additive_metric_summed(self):
        repo, db = _make_official_repo()
        row1 = MagicMock(metric_name="impressions", metric_date=_d(2026, 3, 1), value=500)
        row2 = MagicMock(metric_name="impressions", metric_date=_d(2026, 3, 2), value=300)
        db.execute.return_value.all.return_value = [row1, row2]
        result = repo.get_channel_metrics(TENANT_ID, "meta", "meta-ads", _d(2026, 3, 1), _d(2026, 3, 31))
        assert result["impressions"] == 800


class TestOfficialGetChannelDailyMetrics:
    def test_empty_returns_empty_list(self):
        repo, db = _make_official_repo()
        db.execute.return_value.all.return_value = []
        result = repo.get_channel_daily_metrics(TENANT_ID, "meta-ads", ["impressions"], _d(2026, 3, 1), _d(2026, 3, 31))
        assert result == []

    def test_account_rows_returned(self):
        repo, db = _make_official_repo()
        row = MagicMock(metric_date=_d(2026, 3, 1), metric_name="impressions", value=1000)
        row2 = MagicMock(metric_date=_d(2026, 3, 2), metric_name="impressions", total_value=500)
        db.execute.return_value.all.side_effect = [[row], [row2]]
        result = repo.get_channel_daily_metrics(TENANT_ID, "meta-ads", ["impressions"], _d(2026, 3, 1), _d(2026, 3, 31))
        assert len(result) >= 1


class TestOfficialGetChannelMetricsForPeriod:
    def test_empty_returns_empty_dict(self):
        repo, db = _make_official_repo()
        db.execute.return_value.all.return_value = []
        result = repo.get_channel_metrics_for_period(TENANT_ID, "meta-ads", _d(2026, 3, 1), _d(2026, 3, 31))
        assert result == {}


class TestOfficialGetChannelRawDailyRows:
    def test_empty_returns_empty_list(self):
        repo, db = _make_official_repo()
        db.execute.return_value.all.return_value = []
        result = repo.get_channel_raw_daily_rows(TENANT_ID, "meta-ads", _d(2026, 3, 1), _d(2026, 3, 31))
        assert result == []

    def test_rows_converted_to_tuples(self):
        repo, db = _make_official_repo()
        row = MagicMock(
            metric_date=_d(2026, 3, 1),
            metric_name="impressions",
            value=1000,
            campaign_id="camp1",
            ad_set_id=None,
            ad_id=None,
        )
        db.execute.return_value.all.return_value = [row]
        result = repo.get_channel_raw_daily_rows(TENANT_ID, "meta-ads", _d(2026, 3, 1), _d(2026, 3, 31))
        assert len(result) == 1
        assert result[0][0] == _d(2026, 3, 1)
        assert result[0][1] == "impressions"
        assert result[0][2] == 1000.0
        assert result[0][3] == "camp1"
