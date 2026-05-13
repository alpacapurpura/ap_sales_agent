"""Supplemental tests for ChannelDashboardService — uncovered branches."""

import uuid
from datetime import date
from unittest.mock import MagicMock

TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


def _make_svc():
    from luana_core_analytics_engine.application.services.channel_dashboard_service import (
        ChannelDashboardService,
    )

    db = MagicMock()
    svc = ChannelDashboardService.__new__(ChannelDashboardService)
    svc.repo = MagicMock()
    svc.repo.db = db
    return svc, db


def _make_row(**kwargs):
    row = MagicMock()
    row._mapping = kwargs
    return row


# ─── _build_time_series ───────────────────────────────────────────────────────


class TestBuildTimeSeries:
    def _svc(self):
        svc, _ = _make_svc()
        return svc

    def test_empty_returns_empty(self):
        svc = self._svc()
        result = svc._build_time_series([])
        assert result == []

    def test_known_metric_has_display_name(self):
        svc = self._svc()
        d = date(2026, 3, 1)
        result = svc._build_time_series([(d, "reach", 1000.0)])
        assert len(result) == 1
        assert result[0].metric_name == "reach"
        assert result[0].display_name != "reach"  # got a real display name from catalog

    def test_unknown_metric_falls_back_to_name(self):
        svc = self._svc()
        d = date(2026, 3, 1)
        result = svc._build_time_series([(d, "xyz_totally_unknown_999", 42.0)])
        assert len(result) == 1
        assert result[0].metric_name == "xyz_totally_unknown_999"
        assert result[0].display_name == "xyz_totally_unknown_999"
        assert result[0].unit == "count"

    def test_multiple_metrics_grouped(self):
        svc = self._svc()
        d = date(2026, 3, 1)
        data = [(d, "reach", 100.0), (d, "impressions", 200.0)]
        result = svc._build_time_series(data)
        names = {r.metric_name for r in result}
        assert "reach" in names
        assert "impressions" in names

    def test_same_metric_multiple_days_sorted(self):
        svc = self._svc()
        d1 = date(2026, 3, 1)
        d2 = date(2026, 3, 3)
        d_mid = date(2026, 3, 2)
        data = [(d2, "reach", 300.0), (d1, "reach", 100.0), (d_mid, "reach", 200.0)]
        result = svc._build_time_series(data)
        assert len(result) == 1
        dates = [p.date for p in result[0].data_points]
        assert dates == [d1.isoformat(), d_mid.isoformat(), d2.isoformat()]

    def test_data_points_rounded(self):
        svc = self._svc()
        d = date(2026, 3, 1)
        result = svc._build_time_series([(d, "reach", 123.456789)])
        assert result[0].data_points[0].value == 123.46


# ─── get_demographics — uncovered branches ───────────────────────────────────


class TestGetDemographicsEdgeCases:
    def test_unknown_metric_category_skipped(self):
        svc, db = _make_svc()
        # Row with metric_name not in _METRIC_TO_CATEGORY → category is None → continue (line 802)
        row = _make_row(
            metric_name="totally_unknown_metric",
            extra={"breakdowns": [{"label": "18-24", "value": 0.3}]},
        )
        db.execute.return_value.fetchall.return_value = [row]
        result = svc.get_demographics(TENANT_ID, "meta-ads")
        assert result.age == []
        assert result.gender == []
        assert result.placement == []

    def test_extra_raw_invalid_json_string_skips_row(self):
        svc, db = _make_svc()
        # extra_raw is invalid JSON string → except path (lines 810-811)
        row = _make_row(
            metric_name="meta_reach_by_age",
            extra="not-valid-json{{{",
        )
        db.execute.return_value.fetchall.return_value = [row]
        result = svc.get_demographics(TENANT_ID, "meta-ads")
        assert result.age == []  # breakdowns empty → skipped

    def test_extra_raw_non_str_non_dict_skips_row(self):
        svc, db = _make_svc()
        # extra_raw is int → else branch (line 815) → extra = {}
        row = _make_row(
            metric_name="meta_reach_by_age",
            extra=42,
        )
        db.execute.return_value.fetchall.return_value = [row]
        result = svc.get_demographics(TENANT_ID, "meta-ads")
        assert result.age == []

    def test_duplicate_category_skipped(self):
        svc, db = _make_svc()
        # Two rows for age → second row skipped (category in seen_categories, line 802)
        row1 = _make_row(
            metric_name="meta_reach_by_age",
            extra={"breakdowns": [{"label": "18-24", "value": 0.5}]},
        )
        row2 = _make_row(
            metric_name="meta_reach_by_age",
            extra={"breakdowns": [{"label": "25-34", "value": 0.5}]},
        )
        db.execute.return_value.fetchall.return_value = [row1, row2]
        result = svc.get_demographics(TENANT_ID, "meta-ads")
        # Only first row processed (category already seen for second)
        assert len(result.age) == 1
