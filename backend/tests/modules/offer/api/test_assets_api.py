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


class TestEditionFilter:
    def test_list_filters_by_edition_id_query_param(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ) -> None:
        model = create_product_model(tenant_a, name="EditionFilter")
        db.add(model)
        db.flush()
        client = _build_client(db, tenant_a)

        edition_a = uuid.uuid4()
        edition_b = uuid.uuid4()

        # Upload one asset per edition scope.
        for edition_id in (edition_a, edition_b):
            client.post(
                f"/api/v1/offer/products/{model.id}/assets/upload",
                data={
                    "name": f"for {edition_id}",
                    "type": "flyer",
                    "edition_id": str(edition_id),
                },
                files={"file": ("x.png", io.BytesIO(b"x"), "image/png")},
            )

        resp_a = client.get(
            f"/api/v1/offer/products/{model.id}/assets",
            params={"edition_id": str(edition_a)},
        )
        assert resp_a.status_code == 200
        body_a = resp_a.json()
        assert body_a["total"] == 1
        assert body_a["items"][0]["edition_id"] == str(edition_a)

        # Legacy call without edition filter sees both.
        resp_all = client.get(f"/api/v1/offer/products/{model.id}/assets")
        assert resp_all.json()["total"] == 2
