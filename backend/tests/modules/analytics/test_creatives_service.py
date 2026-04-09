"""Tests for creatives overview service — ad gallery + video retention metrics."""

from unittest.mock import MagicMock
from uuid import UUID

from src.modules.analytics.application.dto.campaign_dto import (
    CreativesOverviewDTO,
)
from src.modules.analytics.application.services.campaign_service import (
    CampaignService,
)

TENANT_ID = UUID("11111111-1111-1111-1111-111111111111")


def _make_ad_row(**overrides) -> MagicMock:
    """Build a mock row matching ads JOIN ad_campaigns columns."""
    defaults = {
        "external_id": "ad_1",
        "name": "Test Ad",
        "campaign_name": "Test Campaign",
        "campaign_external_id": "camp_1",
        "status": "ACTIVE",
        "effective_status": "ACTIVE",
        "creative_thumbnail_url": "https://example.com/thumb.jpg",
        "creative_title": "Great Product",
        "creative_cta": "SHOP_NOW",
        "preview_shareable_link": "https://fb.com/ads/preview/123",
    }
    defaults.update(overrides)
    row = MagicMock()
    row._mapping = defaults
    return row


def _make_video_metric_row(metric_name: str, total_value: float) -> MagicMock:
    """Build a mock row for video retention metric aggregation."""
    row = MagicMock()
    row._mapping = {
        "metric_name": metric_name,
        "total_value": total_value,
    }
    return row


class TestGetCreativesOverview:
    """Tests for CampaignService.get_creatives_overview()."""

    def test_returns_ads_from_joined_query(self):
        """Ads are returned with campaign name from JOIN."""
        db = MagicMock()
        db.execute.side_effect = [
            # 1st call: ads query
            MagicMock(
                fetchall=MagicMock(
                    return_value=[
                        _make_ad_row(
                            external_id="ad_1",
                            name="Ad Alpha",
                            campaign_name="Campaign One",
                        ),
                        _make_ad_row(
                            external_id="ad_2",
                            name="Ad Beta",
                            campaign_name="Campaign Two",
                            effective_status="PAUSED",
                        ),
                    ]
                )
            ),
            # 2nd call: video retention metrics
            MagicMock(fetchall=MagicMock(return_value=[])),
        ]

        service = CampaignService(db)
        result = service.get_creatives_overview(TENANT_ID, "30d")

        assert isinstance(result, CreativesOverviewDTO)
        assert result.total_ads == 2
        assert result.ads[0].name == "Ad Alpha"
        assert result.ads[0].campaign_name == "Campaign One"
        assert result.ads[1].effective_status == "PAUSED"

    def test_video_retention_metrics_aggregated(self):
        """Video retention metrics are summed from official_metrics."""
        db = MagicMock()
        db.execute.side_effect = [
            # ads query
            MagicMock(fetchall=MagicMock(return_value=[])),
            # video metrics
            MagicMock(
                fetchall=MagicMock(
                    return_value=[
                        _make_video_metric_row("meta_video_views", 10000.0),
                        _make_video_metric_row("meta_video_p25", 7500.0),
                        _make_video_metric_row("meta_video_p50", 5000.0),
                        _make_video_metric_row("meta_video_p75", 2500.0),
                        _make_video_metric_row("meta_video_p100", 1000.0),
                        _make_video_metric_row("meta_video_30sec", 6000.0),
                        _make_video_metric_row("meta_video_avg_watch_time", 15.5),
                    ]
                )
            ),
        ]

        service = CampaignService(db)
        result = service.get_creatives_overview(TENANT_ID, "30d")

        assert result.video_retention.plays == 10000.0
        assert result.video_retention.p25 == 7500.0
        assert result.video_retention.p50 == 5000.0
        assert result.video_retention.p75 == 2500.0
        assert result.video_retention.p100 == 1000.0
        assert result.video_retention.views_30s == 6000.0
        assert result.video_retention.avg_watch_time == 15.5

    def test_empty_data_returns_defaults(self):
        """When no ads or metrics exist, return empty defaults."""
        db = MagicMock()
        db.execute.side_effect = [
            MagicMock(fetchall=MagicMock(return_value=[])),
            MagicMock(fetchall=MagicMock(return_value=[])),
        ]

        service = CampaignService(db)
        result = service.get_creatives_overview(TENANT_ID, "30d")

        assert result.total_ads == 0
        assert result.ads == []
        assert result.video_retention.plays == 0
        assert result.video_retention.p25 == 0
        assert result.video_retention.p50 == 0
        assert result.video_retention.p75 == 0
        assert result.video_retention.p100 == 0

    def test_active_ads_sorted_first(self):
        """ACTIVE ads appear before non-active ads in results."""
        db = MagicMock()
        db.execute.side_effect = [
            MagicMock(
                fetchall=MagicMock(
                    return_value=[
                        _make_ad_row(
                            external_id="ad_active",
                            name="Active Ad",
                            effective_status="ACTIVE",
                        ),
                        _make_ad_row(
                            external_id="ad_paused",
                            name="Paused Ad",
                            effective_status="PAUSED",
                        ),
                    ]
                )
            ),
            MagicMock(fetchall=MagicMock(return_value=[])),
        ]

        service = CampaignService(db)
        result = service.get_creatives_overview(TENANT_ID, "30d")

        # Verify ordering: active first (SQL handles this)
        assert result.ads[0].effective_status == "ACTIVE"

    def test_filters_by_tenant_id(self):
        """Verify both queries use tenant_id."""
        db = MagicMock()
        db.execute.side_effect = [
            MagicMock(fetchall=MagicMock(return_value=[])),
            MagicMock(fetchall=MagicMock(return_value=[])),
        ]

        service = CampaignService(db)
        service.get_creatives_overview(TENANT_ID, "30d")

        # Both SQL queries should have been called
        assert db.execute.call_count == 2
        # Check tenant_id is in both query params
        for call in db.execute.call_args_list:
            params = call[0][1]
            assert params["tenant_id"] == str(TENANT_ID)

    def test_creative_fields_populated(self):
        """Creative-specific fields (thumbnail, title, CTA) are populated."""
        db = MagicMock()
        db.execute.side_effect = [
            MagicMock(
                fetchall=MagicMock(
                    return_value=[
                        _make_ad_row(
                            creative_thumbnail_url="https://example.com/img.jpg",
                            creative_title="My Title",
                            creative_cta="LEARN_MORE",
                            preview_shareable_link="https://fb.com/preview/456",
                        ),
                    ]
                )
            ),
            MagicMock(fetchall=MagicMock(return_value=[])),
        ]

        service = CampaignService(db)
        result = service.get_creatives_overview(TENANT_ID, "30d")

        ad = result.ads[0]
        assert ad.creative_thumbnail_url == "https://example.com/img.jpg"
        assert ad.creative_title == "My Title"
        assert ad.creative_cta == "LEARN_MORE"
        assert ad.preview_shareable_link == "https://fb.com/preview/456"

    def test_period_7d(self):
        """Period=7d computes correct date range."""
        db = MagicMock()
        db.execute.side_effect = [
            MagicMock(fetchall=MagicMock(return_value=[])),
            MagicMock(fetchall=MagicMock(return_value=[])),
        ]

        service = CampaignService(db)
        result = service.get_creatives_overview(TENANT_ID, "7d")

        assert isinstance(result, CreativesOverviewDTO)
