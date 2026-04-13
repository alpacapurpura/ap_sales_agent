"""Integration tests for the offer Assets CRUD router."""

import io
import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.offer.api.assets import router
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


class TestListAssets:
    def test_empty_list_returns_zero_total(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ) -> None:
        model = create_product_model(tenant_a, name="Empty")
        db.add(model)
        db.flush()
        client = _build_client(db, tenant_a)

        response = client.get(f"/api/v1/offer/products/{model.id}/assets")

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 0
        assert body["items"] == []
        assert body["limit"] == 24
        assert body["offset"] == 0


class TestUploadAsset:
    def test_upload_creates_ready_external_asset(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ) -> None:
        model = create_product_model(tenant_a, name="Upload")
        db.add(model)
        db.flush()
        client = _build_client(db, tenant_a)

        response = client.post(
            f"/api/v1/offer/products/{model.id}/assets/upload",
            data={"name": "Hero Flyer", "type": "flyer"},
            files={"file": ("flyer.png", io.BytesIO(b"fake-png-bytes"), "image/png")},
        )

        assert response.status_code == 201, response.text
        body = response.json()
        assert body["type"] == "flyer"
        assert body["source"] == "external"
        assert body["status"] == "ready"
        assert body["file_url"] is not None
        assert body["file_url"].startswith("https://stub.local/")


class TestGetAsset:
    def test_unknown_asset_returns_404(self, db: Session, tenant_a: uuid.UUID) -> None:
        model = create_product_model(tenant_a, name="GetMissing")
        db.add(model)
        db.flush()
        client = _build_client(db, tenant_a)

        response = client.get(
            f"/api/v1/offer/products/{model.id}/assets/{uuid.uuid4()}",
        )

        assert response.status_code == 404
