"""HTTP integration tests for the Phase 2 endpoints: /public, /publish, /unpublish."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.offer.api.launch_editions import router
from src.modules.offer.application.launch_edition_service import LaunchEditionService
from src.modules.offer.application.offer_service import OfferService
from src.modules.offer.domain.enums import OfferArchetype


def _build_client(db, tenant_id: uuid.UUID) -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/offer/products")
    fake_user = User(
        id=uuid.uuid4(),
        email="owner@example.com",
        full_name="Owner",
        tenant_id=tenant_id,
        is_active=True,
    )
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: fake_user
    return TestClient(app)


class TestListPublicEndpoint:
    def test_returns_empty_list_when_only_placeholder_exists(self, db, tenant_a: uuid.UUID):
        offer = OfferService(db).create_offer(
            name="Bootcamp",
            tenant_id=tenant_a,
            archetype=OfferArchetype.PROGRAMA,
        )
        db.flush()
        client = _build_client(db, tenant_a)
        resp = client.get(f"/api/v1/offer/products/{offer.id}/editions/public")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_published_editions_ordered_by_start_date(self, db, tenant_a: uuid.UUID):
        offer = OfferService(db).create_offer(
            name="Bootcamp",
            tenant_id=tenant_a,
            archetype=OfferArchetype.PROGRAMA,
        )
        db.flush()
        svc = LaunchEditionService(db)
        # Publish placeholder on Aug.
        placeholder = svc.list_editions(offer.id, tenant_a)[0]
        svc.update_edition(
            placeholder.id,
            tenant_a,
            {
                "start_date": datetime(2026, 8, 15, tzinfo=timezone.utc),
                "end_date": datetime(2026, 10, 15, tzinfo=timezone.utc),
            },
        )
        svc.publish_edition(placeholder.id, tenant_a)

        # New edition on May (earlier).
        new = svc.create_edition(
            offer_id=offer.id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 5, 15, tzinfo=timezone.utc),
            end_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        svc.publish_edition(new.id, tenant_a)
        db.flush()

        client = _build_client(db, tenant_a)
        resp = client.get(f"/api/v1/offer/products/{offer.id}/editions/public")
        assert resp.status_code == 200
        payload = resp.json()
        assert len(payload) == 2
        # Soonest first (May, then Aug).
        assert payload[0]["start_date"].startswith("2026-05")
        assert payload[1]["start_date"].startswith("2026-08")


class TestPublishEndpoint:
    def test_publish_returns_422_when_constraints_missing(self, db, tenant_a: uuid.UUID):
        offer = OfferService(db).create_offer(
            name="Bootcamp",
            tenant_id=tenant_a,
            archetype=OfferArchetype.PROGRAMA,
        )
        db.flush()
        ed = LaunchEditionService(db).list_editions(offer.id, tenant_a)[0]

        client = _build_client(db, tenant_a)
        resp = client.post(f"/api/v1/offer/products/{offer.id}/editions/{ed.id}/publish")
        assert resp.status_code == 422
        assert "start_date" in resp.json()["detail"]

    def test_publish_returns_200_when_valid(self, db, tenant_a: uuid.UUID):
        offer = OfferService(db).create_offer(
            name="Bootcamp",
            tenant_id=tenant_a,
            archetype=OfferArchetype.PROGRAMA,
        )
        db.flush()
        svc = LaunchEditionService(db)
        ed = svc.list_editions(offer.id, tenant_a)[0]
        svc.update_edition(
            ed.id,
            tenant_a,
            {
                "start_date": datetime(2026, 5, 15, tzinfo=timezone.utc),
                "end_date": datetime(2026, 7, 15, tzinfo=timezone.utc),
            },
        )
        db.flush()

        client = _build_client(db, tenant_a)
        resp = client.post(f"/api/v1/offer/products/{offer.id}/editions/{ed.id}/publish")
        assert resp.status_code == 200
        assert resp.json()["visibility"] == "public"
        assert resp.json()["status"] == "upcoming"

    def test_publish_returns_404_when_edition_not_found(self, db, tenant_a: uuid.UUID):
        offer = OfferService(db).create_offer(
            name="Bootcamp",
            tenant_id=tenant_a,
            archetype=OfferArchetype.PROGRAMA,
        )
        db.flush()
        missing = uuid.uuid4()
        client = _build_client(db, tenant_a)
        resp = client.post(f"/api/v1/offer/products/{offer.id}/editions/{missing}/publish")
        assert resp.status_code == 404


class TestUnpublishEndpoint:
    def test_unpublish_keeps_status_changes_visibility(self, db, tenant_a: uuid.UUID):
        offer = OfferService(db).create_offer(
            name="Bootcamp",
            tenant_id=tenant_a,
            archetype=OfferArchetype.PROGRAMA,
        )
        db.flush()
        svc = LaunchEditionService(db)
        ed = svc.list_editions(offer.id, tenant_a)[0]
        svc.update_edition(
            ed.id,
            tenant_a,
            {
                "start_date": datetime(2026, 5, 15, tzinfo=timezone.utc),
                "end_date": datetime(2026, 7, 15, tzinfo=timezone.utc),
            },
        )
        svc.publish_edition(ed.id, tenant_a)
        db.flush()

        client = _build_client(db, tenant_a)
        resp = client.post(f"/api/v1/offer/products/{offer.id}/editions/{ed.id}/unpublish")
        assert resp.status_code == 200
        body = resp.json()
        assert body["visibility"] == "private"
        # Status preserved.
        assert body["status"] == "upcoming"
