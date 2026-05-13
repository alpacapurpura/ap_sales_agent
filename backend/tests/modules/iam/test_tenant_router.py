"""Tests for IAM tenant router endpoints."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from luana_core_platform.core.database import get_db
from luana_core_iam.api.routers.tenant_router import router


@pytest.fixture
def client(db):
    app = FastAPI()
    app.include_router(router, prefix="/tenants")
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


class TestListTenants:
    def test_returns_200_empty(self, client):
        resp = client.get("/tenants/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_seeded_tenant(self, client, seed_tenant):
        resp = client.get("/tenants/")
        assert resp.status_code == 200
        slugs = [t["slug"] for t in resp.json()]
        assert "test-tenant" in slugs

    def test_returns_multiple_tenants(self, client, seed_tenant, seed_other_tenant):
        resp = client.get("/tenants/")
        assert resp.status_code == 200
        assert len(resp.json()) >= 2


class TestCreateTenant:
    def test_creates_tenant_returns_200(self, client):
        resp = client.post(
            "/tenants/",
            params={
                "name": "New Corp",
                "slug": "new-corp",
                "company_name": "New Corp Ltd",
                "agent_persona": "Helpful",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["slug"] == "new-corp"

    def test_duplicate_slug_returns_400(self, client, seed_tenant):
        resp = client.post(
            "/tenants/",
            params={
                "name": "Dupe",
                "slug": "test-tenant",
                "company_name": "Dupe Co",
                "agent_persona": "X",
            },
        )
        assert resp.status_code == 400
