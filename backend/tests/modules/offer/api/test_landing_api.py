"""Integration tests for the ``/offer/products/{id}/landing/*`` endpoints."""

import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from luana_core_platform.core.database import get_db
from luana_core_iam.api.dependencies import get_current_user
from luana_core_iam.domain.user import User
from luana_core_offer_studio.api.landing import router
from tests.modules.offer.conftest import create_product_model


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


class TestLandingStatus:
    def test_status_returns_idle_for_offer_without_landing(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ) -> None:
        model = create_product_model(tenant_a, name="NoLanding")
        db.add(model)
        db.flush()
        client = _build_client(db, tenant_a)

        response = client.get(f"/api/v1/offer/products/{model.id}/landing/status")

        assert response.status_code == 200
        body = response.json()
        assert body["is_published"] is False
        assert body["job_status"] == "idle"
        assert body["is_outdated"] is False


class TestLandingGenerate:
    def test_generate_returns_422_when_offer_incomplete(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ) -> None:
        # Fresh product_model fixture has minimal fields filled — well below
        # the 90% completion threshold — so generate must reject it.
        model = create_product_model(
            tenant_a,
            name="Incomplete",
            headline_promise="",
            marketing_pain_points=[],
            marketing_desires=[],
            pricing=[],
        )
        db.add(model)
        db.flush()
        client = _build_client(db, tenant_a)

        response = client.post(f"/api/v1/offer/products/{model.id}/landing/generate")

        assert response.status_code == 422
        detail = response.json()["detail"]
        assert detail["error"] == "landing_not_ready"
        assert detail["required"] == 90.0


class TestLandingPublishUnpublish:
    def test_publish_without_landing_returns_422(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ) -> None:
        model = create_product_model(tenant_a, name="NoLandingPublish")
        db.add(model)
        db.flush()
        client = _build_client(db, tenant_a)

        response = client.post(f"/api/v1/offer/products/{model.id}/landing/publish")

        # Stub repo always returns None → service raises LandingNotReadyError.
        assert response.status_code == 422
