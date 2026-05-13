"""Tests for campaign performance aggregation."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import UUID

from luana_core_analytics_engine.application.services.campaign_service import CampaignService

TENANT_ID = UUID("11111111-1111-1111-1111-111111111111")


class TestGetPerformance:
    """Tests for CampaignService.get_performance()."""

    def _make_campaign_row(self, **overrides):
        defaults = {
            "external_id": "camp_1",
            "name": "Test Campaign",
            "objective": "OUTCOME_SALES",
            "status": "ACTIVE",
            "effective_status": "ACTIVE",
            "bid_strategy": "LOWEST_COST_WITHOUT_CAP",
            "daily_budget": 50000,
            "lifetime_budget": None,
            "budget_remaining": None,
            "buying_type": "AUCTION",
            "start_time": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "stop_time": None,
            "ad_sets_count": 2,
            "ads_count": 5,
        }
        defaults.update(overrides)
        mock_row = MagicMock()
        mock_row._mapping = defaults
        return mock_row

    def _make_metric_row(self, campaign_id, metric_name, total_value):
        mock_row = MagicMock()
        mock_row._mapping = {
            "campaign_id": campaign_id,
            "metric_name": metric_name,
            "total_value": total_value,
        }
        return mock_row

    def _make_rec_row(self, **overrides):
        defaults = {
            "recommendation_type": "CREATIVE_FATIGUE",
            "source": "account",
            "title": "Creative fatigue",
            "body": "Refresh your creatives",
            "importance": "HIGH",
            "lift_estimate": None,
            "opportunity_score": 0.8,
            "url": None,
            "object_ids": [],
        }
        defaults.update(overrides)
        mock_row = MagicMock()
        mock_row._mapping = defaults
        return mock_row

    def test_returns_campaigns_with_metrics(self):
        db = MagicMock()
        # 1st call: campaigns query
        db.execute.side_effect = [
            MagicMock(
                fetchall=MagicMock(
                    return_value=[
                        self._make_campaign_row(
                            external_id="camp_1",
                            name="Campaign A",
                        ),
                    ],
                ),
            ),
            # 2nd call: metrics aggregated by campaign
            MagicMock(
                fetchall=MagicMock(
                    return_value=[
                        self._make_metric_row("camp_1", "spend", 1000.0),
                        self._make_metric_row("camp_1", "conversions", 50.0),
                        self._make_metric_row("camp_1", "clicks", 2000.0),
                        self._make_metric_row("camp_1", "impressions", 100000.0),
                    ],
                ),
            ),
            # 3rd call: recommendations
            MagicMock(fetchall=MagicMock(return_value=[])),
            # 4th call: currency
            MagicMock(
                fetchone=MagicMock(
                    return_value=MagicMock(
                        _mapping={"currency": "MXN"},
                    ),
                ),
            ),
            # 5th call: last_synced
            MagicMock(
                fetchone=MagicMock(
                    return_value=MagicMock(
                        _mapping={
                            "last_synced": datetime(2026, 4, 6, tzinfo=timezone.utc),
                        },
                    ),
                ),
            ),
        ]

        service = CampaignService(db)
        result = service.get_performance(TENANT_ID, "30d")

        assert result.total_campaigns == 1
        assert result.active_campaigns == 1
        assert result.campaigns[0].name == "Campaign A"
        assert result.campaigns[0].metrics.spend == 1000.0
        assert result.campaigns[0].metrics.conversions == 50.0
        assert result.campaigns[0].metrics.cpa == 20.0  # 1000/50
        assert result.currency == "MXN"

    def test_health_critical_when_cpa_3x_average(self):
        # 3 campaigns: two cheap (CPA=10 each), one expensive (CPA=400)
        # avg CPA = (10+10+400)/3 = 140. Bad ratio = 400/140 = 2.86 -> warning
        # To get critical (>3x): CPA must be >3*avg.
        # Use: 4 good (CPA=10) + 1 bad (CPA=500). avg=(10*4+500)/5=108. ratio=500/108=4.63 -> critical
        db = MagicMock()
        db.execute.side_effect = [
            # campaigns
            MagicMock(
                fetchall=MagicMock(
                    return_value=[
                        self._make_campaign_row(external_id="camp_g1", name="Good1"),
                        self._make_campaign_row(external_id="camp_g2", name="Good2"),
                        self._make_campaign_row(external_id="camp_g3", name="Good3"),
                        self._make_campaign_row(external_id="camp_g4", name="Good4"),
                        self._make_campaign_row(external_id="camp_bad", name="Bad"),
                    ],
                ),
            ),
            # metrics
            MagicMock(
                fetchall=MagicMock(
                    return_value=[
                        self._make_metric_row("camp_g1", "spend", 100.0),
                        self._make_metric_row("camp_g1", "conversions", 10.0),
                        self._make_metric_row("camp_g2", "spend", 100.0),
                        self._make_metric_row("camp_g2", "conversions", 10.0),
                        self._make_metric_row("camp_g3", "spend", 100.0),
                        self._make_metric_row("camp_g3", "conversions", 10.0),
                        self._make_metric_row("camp_g4", "spend", 100.0),
                        self._make_metric_row("camp_g4", "conversions", 10.0),
                        self._make_metric_row("camp_bad", "spend", 500.0),
                        self._make_metric_row("camp_bad", "conversions", 1.0),
                    ],
                ),
            ),
            # recommendations
            MagicMock(fetchall=MagicMock(return_value=[])),
            # currency
            MagicMock(
                fetchone=MagicMock(
                    return_value=MagicMock(
                        _mapping={"currency": "USD"},
                    ),
                ),
            ),
            # last_synced
            MagicMock(
                fetchone=MagicMock(
                    return_value=MagicMock(
                        _mapping={"last_synced": None},
                    ),
                ),
            ),
        ]

        service = CampaignService(db)
        result = service.get_performance(TENANT_ID, "30d")

        good1 = next(c for c in result.campaigns if c.name == "Good1")
        bad = next(c for c in result.campaigns if c.name == "Bad")
        assert good1.health == "good"
        assert bad.health == "critical"  # CPA 500 vs avg 108 -> 4.63x -> critical

    def test_empty_campaigns_returns_empty(self):
        db = MagicMock()
        db.execute.side_effect = [
            MagicMock(fetchall=MagicMock(return_value=[])),
            MagicMock(fetchall=MagicMock(return_value=[])),
            MagicMock(fetchall=MagicMock(return_value=[])),
            MagicMock(
                fetchone=MagicMock(
                    return_value=MagicMock(
                        _mapping={"currency": None},
                    ),
                ),
            ),
            MagicMock(
                fetchone=MagicMock(
                    return_value=MagicMock(
                        _mapping={"last_synced": None},
                    ),
                ),
            ),
        ]

        service = CampaignService(db)
        result = service.get_performance(TENANT_ID, "30d")

        assert result.total_campaigns == 0
        assert result.campaigns == []
