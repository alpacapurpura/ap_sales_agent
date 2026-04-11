"""Integration tests for ``POST /offer/products/{id}/status``."""

import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.offer.api.lifecycle import router
from src.modules.offer.domain.enums import OfferStatus
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


class TestChangeStatus:
    def test_transition_active_to_paused_returns_200(
        self, db: Session, tenant_a: uuid.UUID
    ) -> None:
        model = create_product_model(
            tenant_a, name="Live", status=OfferStatus.ACTIVE.value
        )
        db.add(model)
        db.flush()
        client = _build_client(db, tenant_a)

        response = client.post(
            f"/api/v1/offer/products/{model.id}/status",
            json={"new_status": "paused"},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "paused"
        assert body["offer_id"] == str(model.id)

    def test_invalid_transition_from_draft_to_paused_returns_409(
        self, db: Session, tenant_a: uuid.UUID
    ) -> None:
        model = create_product_model(
            tenant_a, name="Drafted", status=OfferStatus.DRAFT.value
        )
        db.add(model)
        db.flush()
        client = _build_client(db, tenant_a)

        response = client.post(
            f"/api/v1/offer/products/{model.id}/status",
            json={"new_status": "paused"},
        )

        assert response.status_code == 409

    def test_unknown_offer_returns_404(self, db: Session, tenant_a: uuid.UUID) -> None:
        client = _build_client(db, tenant_a)

        response = client.post(
            f"/api/v1/offer/products/{uuid.uuid4()}/status",
            json={"new_status": "active"},
        )

        assert response.status_code == 404
