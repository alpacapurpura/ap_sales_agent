"""Tests for analytics API routes — campaigns and email_metrics endpoints."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


def _make_user():
    from src.modules.iam.domain.user import User

    user = MagicMock(spec=User)
    user.tenant_id = TENANT_ID
    return user


def _make_campaigns_app():
    from src.core.database import get_db
    from src.modules.analytics.api.campaigns import router
    from src.modules.iam.api.dependencies import get_current_user

    db = MagicMock()
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = _make_user
    return app, db


def _make_email_app():
    from src.core.database import get_db
    from src.modules.analytics.api.email_metrics import router
    from src.modules.iam.api.dependencies import get_current_user

    db = MagicMock()
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = _make_user
    return app, db


# ─── Campaigns API ────────────────────────────────────────────────────────────


class TestCampaignsOverviewRoute:
    def test_get_overview_200(self):
        app, _ = _make_campaigns_app()
        client = TestClient(app, raise_server_exceptions=False)

        with patch("src.modules.analytics.api.campaigns.CampaignService") as MockSvc:
            from src.modules.analytics.application.dto.campaign_dto import CampaignOverviewDTO

            instance = MagicMock()
            instance.get_overview.return_value = CampaignOverviewDTO(
                campaigns=[],
                recommendations=[],
                total_campaigns=0,
                active_campaigns=0,
                last_synced=None,
            )
            MockSvc.return_value = instance
            resp = client.get("/campaigns")

        assert resp.status_code == 200


class TestCampaignsPerformanceRoute:
    def test_invalid_period_returns_400(self):
        app, _ = _make_campaigns_app()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/campaigns/performance?period=1d")
        assert resp.status_code == 400

    def test_valid_period_returns_200(self):
        app, _ = _make_campaigns_app()
        client = TestClient(app, raise_server_exceptions=False)

        with patch("src.modules.analytics.api.campaigns.CampaignService") as MockSvc:
            from src.modules.analytics.application.dto.campaign_dto import CampaignPerformanceDTO

            instance = MagicMock()
            instance.get_performance.return_value = CampaignPerformanceDTO(
                period="30d",
                campaigns=[],
                recommendations=[],
                total_campaigns=0,
                active_campaigns=0,
            )
            MockSvc.return_value = instance
            resp = client.get("/campaigns/performance?period=30d")

        assert resp.status_code == 200


class TestCampaignsCreativesRoute:
    def test_invalid_period_returns_400(self):
        app, _ = _make_campaigns_app()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/campaigns/creatives?period=bad")
        assert resp.status_code == 400

    def test_valid_period_returns_200(self):
        app, _ = _make_campaigns_app()
        client = TestClient(app, raise_server_exceptions=False)

        with patch("src.modules.analytics.api.campaigns.CampaignService") as MockSvc:
            from src.modules.analytics.application.dto.campaign_dto import CreativesOverviewDTO

            instance = MagicMock()
            instance.get_creatives_overview.return_value = CreativesOverviewDTO(
                period="30d",
                ads=[],
            )
            MockSvc.return_value = instance
            resp = client.get("/campaigns/creatives?period=30d")

        assert resp.status_code == 200


class TestAdsPerformanceRoute:
    def test_invalid_period_returns_400(self):
        app, _ = _make_campaigns_app()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/campaigns/ads/performance?period=99d")
        assert resp.status_code == 400

    def test_valid_returns_200(self):
        app, _ = _make_campaigns_app()
        client = TestClient(app, raise_server_exceptions=False)

        with patch("src.modules.analytics.api.campaigns.AdPerformanceService") as MockSvc:
            from src.modules.analytics.application.dto.campaign_dto import AdPerformanceListDTO

            instance = MagicMock()
            instance.get_top_ads.return_value = AdPerformanceListDTO(period="30d", ads=[])
            MockSvc.return_value = instance
            resp = client.get("/campaigns/ads/performance?period=7d")

        assert resp.status_code == 200


class TestAdsFormatComparisonRoute:
    def test_invalid_period_returns_400(self):
        app, _ = _make_campaigns_app()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/campaigns/ads/format-comparison?period=200d")
        assert resp.status_code == 400

    def test_valid_returns_200(self):
        app, _ = _make_campaigns_app()
        client = TestClient(app, raise_server_exceptions=False)

        with patch("src.modules.analytics.api.campaigns.AdPerformanceService") as MockSvc:
            from src.modules.analytics.application.dto.campaign_dto import FormatComparisonDTO

            instance = MagicMock()
            instance.get_format_comparison.return_value = FormatComparisonDTO(
                period="30d",
                formats=[],
            )
            MockSvc.return_value = instance
            resp = client.get("/campaigns/ads/format-comparison?period=30d")

        assert resp.status_code == 200


class TestCampaignAdSetsRoute:
    def test_returns_ad_sets(self):
        app, _ = _make_campaigns_app()
        client = TestClient(app, raise_server_exceptions=False)

        with patch("src.modules.analytics.api.campaigns.CampaignService") as MockSvc:
            instance = MagicMock()
            instance.get_ad_sets.return_value = []
            MockSvc.return_value = instance
            resp = client.get("/campaigns/camp-ext-1/adsets")

        assert resp.status_code == 200


class TestAdSetAdsRoute:
    def test_returns_ads(self):
        app, _ = _make_campaigns_app()
        client = TestClient(app, raise_server_exceptions=False)

        with patch("src.modules.analytics.api.campaigns.CampaignService") as MockSvc:
            instance = MagicMock()
            instance.get_ads.return_value = []
            MockSvc.return_value = instance
            resp = client.get("/campaigns/adsets/adset-1/ads")

        assert resp.status_code == 200


class TestCampaignSyncStatusRoute:
    def test_no_redis_returns_unknown(self):
        app, _ = _make_campaigns_app()
        client = TestClient(app, raise_server_exceptions=False)

        with patch("src.core.database.redis_client", None):
            resp = client.get("/campaigns/sync/status")

        assert resp.status_code == 200
        assert resp.json()["status"] == "unknown"

    def test_never_synced_when_no_key(self):
        app, _ = _make_campaigns_app()
        client = TestClient(app, raise_server_exceptions=False)

        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        with patch("src.core.database.redis_client", mock_redis):
            resp = client.get("/campaigns/sync/status")

        assert resp.status_code == 200
        assert resp.json()["status"] == "never_synced"

    def test_returns_sync_data_when_key_exists(self):
        import json

        app, _ = _make_campaigns_app()
        client = TestClient(app, raise_server_exceptions=False)

        mock_redis = MagicMock()
        mock_redis.get.return_value = json.dumps(
            {
                "status": "success",
                "campaigns_synced": 5,
                "ad_sets_synced": 10,
                "ads_synced": 30,
                "recommendations_synced": 2,
            }
        )

        with patch("src.core.database.redis_client", mock_redis):
            resp = client.get("/campaigns/sync/status")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["campaigns_synced"] == 5


class TestTriggerCampaignSyncRoute:
    def test_trigger_sync_returns_response(self):
        app, _ = _make_campaigns_app()
        client = TestClient(app, raise_server_exceptions=False)

        with patch("src.modules.analytics.api.campaigns.CampaignService") as MockSvc:
            from src.modules.analytics.api.campaigns import CampaignSyncResponse

            instance = MagicMock()
            instance.trigger_sync = AsyncMock(return_value=CampaignSyncResponse(status="queued"))
            MockSvc.return_value = instance
            resp = client.post("/campaigns/sync")

        assert resp.status_code == 200


# ─── Email Metrics API ─────────────────────────────────────────────────────────


class TestEmailDashboardRoute:
    def test_get_dashboard_200(self):
        app, _ = _make_email_app()
        client = TestClient(app, raise_server_exceptions=False)

        with patch("src.modules.analytics.api.email_metrics.EmailDashboardService") as MockSvc:
            from src.modules.analytics.application.dto.email_dashboard_dto import EmailDashboardDTO

            instance = MagicMock()
            instance.get_dashboard = AsyncMock(return_value=MagicMock(spec=EmailDashboardDTO))
            MockSvc.return_value = instance
            resp = client.get("/email/dashboard")

        assert resp.status_code == 200


class TestEmailCampaignsRoute:
    def test_get_campaigns_200(self):
        app, _ = _make_email_app()
        client = TestClient(app, raise_server_exceptions=False)

        with patch("src.modules.analytics.api.email_metrics.EmailDashboardService") as MockSvc:
            from src.modules.analytics.application.dto.email_dashboard_dto import EmailCampaignsResponseDTO

            instance = MagicMock()
            instance.get_campaigns = AsyncMock(return_value=MagicMock(spec=EmailCampaignsResponseDTO))
            MockSvc.return_value = instance
            resp = client.get("/email/campaigns")

        assert resp.status_code == 200


class TestEmailHealthRoute:
    def test_get_health_200(self):
        app, _ = _make_email_app()
        client = TestClient(app, raise_server_exceptions=False)

        with patch("src.modules.analytics.api.email_metrics.EmailDashboardService") as MockSvc:
            from src.modules.analytics.application.dto.email_dashboard_dto import EmailHealthResponseDTO

            instance = MagicMock()
            instance.get_health = AsyncMock(return_value=MagicMock(spec=EmailHealthResponseDTO))
            MockSvc.return_value = instance
            resp = client.get("/email/health")

        assert resp.status_code == 200


class TestEmailGrowthRoute:
    def test_get_growth_200(self):
        app, _ = _make_email_app()
        client = TestClient(app, raise_server_exceptions=False)

        with patch("src.modules.analytics.api.email_metrics.EmailDashboardService") as MockSvc:
            from src.modules.analytics.application.dto.email_dashboard_dto import EmailGrowthResponseDTO

            instance = MagicMock()
            instance.get_growth = AsyncMock(return_value=MagicMock(spec=EmailGrowthResponseDTO))
            MockSvc.return_value = instance
            resp = client.get("/email/growth")

        assert resp.status_code == 200


class TestEmailAudienceRoute:
    def test_get_audience_200(self):
        app, _ = _make_email_app()
        client = TestClient(app, raise_server_exceptions=False)

        with patch("src.modules.analytics.api.email_metrics.EmailDashboardService") as MockSvc:
            from src.modules.analytics.application.dto.email_dashboard_dto import EmailAudienceResponseDTO

            instance = MagicMock()
            instance.get_audience = AsyncMock(return_value=MagicMock(spec=EmailAudienceResponseDTO))
            MockSvc.return_value = instance
            resp = client.get("/email/audience")

        assert resp.status_code == 200


class TestEmailAutomationsRoute:
    def test_get_automations_200(self):
        app, _ = _make_email_app()
        client = TestClient(app, raise_server_exceptions=False)

        with patch("src.modules.analytics.api.email_metrics.EmailDashboardService") as MockSvc:
            from src.modules.analytics.application.dto.email_dashboard_dto import EmailAutomationsResponseDTO

            instance = MagicMock()
            instance.get_automations = AsyncMock(return_value=MagicMock(spec=EmailAutomationsResponseDTO))
            MockSvc.return_value = instance
            resp = client.get("/email/automations")

        assert resp.status_code == 200
