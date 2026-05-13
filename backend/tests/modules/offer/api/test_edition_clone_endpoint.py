"""HTTP integration tests for ``POST /clone`` and ``GET /landing``."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from luana_core_platform.core.database import get_db
from luana_core_iam.api.dependencies import get_current_user
from luana_core_iam.domain.user import User
from luana_core_landing.infrastructure.models.landing_model import LandingPageModel
from luana_core_offer_studio.api.launch_editions import router
from luana_core_offer_studio.application.launch_edition_service import LaunchEditionService
from luana_core_offer_studio.application.offer_service import OfferService
from luana_core_offer_studio.domain.enums import OfferArchetype


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


def _seed_offer_edition_landing(
    db,
    tenant_id: uuid.UUID,
    *,
    archetype: OfferArchetype = OfferArchetype.EXPERIENCIA,
):
    offer = OfferService(db).create_offer(
        name="Masterclass",
        tenant_id=tenant_id,
        archetype=archetype,
    )
    svc = LaunchEditionService(db)
    placeholder = svc.list_editions(offer.id, tenant_id)[0]
    source = svc.update_edition(
        placeholder.id,
        tenant_id,
        {
            "start_date": datetime(2026, 6, 1, 18, 0, tzinfo=timezone.utc),
            "location_override": {"city": "Lima"},
        },
    )
    landing = LandingPageModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        offer_id=offer.id,
        edition_id=source.id,
        slug="masterclass-src",
        config={
            "archetype": "THE_EVENT",
            "slug": "masterclass-src",
            "content": {
                "headline": "Únete el {{start_date}}",
                "subheadline": "En {{location}}",
            },
            "is_published": False,
        },
        is_published=False,
    )
    db.add(landing)
    db.flush()
    return offer, source, landing


class TestCloneEndpoint:
    def test_happy_path_clones_edition_landing_and_returns_ids(self, db, tenant_a):
        offer, source, _landing = _seed_offer_edition_landing(db, tenant_a)
        client = _build_client(db, tenant_a)

        resp = client.post(
            f"/api/v1/offer/products/{offer.id}/editions/{source.id}/clone",
            json={
                "strategy": "date_replace",
                "new_edition_input": {
                    "start_date": "2026-11-10T18:00:00+00:00",
                    "location_override": {"city": "Arequipa"},
                },
            },
        )
        assert resp.status_code == 201, resp.text
        payload = resp.json()
        assert payload["edition"]["cloned_from_edition_id"] == str(source.id)
        assert payload["edition"]["visibility"] == "private"
        assert payload["edition"]["status"] == "draft"
        assert payload["landing_id"] is not None
        assert payload["landing_slug"] == "masterclass-src-ed2"

    def test_returns_404_for_missing_source(self, db, tenant_a):
        offer, _source, _landing = _seed_offer_edition_landing(db, tenant_a)
        client = _build_client(db, tenant_a)

        resp = client.post(
            f"/api/v1/offer/products/{offer.id}/editions/{uuid.uuid4()}/clone",
            json={
                "strategy": "literal",
                "new_edition_input": {
                    "start_date": "2026-12-01T00:00:00+00:00",
                },
            },
        )
        assert resp.status_code == 404


class TestEditionLandingEndpoint:
    def test_returns_landing_when_bound(self, db, tenant_a):
        offer, source, _landing = _seed_offer_edition_landing(db, tenant_a)
        client = _build_client(db, tenant_a)

        resp = client.get(
            f"/api/v1/offer/products/{offer.id}/editions/{source.id}/landing",
        )
        assert resp.status_code == 200
        assert resp.json()["slug"] == "masterclass-src"

    def test_returns_empty_shape_when_no_landing(self, db, tenant_a):
        offer = OfferService(db).create_offer(
            name="NoLandingOffer",
            tenant_id=tenant_a,
            archetype=OfferArchetype.EXPERIENCIA,
        )
        edition = LaunchEditionService(db).list_editions(offer.id, tenant_a)[0]
        client = _build_client(db, tenant_a)

        resp = client.get(
            f"/api/v1/offer/products/{offer.id}/editions/{edition.id}/landing",
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["landing_id"] is None
        assert body["slug"] is None

    def test_404_for_wrong_tenant(self, db, tenant_a, tenant_b):
        offer, source, _landing = _seed_offer_edition_landing(db, tenant_a)
        client = _build_client(db, tenant_b)

        resp = client.get(
            f"/api/v1/offer/products/{offer.id}/editions/{source.id}/landing",
        )
        assert resp.status_code == 404
