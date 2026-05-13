"""HTTP-level tests for tenant_profile API.

Exercises the error contract documented in CONTRACT.md §3.3:
- 400 invalid_business_types (length, duplicates, unknown slug)
- 409 rate_limited with next_allowed_change_at in body
- 403 forbidden when X-Tenant-ID missing or malformed
"""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.main import app
from luana_core_tenant_profile.domain.tenant_profile import RATE_LIMIT_WINDOW, TenantProfile
from luana_core_tenant_profile.infrastructure.repositories.tenant_profile_repository import (
    SqlTenantProfileRepository,
)
from luana_core_platform.domain.datetime_utils import utc_now
from tests.modules.tenant_profile.conftest import TYPE_A, TYPE_B


@pytest.fixture
def client(db_with_override) -> TestClient:
    """TestClient using the in-memory SQLite session from the db fixture."""
    return TestClient(app)


@pytest.fixture
def db_with_override(db):
    """Override the FastAPI ``get_db`` dependency to use the test session."""
    from luana_core_platform.core.database import get_db

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    yield db
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def auth_headers():
    """Shared header bag — per-test tenant IDs override as needed."""
    return {"X-Tenant-ID": str(uuid4())}


class TestGetProfile:
    def test_returns_empty_profile_for_new_tenant(self, client, auth_headers) -> None:
        response = client.get("/api/v1/tenant/profile", headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["business_types"] == []
        assert body["is_complete"] is False
        assert body["can_change_now"] is True
        assert body["next_allowed_change_at"] is None

    def test_returns_403_without_header(self, client) -> None:
        response = client.get("/api/v1/tenant/profile")
        assert response.status_code == 403

    def test_returns_403_for_non_uuid_header(self, client) -> None:
        response = client.get("/api/v1/tenant/profile", headers={"X-Tenant-ID": "not-a-uuid"})
        assert response.status_code == 403


class TestPatchProfile:
    def test_first_declaration_succeeds(self, client, auth_headers) -> None:
        response = client.patch(
            "/api/v1/tenant/profile",
            headers=auth_headers,
            json={"business_types": [TYPE_A.value]},
        )
        assert response.status_code == 200, response.json()
        body = response.json()
        assert body["business_types"] == [TYPE_A.value]
        assert body["is_complete"] is True
        assert body["declared_at"] is not None

    def test_rejects_empty_list(self, client, auth_headers) -> None:
        response = client.patch(
            "/api/v1/tenant/profile",
            headers=auth_headers,
            json={"business_types": []},
        )
        assert response.status_code == 422  # Pydantic min_length

    def test_rejects_too_many_entries(self, client, auth_headers) -> None:
        response = client.patch(
            "/api/v1/tenant/profile",
            headers=auth_headers,
            json={"business_types": [TYPE_A.value, TYPE_B.value, "consultor_profesional"]},
        )
        assert response.status_code == 422  # Pydantic max_length

    def test_rejects_unknown_slug(self, client, auth_headers) -> None:
        response = client.patch(
            "/api/v1/tenant/profile",
            headers=auth_headers,
            json={"business_types": ["not_a_real_slug"]},
        )
        assert response.status_code in {400, 422}

    def test_rejects_duplicates(self, client, auth_headers) -> None:
        response = client.patch(
            "/api/v1/tenant/profile",
            headers=auth_headers,
            json={"business_types": [TYPE_A.value, TYPE_A.value]},
        )
        assert response.status_code == 400
        body = response.json()
        assert body["detail"]["code"] == "invalid_business_types"

    def test_rate_limited_returns_409_with_next_allowed(self, client, auth_headers, db_with_override) -> None:
        # Seed: declared 5 days ago, still inside 30-day window
        from uuid import UUID

        tenant_id = UUID(auth_headers["X-Tenant-ID"])
        anchor = utc_now() - timedelta(days=5)
        profile = TenantProfile(
            tenant_id=tenant_id,
            business_types=(TYPE_A,),
            declared_at=anchor,
            updated_at=anchor,
            last_business_types_change_at=anchor,
        )
        SqlTenantProfileRepository(db_with_override).save(profile)

        response = client.patch(
            "/api/v1/tenant/profile",
            headers=auth_headers,
            json={"business_types": [TYPE_B.value]},
        )
        assert response.status_code == 409
        body = response.json()
        assert body["detail"]["code"] == "rate_limited"
        assert "next_allowed_change_at" in body["detail"]

    def test_change_after_window_succeeds(self, client, auth_headers, db_with_override) -> None:
        from uuid import UUID

        tenant_id = UUID(auth_headers["X-Tenant-ID"])
        anchor = utc_now() - RATE_LIMIT_WINDOW - timedelta(days=1)
        profile = TenantProfile(
            tenant_id=tenant_id,
            business_types=(TYPE_A,),
            declared_at=anchor,
            updated_at=anchor,
            last_business_types_change_at=anchor,
        )
        SqlTenantProfileRepository(db_with_override).save(profile)

        response = client.patch(
            "/api/v1/tenant/profile",
            headers=auth_headers,
            json={"business_types": [TYPE_B.value]},
        )
        assert response.status_code == 200
        assert response.json()["business_types"] == [TYPE_B.value]


class TestCatalog:
    def test_returns_full_catalog_shape(self, client) -> None:
        response = client.get("/api/v1/catalogs/business-types")
        assert response.status_code == 200
        body = response.json()
        assert "version" in body
        assert isinstance(body["business_types"], list)
        assert len(body["business_types"]) == 9  # ExpertBusinessType has 9 members
        sample = body["business_types"][0]
        for key in ("slug", "label_es", "description_es", "icon_name", "examples_es"):
            assert key in sample

    def test_catalog_does_not_require_tenant_header(self, client) -> None:
        # Catalog is tenant-agnostic metadata; may require auth but not X-Tenant-ID.
        response = client.get("/api/v1/catalogs/business-types")
        assert response.status_code == 200
