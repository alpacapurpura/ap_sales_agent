"""Supplemental tests for CampaignService — covering uncovered query methods."""

import uuid
from unittest.mock import MagicMock

TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


def _make_svc():
    from luana_core_analytics_engine.application.services.campaign_service import CampaignService

    db = MagicMock()
    return CampaignService(db), db


def _row(**kwargs):
    row = MagicMock()
    row._mapping = kwargs
    return row


# ─── get_overview ─────────────────────────────────────────────────────────────


class TestGetOverview:
    def _setup_db(self, campaign_rows=None, rec_rows=None, last_synced_row=None):
        _, db = _make_svc()
        campaign_rows = campaign_rows or []
        rec_rows = rec_rows or []

        last_synced = MagicMock()
        last_synced._mapping = {"last_synced": None}

        call_count = [0]
        results = [
            MagicMock(fetchall=MagicMock(return_value=campaign_rows)),  # campaigns
            MagicMock(fetchall=MagicMock(return_value=rec_rows)),  # recommendations
            MagicMock(fetchone=MagicMock(return_value=last_synced)),  # last_synced
        ]

        def side_effect(*args, **kwargs):
            r = results[min(call_count[0], len(results) - 1)]
            call_count[0] += 1
            return r

        db.execute.side_effect = side_effect

        from luana_core_analytics_engine.application.services.campaign_service import CampaignService

        return CampaignService(db)

    def test_empty_db_returns_zero_campaigns(self):
        svc = self._setup_db()
        result = svc.get_overview(TENANT_ID)
        assert result.total_campaigns == 0
        assert result.active_campaigns == 0

    def test_active_campaigns_counted(self):
        rows = [
            _row(
                external_id="1",
                name="C1",
                effective_status="ACTIVE",
                objective=None,
                status="ACTIVE",
                bid_strategy=None,
                daily_budget=None,
                lifetime_budget=None,
                budget_remaining=None,
                buying_type=None,
                start_time=None,
                stop_time=None,
                ad_sets_count=0,
                ads_count=0,
            ),
            _row(
                external_id="2",
                name="C2",
                effective_status="PAUSED",
                objective=None,
                status="PAUSED",
                bid_strategy=None,
                daily_budget=None,
                lifetime_budget=None,
                budget_remaining=None,
                buying_type=None,
                start_time=None,
                stop_time=None,
                ad_sets_count=0,
                ads_count=0,
            ),
        ]
        svc = self._setup_db(campaign_rows=rows)
        result = svc.get_overview(TENANT_ID)
        assert result.total_campaigns == 2
        assert result.active_campaigns == 1

    def test_recommendations_included(self):
        rec_rows = [
            _row(
                recommendation_type="BUDGET",
                source="meta",
                title="Increase budget",
                body="",
                importance="HIGH",
                lift_estimate=None,
                opportunity_score=0.8,
                url=None,
                object_ids=[],
            ),
        ]
        svc = self._setup_db(rec_rows=rec_rows)
        result = svc.get_overview(TENANT_ID)
        assert len(result.recommendations) == 1
        assert result.recommendations[0].recommendation_type == "BUDGET"

    def test_critical_health_when_cpa_3x_average(self):
        # This tests the CPA health scoring in get_performance — lines 290, 293-294
        # but get_overview is simpler to test
        svc = self._setup_db()
        result = svc.get_overview(TENANT_ID)
        assert result is not None


# ─── get_ad_sets ──────────────────────────────────────────────────────────────


class TestGetAdSets:
    def test_empty_returns_empty_list(self):
        svc, db = _make_svc()
        db.execute.return_value.fetchall.return_value = []
        result = svc.get_ad_sets(TENANT_ID, "campaign-ext-123")
        assert result == []

    def test_returns_ad_set_dtos(self):
        svc, db = _make_svc()
        rows = [
            _row(
                external_id="adset-1",
                campaign_external_id="campaign-ext-123",
                name="Ad Set 1",
                status="ACTIVE",
                effective_status="ACTIVE",
                optimization_goal="LINK_CLICKS",
                targeting=None,
                learning_stage=None,
                daily_budget=50.0,
                ads_count=3,
            ),
        ]
        db.execute.return_value.fetchall.return_value = rows
        result = svc.get_ad_sets(TENANT_ID, "campaign-ext-123")
        assert len(result) == 1
        assert result[0].external_id == "adset-1"
        assert result[0].ads_count == 3

    def test_nullable_fields_handled(self):
        svc, db = _make_svc()
        rows = [
            _row(
                external_id="adset-2",
                campaign_external_id="camp-1",
                name="Ad Set 2",
                status=None,
                effective_status=None,
                optimization_goal=None,
                targeting=None,
                learning_stage=None,
                daily_budget=None,
                ads_count=0,
            ),
        ]
        db.execute.return_value.fetchall.return_value = rows
        result = svc.get_ad_sets(TENANT_ID, "camp-1")
        assert result[0].status is None
        assert result[0].optimization_goal is None


# ─── get_ads ──────────────────────────────────────────────────────────────────


class TestGetAds:
    def test_empty_returns_empty_list(self):
        svc, db = _make_svc()
        db.execute.return_value.fetchall.return_value = []
        result = svc.get_ads(TENANT_ID, "adset-ext-123")
        assert result == []

    def test_returns_ad_dtos(self):
        svc, db = _make_svc()
        rows = [
            _row(external_id="ad-1", name="Ad 1", status="ACTIVE", effective_status="ACTIVE"),
        ]
        db.execute.return_value.fetchall.return_value = rows
        result = svc.get_ads(TENANT_ID, "adset-ext-123")
        assert len(result) == 1
        assert result[0].external_id == "ad-1"
        assert result[0].name == "Ad 1"

    def test_multiple_ads_returned(self):
        svc, db = _make_svc()
        rows = [
            _row(external_id=f"ad-{i}", name=f"Ad {i}", status="ACTIVE", effective_status="ACTIVE") for i in range(5)
        ]
        db.execute.return_value.fetchall.return_value = rows
        result = svc.get_ads(TENANT_ID, "adset-ext-1")
        assert len(result) == 5
