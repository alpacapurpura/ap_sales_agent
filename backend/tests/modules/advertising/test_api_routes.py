"""Tests for the advertising FastAPI router."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.database import get_db
from src.modules.advertising.api.routes import router
from src.modules.advertising.application.dto.association_dto import (
    AssociationSuggestionDTO,
)
from src.modules.advertising.application.dto.health_check_dto import (
    MetaHealthCheckDTO,
)
from src.modules.advertising.application.dto.metrics_by_offer_dto import (
    BrandingAggregateDTO,
    MetricsByOfferDTO,
    UnassignedAggregateDTO,
)
from src.modules.iam.api.dependencies import (
    get_current_user,
    get_tenant_context,
    get_tenant_locale,
)
from src.shared.domain.locale import TenantLocale


def _build_client(db, tenant_id: UUID):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_tenant_context] = lambda: tenant_id
    app.dependency_overrides[get_tenant_locale] = TenantLocale.default
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant_id,
        email="t@t.co",
        full_name="Tester",
        role="admin",
    )
    return TestClient(app)


class TestAssociationsEndpoint:
    def test_create_manual_association(self, db, tenant_id, offer_id, make_offer):
        make_offer(db, tenant_id=tenant_id, name="Curso", offer_id=offer_id)
        client = _build_client(db, tenant_id)
        resp = client.post(
            "/api/v1/advertising/associations",
            json={
                "targetType": "campaign",
                "targetExternalId": "c1",
                "offerId": str(offer_id),
                "associationType": "manual",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["targetType"] == "campaign"
        assert data["targetExternalId"] == "c1"
        assert data["offerId"] == str(offer_id)
        assert data["associationType"] == "manual"
        assert data["offerName"] == "Curso"

    def test_excluded_branding_rejects_offer_id(self, db, tenant_id, offer_id):
        client = _build_client(db, tenant_id)
        resp = client.post(
            "/api/v1/advertising/associations",
            json={
                "targetType": "campaign",
                "targetExternalId": "c1",
                "offerId": str(offer_id),
                "associationType": "excluded_branding",
            },
        )
        assert resp.status_code == 422

    def test_manual_requires_offer_id(self, db, tenant_id):
        client = _build_client(db, tenant_id)
        resp = client.post(
            "/api/v1/advertising/associations",
            json={
                "targetType": "campaign",
                "targetExternalId": "c1",
                "associationType": "manual",
            },
        )
        assert resp.status_code == 422

    def test_list_associations_returns_active_rows(
        self, db, tenant_id, offer_id, make_offer
    ):
        make_offer(db, tenant_id=tenant_id, name="Curso", offer_id=offer_id)
        client = _build_client(db, tenant_id)
        client.post(
            "/api/v1/advertising/associations",
            json={
                "targetType": "campaign",
                "targetExternalId": "c1",
                "offerId": str(offer_id),
                "associationType": "manual",
            },
        )
        resp = client.get("/api/v1/advertising/associations")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) == 1
        assert items[0]["targetExternalId"] == "c1"

    def test_delete_association_soft_deletes(self, db, tenant_id, offer_id, make_offer):
        make_offer(db, tenant_id=tenant_id, name="Curso", offer_id=offer_id)
        client = _build_client(db, tenant_id)
        created = client.post(
            "/api/v1/advertising/associations",
            json={
                "targetType": "campaign",
                "targetExternalId": "c1",
                "offerId": str(offer_id),
                "associationType": "manual",
            },
        ).json()
        resp = client.delete(f"/api/v1/advertising/associations/{created['id']}")
        assert resp.status_code == 204
        # Now list should be empty
        listed = client.get("/api/v1/advertising/associations").json()
        assert listed == []


class TestAutoDetectEndpoint:
    def test_auto_detect_delegates_to_service(self, db, tenant_id):
        client = _build_client(db, tenant_id)
        suggestion = AssociationSuggestionDTO(
            target_type="campaign",
            target_external_id="c1",
            target_name="Campaña sugerida",
            suggested_offer_id=uuid4(),
            suggested_offer_name="Offer X",
            association_type="auto_keyword",
            confidence="medium",
            reason="match 60%",
        )
        with patch(
            "src.modules.advertising.api.routes.OfferDetectionService"
        ) as svc_cls:
            instance = MagicMock()
            instance.detect = AsyncMock(return_value=[suggestion])
            svc_cls.return_value = instance
            resp = client.post("/api/v1/advertising/associations/auto-detect")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["targetExternalId"] == "c1"
        assert data[0]["confidence"] == "medium"


class TestHealthCheckEndpoint:
    def test_delegates_to_service(self, db, tenant_id):
        client = _build_client(db, tenant_id)
        dto = MetaHealthCheckDTO(
            overall_status="healthy",
            active_campaigns=[],
            offers_coverage=[],
            unassigned_targets=[],
            recommendations=[],
            summary_text="Todo correcto",
        )
        with patch("src.modules.advertising.api.routes.HealthCheckService") as svc_cls:
            instance = MagicMock()
            instance.run = AsyncMock(return_value=dto)
            svc_cls.return_value = instance
            resp = client.get("/api/v1/advertising/health-check")
        assert resp.status_code == 200
        assert resp.json()["overallStatus"] == "healthy"
        assert resp.json()["summaryText"] == "Todo correcto"

    def test_rejects_unsupported_provider(self, db, tenant_id):
        client = _build_client(db, tenant_id)
        resp = client.get(
            "/api/v1/advertising/health-check", params={"provider": "tiktok"}
        )
        assert resp.status_code == 400


class TestMetricsByOfferEndpoint:
    def test_delegates_and_validates_period(self, db, tenant_id):
        client = _build_client(db, tenant_id)
        dto = MetricsByOfferDTO(
            period="30d",
            start_date="2026-03-11",
            end_date="2026-04-09",
            currency="USD",
            offers=[],
            unassigned=UnassignedAggregateDTO(
                target_count=0,
                total_spend=0.0,
                impressions=0.0,
                clicks=0.0,
                ctr=0.0,
                cpm=0.0,
                cpc=0.0,
                reach=None,
                funnel=[],
            ),
            branding_only=BrandingAggregateDTO(
                target_count=0,
                total_spend=0.0,
                impressions=0.0,
                clicks=0.0,
                ctr=0.0,
                cpm=0.0,
                cpc=0.0,
                reach=None,
                frequency=None,
                funnel=[],
            ),
            funnel_all=[],
            reach_all=None,
        )
        with patch(
            "src.modules.advertising.api.routes.MetricsByOfferService"
        ) as svc_cls:
            instance = MagicMock()
            instance.run = AsyncMock(return_value=dto)
            svc_cls.return_value = instance
            resp = client.get("/api/v1/advertising/metrics-by-offer")
        assert resp.status_code == 200
        assert resp.json()["period"] == "30d"

    def test_invalid_period_returns_400(self, db, tenant_id):
        client = _build_client(db, tenant_id)
        resp = client.get(
            "/api/v1/advertising/metrics-by-offer", params={"period": "1y"}
        )
        assert resp.status_code == 400


class TestCampaignTemplateEndpoint:
    def test_returns_404_when_no_template(self, db, tenant_id):
        client = _build_client(db, tenant_id)
        with patch(
            "src.modules.advertising.api.routes.CampaignTemplateService"
        ) as svc_cls:
            instance = MagicMock()
            instance.get_template_for_offer = AsyncMock(return_value=None)
            svc_cls.return_value = instance
            resp = client.get(
                "/api/v1/advertising/campaign-templates/suggest",
                params={"offer_id": str(uuid4())},
            )
        assert resp.status_code == 404


class TestOffersForAssignmentEndpoint:
    def test_returns_active_non_lead_magnet_offers(self, db, tenant_id, make_offer):
        """Endpoint lists non-archived offers. Archived and lead magnets are excluded.

        Drafts ARE returned — in practice every offer sits in ``status='draft'``
        until a future UI promotes it, so filtering drafts here would leave the
        assignment dropdown empty.
        """
        from datetime import UTC, datetime

        make_offer(
            db,
            tenant_id=tenant_id,
            name="Curso Digital",
            archetype="PROGRAMA",
            checkout_page_url="https://buy/curso",
        )
        make_offer(
            db,
            tenant_id=tenant_id,
            name="Asesoría 1:1",
            archetype="SERVICIO",
            onboarding_action="BOOK_KICKOFF_CALL",
        )
        # Draft offers MUST appear — users create offers as drafts and expect
        # to be able to associate campaigns to them before "publishing".
        make_offer(
            db,
            tenant_id=tenant_id,
            name="Diseña tu 2026",
            archetype="PRODUCTO",
            status="draft",
        )
        # Lead magnet — MUST be hidden from the assignment dropdown
        make_offer(
            db,
            tenant_id=tenant_id,
            name="Guía Lead Magnet",
            archetype="PRODUCTO",
            is_lead_magnet=True,
        )
        # Archived offers should NOT appear — archival lives on ``archived_at``
        # after migration 040, not on ``status``.
        archived = make_offer(
            db,
            tenant_id=tenant_id,
            name="Vieja Archivada",
            archetype="PRODUCTO",
        )
        archived.archived_at = datetime.now(UTC)
        db.flush()

        client = _build_client(db, tenant_id)
        resp = client.get("/api/v1/advertising/offers")
        assert resp.status_code == 200
        data = resp.json()
        names = {o["name"] for o in data}
        # Archived AND lead magnet excluded; drafts included → 3 offers
        assert names == {"Curso Digital", "Asesoría 1:1", "Diseña tu 2026"}
        # Each offer has an expected metric derived from its properties
        by_name = {o["name"]: o for o in data}
        assert by_name["Asesoría 1:1"]["expectedMetric"] == "call_booked"
        assert by_name["Curso Digital"]["expectedMetric"] == "purchase"

    def test_lead_magnets_explicitly_hidden(self, db, tenant_id, make_offer):
        """Even when the only offers are lead magnets, the endpoint returns nothing."""
        make_offer(
            db,
            tenant_id=tenant_id,
            name="LM A",
            archetype="PRODUCTO",
            is_lead_magnet=True,
        )
        make_offer(
            db,
            tenant_id=tenant_id,
            name="LM B",
            archetype="PRODUCTO",
            is_lead_magnet=True,
        )
        client = _build_client(db, tenant_id)
        resp = client.get("/api/v1/advertising/offers")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_empty_when_tenant_has_no_offers(self, db, tenant_id):
        client = _build_client(db, tenant_id)
        resp = client.get("/api/v1/advertising/offers")
        assert resp.status_code == 200
        assert resp.json() == []
