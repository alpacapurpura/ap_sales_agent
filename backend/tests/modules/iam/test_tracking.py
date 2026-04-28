"""Tests for IAM tracking endpoints."""

import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.api.tracking import public_router, router
from src.modules.iam.domain.user import User


def _make_user(tenant_id: uuid.UUID) -> User:
    return User(
        id=uuid.uuid4(),
        full_name="Alice Test",
        email="alice@example.com",
        clerk_id="clerk_test",
        role="admin",
        is_active=True,
        tenant_id=tenant_id,
    )


@pytest.fixture
def client(db, tenant_id):
    user = _make_user(tenant_id)
    app = FastAPI()
    app.include_router(router, prefix="/settings")
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


@pytest.fixture
def public_client(db):
    app = FastAPI()
    app.include_router(public_router, prefix="/public")
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


class TestGetTrackingConfig:
    def test_returns_200(self, client, seed_tenant):
        resp = client.get("/settings/tracking")
        assert resp.status_code == 200

    def test_returns_tracking_fields(self, client, seed_tenant):
        resp = client.get("/settings/tracking")
        body = resp.json()
        for field in ("gtm_container_id", "meta_pixel_id", "ga_measurement_id"):
            assert field in body

    def test_tenant_not_found_returns_404(self, db):
        user = _make_user(uuid.uuid4())
        app = FastAPI()
        app.include_router(router, prefix="/settings")
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        resp = TestClient(app).get("/settings/tracking")
        assert resp.status_code == 404

    def test_no_tenant_id_returns_400(self, db):
        user = User(
            id=uuid.uuid4(),
            full_name="No Tenant",
            email="no@x.com",
            clerk_id="c",
            role="user",
            is_active=True,
        )
        app = FastAPI()
        app.include_router(router, prefix="/settings")
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        resp = TestClient(app).get("/settings/tracking")
        assert resp.status_code == 400


class TestUpdateTrackingConfig:
    def test_patch_updates_gtm(self, client, seed_tenant):
        resp = client.patch("/settings/tracking", json={"gtm_container_id": "GTM-ABC123"})
        assert resp.status_code == 200
        assert resp.json()["gtm_container_id"] == "GTM-ABC123"

    def test_patch_preserves_existing_fields(self, client, seed_tenant):
        client.patch("/settings/tracking", json={"meta_pixel_id": "12345"})
        resp = client.patch("/settings/tracking", json={"ga_measurement_id": "G-TEST"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["meta_pixel_id"] == "12345"
        assert body["ga_measurement_id"] == "G-TEST"

    def test_patch_tenant_not_found_returns_404(self, db):
        user = _make_user(uuid.uuid4())
        app = FastAPI()
        app.include_router(router, prefix="/settings")
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        resp = TestClient(app).patch("/settings/tracking", json={"gtm_container_id": "GTM-X"})
        assert resp.status_code == 404


class TestPublicTrackingConfig:
    def test_returns_200_for_existing_tenant(self, public_client, seed_tenant, tenant_id):
        resp = public_client.get(f"/public/tracking/{tenant_id}")
        assert resp.status_code == 200

    def test_returns_404_for_unknown_tenant(self, public_client):
        resp = public_client.get(f"/public/tracking/{uuid.uuid4()}")
        assert resp.status_code == 404

    def test_returns_tracking_fields(self, public_client, seed_tenant, tenant_id):
        body = public_client.get(f"/public/tracking/{tenant_id}").json()
        for field in ("gtm_container_id", "meta_pixel_id", "ga_measurement_id"):
            assert field in body
