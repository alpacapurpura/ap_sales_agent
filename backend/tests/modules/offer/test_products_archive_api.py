"""Integration tests for the offer/products archive + delete endpoints."""

import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.offer.api.products import router
from src.shared.domain.datetime_utils import utc_now
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


class TestArchiveEndpoint:
    def test_archive_sets_archived_at(self, db: Session, tenant_a):
        model = create_product_model(tenant_a, name="ToArchive")
        db.add(model)
        db.flush()
        client = _build_client(db, tenant_a)

        response = client.post(f"/api/v1/offer/products/{model.id}/archive")

        assert response.status_code == 200
        body = response.json()
        assert body["archived_at"] is not None

    def test_archive_not_found_returns_404(self, db: Session, tenant_a):
        client = _build_client(db, tenant_a)
        response = client.post(f"/api/v1/offer/products/{uuid.uuid4()}/archive")
        assert response.status_code == 404


class TestRestoreEndpoint:
    def test_restore_clears_archived_at(self, db: Session, tenant_a):
        model = create_product_model(tenant_a, archived_at=utc_now())
        db.add(model)
        db.flush()
        client = _build_client(db, tenant_a)

        response = client.post(f"/api/v1/offer/products/{model.id}/restore")

        assert response.status_code == 200
        assert response.json()["archived_at"] is None


class TestArchivedListEndpoint:
    def test_list_archived_returns_only_archived(self, db: Session, tenant_a):
        db.add_all(
            [
                create_product_model(tenant_a, name="Active"),
                create_product_model(tenant_a, name="Archived", archived_at=utc_now()),
            ]
        )
        db.flush()
        client = _build_client(db, tenant_a)

        response = client.get("/api/v1/offer/products/archived")

        assert response.status_code == 200
        names = [o["public_name"] for o in response.json()]
        assert names == ["Archived"]

    def test_list_active_excludes_archived(self, db: Session, tenant_a):
        db.add_all(
            [
                create_product_model(tenant_a, name="Active"),
                create_product_model(tenant_a, name="Archived", archived_at=utc_now()),
            ]
        )
        db.flush()
        client = _build_client(db, tenant_a)

        response = client.get("/api/v1/offer/products")

        assert response.status_code == 200
        names = [o["public_name"] for o in response.json()]
        assert "Active" in names and "Archived" not in names


class TestDeleteEndpoint:
    def test_delete_on_archived_returns_204(self, db: Session, tenant_a):
        model = create_product_model(tenant_a, archived_at=utc_now())
        db.add(model)
        db.flush()
        client = _build_client(db, tenant_a)

        response = client.delete(f"/api/v1/offer/products/{model.id}")
        assert response.status_code == 204

        # Verify it's gone from both lists
        archived_response = client.get("/api/v1/offer/products/archived")
        assert all(o["id"] != str(model.id) for o in archived_response.json())

    def test_delete_on_active_returns_409(self, db: Session, tenant_a):
        model = create_product_model(tenant_a)
        db.add(model)
        db.flush()
        client = _build_client(db, tenant_a)

        response = client.delete(f"/api/v1/offer/products/{model.id}")
        assert response.status_code == 409

    def test_delete_not_found_returns_404(self, db: Session, tenant_a):
        client = _build_client(db, tenant_a)
        response = client.delete(f"/api/v1/offer/products/{uuid.uuid4()}")
        assert response.status_code == 404
