"""Tests for BuyerPersona REST API — CRUD + tenant isolation."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.brand.api.buyer_personas import router
from src.modules.iam.api.dependencies import get_current_user, get_db
from src.modules.iam.domain.user import User
from tests.modules.conftest import TENANT_A, TENANT_B, USER_A

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def _build_client(db: Session, tenant_id: uuid.UUID) -> TestClient:
    """Build a TestClient with overridden dependencies."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/brand/buyer-personas")

    fake_user = User(
        id=USER_A,
        email="test@example.com",
        full_name="Test User",
        tenant_id=tenant_id,
        is_active=True,
    )
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: fake_user
    return TestClient(app)


class TestBuyerPersonaAPI:
    """CRUD tests for buyer persona endpoints."""

    def test_create_persona(self, db: Session) -> None:
        """POST creates a persona and returns it with an id."""
        client = _build_client(db, TENANT_A)
        resp = client.post(
            "/api/v1/brand/buyer-personas/",
            json={"name": "Mamá Rural"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Mamá Rural"
        assert data["scope"] == "GLOBAL"
        assert data["completeness_score"] == 0.0
        assert "id" in data

    def test_list_personas(self, db: Session) -> None:
        """GET list returns personas for the tenant."""
        client = _build_client(db, TENANT_A)
        client.post("/api/v1/brand/buyer-personas/", json={"name": "P1"})
        client.post("/api/v1/brand/buyer-personas/", json={"name": "P2"})

        resp = client.get("/api/v1/brand/buyer-personas/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_get_persona(self, db: Session) -> None:
        """GET by id returns the persona."""
        client = _build_client(db, TENANT_A)
        created = client.post(
            "/api/v1/brand/buyer-personas/",
            json={"name": "Test"},
        ).json()

        resp = client.get(f"/api/v1/brand/buyer-personas/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test"

    def test_patch_persona_section(self, db: Session) -> None:
        """PATCH updates specific fields and recalculates completeness."""
        client = _build_client(db, TENANT_A)
        created = client.post(
            "/api/v1/brand/buyer-personas/",
            json={"name": "Test"},
        ).json()

        resp = client.patch(
            f"/api/v1/brand/buyer-personas/{created['id']}",
            json={
                "demographics": {"age_range": "25-35", "location": "LATAM"},
                "pain_points": [{"description": "No time", "intensity": "high"}],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["demographics"]["age_range"] == "25-35"
        assert len(data["pain_points"]) == 1
        assert data["completeness_score"] > 0.0

    def test_delete_persona(self, db: Session) -> None:
        """DELETE soft-deletes (persona no longer in list)."""
        client = _build_client(db, TENANT_A)
        created = client.post(
            "/api/v1/brand/buyer-personas/",
            json={"name": "Doomed"},
        ).json()

        resp = client.delete(f"/api/v1/brand/buyer-personas/{created['id']}")
        assert resp.status_code == 204

        resp = client.get("/api/v1/brand/buyer-personas/")
        assert len(resp.json()) == 0

    def test_get_persona_wrong_tenant_returns_404(self, db: Session) -> None:
        """Persona created by TENANT_A is invisible to TENANT_B."""
        client_a = _build_client(db, TENANT_A)
        created = client_a.post(
            "/api/v1/brand/buyer-personas/",
            json={"name": "Secret"},
        ).json()

        client_b = _build_client(db, TENANT_B)
        resp = client_b.get(f"/api/v1/brand/buyer-personas/{created['id']}")
        assert resp.status_code == 404

    def test_patch_nonexistent_returns_404(self, db: Session) -> None:
        """PATCH on a nonexistent persona returns 404."""
        client = _build_client(db, TENANT_A)
        fake_id = str(uuid.uuid4())
        resp = client.patch(
            f"/api/v1/brand/buyer-personas/{fake_id}",
            json={"name": "Ghost"},
        )
        assert resp.status_code == 404
