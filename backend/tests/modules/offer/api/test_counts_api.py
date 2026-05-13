"""Integration tests for ``GET /offer/products/{id}/counts``."""

import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from luana_core_platform.core.database import get_db
from luana_core_iam.api.dependencies import get_current_user
from luana_core_iam.domain.user import User
from src.modules.offer.api.counts import router
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


class TestGetCounts:
    def test_returns_zero_counts_for_fresh_offer(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ) -> None:
        model = create_product_model(tenant_a, name="Fresh")
        db.add(model)
        db.flush()
        client = _build_client(db, tenant_a)

        response = client.get(f"/api/v1/offer/products/{model.id}/counts")

        assert response.status_code == 200
        body = response.json()
        assert body == {"assets": 0, "campaigns": 0, "knowledge": 0}

    def test_response_shape_contains_required_keys(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ) -> None:
        model = create_product_model(tenant_a, name="Shape")
        db.add(model)
        db.flush()
        client = _build_client(db, tenant_a)

        response = client.get(f"/api/v1/offer/products/{model.id}/counts")

        assert response.status_code == 200
        body = response.json()
        assert set(body.keys()) == {"assets", "campaigns", "knowledge"}
