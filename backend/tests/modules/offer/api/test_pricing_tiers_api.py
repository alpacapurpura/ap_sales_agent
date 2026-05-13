"""HTTP integration tests for pricing tiers on the edition API (Phase 4)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from luana_core_platform.core.database import get_db
from luana_core_iam.api.dependencies import get_current_user
from luana_core_iam.domain.user import User
from luana_core_offer_studio.api.launch_editions import router
from luana_core_offer_studio.application.launch_edition_service import LaunchEditionService
from luana_core_offer_studio.application.offer_service import OfferService
from luana_core_offer_studio.domain.enums import OfferArchetype


def _build_client(db: Session, tenant_id: uuid.UUID) -> TestClient:
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


class TestPricingTiersAPI:
    def test_create_edition_persists_tiers_and_returns_active(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ) -> None:
        offer = OfferService(db).create_offer(
            name="Masterclass",
            tenant_id=tenant_a,
            archetype=OfferArchetype.EXPERIENCIA,
        )
        db.flush()
        client = _build_client(db, tenant_a)

        # Open-ended tier so the resolver picks it regardless of current time.
        resp = client.post(
            f"/api/v1/offer/products/{offer.id}/editions",
            json={
                "start_date": "2026-05-01T00:00:00+00:00",
                "pricing_tiers": [
                    {
                        "label": "regular",
                        "pricing": [{"label": "Base", "total_amount": 400}],
                        "sort_order": 0,
                    },
                ],
            },
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["pricing_tiers"][0]["label"] == "regular"
        assert body["active_tier"] is not None
        assert body["active_tier"]["label"] == "regular"
        assert body["effective_pricing"][0]["total_amount"] == 400

    def test_rejects_dual_pricing_input(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ) -> None:
        offer = OfferService(db).create_offer(
            name="Masterclass",
            tenant_id=tenant_a,
            archetype=OfferArchetype.EXPERIENCIA,
        )
        db.flush()
        client = _build_client(db, tenant_a)

        resp = client.post(
            f"/api/v1/offer/products/{offer.id}/editions",
            json={
                "start_date": "2026-05-01T00:00:00+00:00",
                "pricing_override": [{"label": "Legacy", "total_amount": 100}],
                "pricing_tiers": [
                    {
                        "label": "regular",
                        "pricing": [{"label": "Base", "total_amount": 400}],
                    },
                ],
            },
        )
        assert resp.status_code == 422
        assert "pricing" in resp.json()["detail"].lower()

    def test_patch_rejects_overlapping_tiers(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ) -> None:
        offer = OfferService(db).create_offer(
            name="Masterclass",
            tenant_id=tenant_a,
            archetype=OfferArchetype.EXPERIENCIA,
        )
        db.flush()
        edition = LaunchEditionService(db).list_editions(offer.id, tenant_a)[0]
        client = _build_client(db, tenant_a)

        resp = client.patch(
            f"/api/v1/offer/products/{offer.id}/editions/{edition.id}",
            json={
                "pricing_tiers": [
                    {
                        "label": "a",
                        "pricing": [{"label": "A", "total_amount": 100}],
                        "valid_from": "2026-05-01T00:00:00+00:00",
                        "valid_until": "2026-05-10T00:00:00+00:00",
                    },
                    {
                        "label": "b",
                        "pricing": [{"label": "B", "total_amount": 200}],
                        "valid_from": "2026-05-05T00:00:00+00:00",
                        "valid_until": "2026-05-15T00:00:00+00:00",
                    },
                ],
            },
        )
        assert resp.status_code == 422
        assert "overlap" in resp.json()["detail"].lower()
