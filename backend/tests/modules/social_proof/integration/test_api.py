"""API integration tests for the social_proof endpoints.

Uses FastAPI's TestClient with dependency overrides — same pattern as
``tests/modules/brand/test_buyer_persona_api.py``.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.testclient import TestClient

from luana_core_iam.api.dependencies import get_current_user, get_db
from luana_core_iam.domain.user import User
from luana_core_social_proof.api.authority import router as authority_router
from luana_core_social_proof.api.placements import router as placements_router
from luana_core_social_proof.api.team_members import router as team_router
from luana_core_social_proof.api.testimonials import router as testimonials_router
from tests.modules.conftest import TENANT_A, TENANT_B, USER_A

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def _build_client(db: Session, tenant_id: uuid.UUID) -> TestClient:
    """TestClient with all 4 social_proof routers mounted + deps overridden."""
    app = FastAPI()
    app.include_router(testimonials_router, prefix="/api/v1/social-proof/testimonials")
    app.include_router(authority_router, prefix="/api/v1/social-proof/authority")
    app.include_router(team_router, prefix="/api/v1/social-proof/team")
    app.include_router(placements_router, prefix="/api/v1/social-proof/placements")

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


class TestTestimonialAPI:
    def test_create_list_get_patch_delete(self, db: Session) -> None:
        client = _build_client(db, TENANT_A)

        # CREATE
        resp = client.post(
            "/api/v1/social-proof/testimonials/",
            json={"author_name": "Juana Pérez", "content": "Brutal"},
        )
        assert resp.status_code == 200, resp.text
        testimonial_id = resp.json()["id"]
        assert resp.json()["author_name"] == "Juana Pérez"
        assert resp.json()["media_type"] == "text"

        # LIST
        listed = client.get("/api/v1/social-proof/testimonials/").json()
        assert len(listed) == 1

        # GET
        got = client.get(f"/api/v1/social-proof/testimonials/{testimonial_id}").json()
        assert got["content"] == "Brutal"

        # PATCH
        patched = client.patch(
            f"/api/v1/social-proof/testimonials/{testimonial_id}",
            json={"content": "Cambió"},
        ).json()
        assert patched["content"] == "Cambió"

        # DELETE
        assert (
            client.delete(
                f"/api/v1/social-proof/testimonials/{testimonial_id}",
            ).status_code
            == 204
        )
        # After delete → 404
        assert (
            client.get(
                f"/api/v1/social-proof/testimonials/{testimonial_id}",
            ).status_code
            == 404
        )

    def test_tenant_isolation_404_across_tenants(self, db: Session) -> None:
        client_a = _build_client(db, TENANT_A)
        created = client_a.post(
            "/api/v1/social-proof/testimonials/",
            json={"author_name": "Secreto"},
        ).json()

        client_b = _build_client(db, TENANT_B)
        assert (
            client_b.get(
                f"/api/v1/social-proof/testimonials/{created['id']}",
            ).status_code
            == 404
        )

    def test_clone_endpoint_creates_independent_row(self, db: Session) -> None:
        client = _build_client(db, TENANT_A)
        created = client.post(
            "/api/v1/social-proof/testimonials/",
            json={"author_name": "Ana", "content": "Original"},
        ).json()
        cloned = client.post(
            f"/api/v1/social-proof/testimonials/{created['id']}/clone",
        ).json()
        assert cloned["id"] != created["id"]
        assert cloned["author_name"] == "Ana"
        assert cloned["content"] == "Original"


class TestAuthorityAPI:
    def test_create_and_get(self, db: Session) -> None:
        client = _build_client(db, TENANT_A)
        resp = client.post(
            "/api/v1/social-proof/authority/",
            json={"entity_name": "Harvard", "authority_type": "certification"},
        )
        assert resp.status_code == 200, resp.text
        item_id = resp.json()["id"]
        assert client.get(f"/api/v1/social-proof/authority/{item_id}").status_code == 200


class TestTeamAPI:
    def test_create_and_get(self, db: Session) -> None:
        client = _build_client(db, TENANT_A)
        resp = client.post(
            "/api/v1/social-proof/team/",
            json={"name": "Chris Alpaca", "role": "Fundador"},
        )
        assert resp.status_code == 200, resp.text
        member_id = resp.json()["id"]
        assert client.get(f"/api/v1/social-proof/team/{member_id}").status_code == 200


class TestPlacementsAPI:
    def test_add_link_to_offer_surface(self, db: Session) -> None:
        client = _build_client(db, TENANT_A)
        testimonial = client.post(
            "/api/v1/social-proof/testimonials/",
            json={"author_name": "Ana"},
        ).json()

        offer_id = str(uuid.uuid4())
        resp = client.post(
            "/api/v1/social-proof/placements/",
            json={
                "source_table": "testimonial",
                "source_id": testimonial["id"],
                "surface_type": "offer",
                "surface_ref_id": offer_id,
                "sort_order": 1,
            },
        )
        assert resp.status_code == 200, resp.text
        placement_id = resp.json()["id"]
        assert resp.json()["surface_type"] == "offer"

        # PATCH reorder
        patched = client.patch(
            f"/api/v1/social-proof/placements/{placement_id}",
            json={"sort_order": 5},
        ).json()
        assert patched["sort_order"] == 5

        # Soft delete
        assert (
            client.delete(
                f"/api/v1/social-proof/placements/{placement_id}",
            ).status_code
            == 204
        )

    def test_placement_validation_offer_requires_ref_id(self, db: Session) -> None:
        client = _build_client(db, TENANT_A)
        testimonial = client.post(
            "/api/v1/social-proof/testimonials/",
            json={"author_name": "Ana"},
        ).json()
        resp = client.post(
            "/api/v1/social-proof/placements/",
            json={
                "source_table": "testimonial",
                "source_id": testimonial["id"],
                "surface_type": "offer",
                "surface_ref_id": None,
            },
        )
        assert resp.status_code == 422


class TestForSurfaceResolver:
    def test_returns_placed_items_grouped_by_kind(self, db: Session) -> None:
        client = _build_client(db, TENANT_A)
        testimonial = client.post(
            "/api/v1/social-proof/testimonials/",
            json={"author_name": "Ana", "content": "Genial"},
        ).json()
        authority = client.post(
            "/api/v1/social-proof/authority/",
            json={"entity_name": "Forbes", "authority_type": "media_mention"},
        ).json()

        offer_id = str(uuid.uuid4())
        client.post(
            "/api/v1/social-proof/placements/",
            json={
                "source_table": "testimonial",
                "source_id": testimonial["id"],
                "surface_type": "offer",
                "surface_ref_id": offer_id,
            },
        )
        client.post(
            "/api/v1/social-proof/placements/",
            json={
                "source_table": "authority_item",
                "source_id": authority["id"],
                "surface_type": "offer",
                "surface_ref_id": offer_id,
            },
        )

        resp = client.get(
            "/api/v1/social-proof/placements/for-surface",
            params={"surface_type": "offer", "surface_ref_id": offer_id},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert len(body["testimonials"]) == 1
        assert len(body["authority_items"]) == 1
        assert len(body["team_members"]) == 0
        assert body["testimonials"][0]["testimonial"]["content"] == "Genial"

    def test_include_brand_merges_brand_and_offer(self, db: Session) -> None:
        client = _build_client(db, TENANT_A)
        brand_t = client.post(
            "/api/v1/social-proof/testimonials/",
            json={"author_name": "Brand", "content": "Brand-level"},
        ).json()
        offer_t = client.post(
            "/api/v1/social-proof/testimonials/",
            json={"author_name": "Offer", "content": "Offer-level"},
        ).json()

        offer_id = str(uuid.uuid4())
        client.post(
            "/api/v1/social-proof/placements/",
            json={
                "source_table": "testimonial",
                "source_id": brand_t["id"],
                "surface_type": "brand_homepage",
                "surface_ref_id": None,
            },
        )
        client.post(
            "/api/v1/social-proof/placements/",
            json={
                "source_table": "testimonial",
                "source_id": offer_t["id"],
                "surface_type": "offer",
                "surface_ref_id": offer_id,
            },
        )

        # Without include_brand: only the offer placement
        body_a = client.get(
            "/api/v1/social-proof/placements/for-surface",
            params={"surface_type": "offer", "surface_ref_id": offer_id},
        ).json()
        assert len(body_a["testimonials"]) == 1

        # With include_brand: both merged
        body_b = client.get(
            "/api/v1/social-proof/placements/for-surface",
            params={
                "surface_type": "offer",
                "surface_ref_id": offer_id,
                "include_brand": True,
            },
        ).json()
        assert len(body_b["testimonials"]) == 2


class TestCascadeDeletion:
    def test_soft_delete_testimonial_cascades_to_placements(self, db: Session) -> None:
        client = _build_client(db, TENANT_A)
        testimonial = client.post(
            "/api/v1/social-proof/testimonials/",
            json={"author_name": "Ana"},
        ).json()
        offer_id = str(uuid.uuid4())
        placement = client.post(
            "/api/v1/social-proof/placements/",
            json={
                "source_table": "testimonial",
                "source_id": testimonial["id"],
                "surface_type": "offer",
                "surface_ref_id": offer_id,
            },
        ).json()

        assert (
            client.delete(
                f"/api/v1/social-proof/testimonials/{testimonial['id']}",
            ).status_code
            == 204
        )

        # Placement is soft-deleted — PATCH returns 404
        assert (
            client.patch(
                f"/api/v1/social-proof/placements/{placement['id']}",
                json={"sort_order": 9},
            ).status_code
            == 404
        )
