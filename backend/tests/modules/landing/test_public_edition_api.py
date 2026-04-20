"""Smoke tests for the per-edition public landing routes (Phase 8)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.database import get_db
from src.modules.iam.infrastructure.models.tenant_model import TenantModel
from src.modules.landing.api.public_edition import router as public_edition_router
from src.modules.landing.domain.content import LandingPageConfig
from src.modules.landing.domain.landing_page import LandingPage
from src.modules.landing.infrastructure.repositories.landing_repository import (
    LandingRepository,
)
from src.modules.offer.domain.enums import VariantStructure
from src.modules.offer.domain.launch_edition import EditionStatus, EditionVisibility
from src.modules.offer.infrastructure.repositories.launch_edition_repository import (
    LaunchEditionRepository,
)
from tests.modules.offer.conftest import create_product_model

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


_TENANT_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_TENANT_SLUG = "acme"


@pytest.fixture
def client(db: Session) -> TestClient:
    app = FastAPI()
    app.include_router(public_edition_router, prefix="/api/v1/public")
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app, follow_redirects=False)


@pytest.fixture
def tenant_row(db: Session) -> TenantModel:
    tenant = TenantModel(
        id=_TENANT_ID,
        slug=_TENANT_SLUG,
        name="Acme",
    )
    db.add(tenant)
    db.flush()
    return tenant


@pytest.fixture
def offer_with_edition(db: Session, tenant_row: TenantModel) -> tuple[uuid.UUID, int]:
    offer = create_product_model(_TENANT_ID, archetype="programa")
    db.add(offer)
    db.flush()

    edition = LaunchEditionRepository(db).create(
        offer_id=offer.id,
        tenant_id=_TENANT_ID,
        variant_structure=VariantStructure.TEMPORAL_COHORT,
        start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        status=EditionStatus.UPCOMING,
        visibility=EditionVisibility.PUBLIC,
    )
    # Published landing for that edition.
    config_dict = {
        "archetype": "THE_SQUEEZE",
        "slug": "programa-jul",
        "content": {
            "headline": "Programa Jul 2026",
            "subheadline": "Aprende con nosotros",
            "bullets": ["Feedback 1:1", "Comunidad", "Certificado"],
            "cta_text": "Inscribirme",
            "privacy_text": "Tu info está protegida.",
        },
    }
    landing = LandingPage(
        id=uuid.uuid4(),
        tenant_id=_TENANT_ID,
        offer_id=offer.id,
        edition_id=edition.id,
        slug="programa-jul",
        config=LandingPageConfig(**config_dict),
        is_published=True,
    )
    LandingRepository(db).create(landing)
    return offer.id, edition.edition_number


class TestRedirect:
    def test_unknown_tenant_returns_404(self, client: TestClient) -> None:
        response = client.get(f"/api/v1/public/tenants/ghost/offers/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_redirects_to_edition(
        self,
        client: TestClient,
        offer_with_edition: tuple[uuid.UUID, int],
    ) -> None:
        offer_id, edition_number = offer_with_edition
        response = client.get(f"/api/v1/public/tenants/{_TENANT_SLUG}/offers/{offer_id}")
        assert response.status_code == 302
        assert f"/ediciones/{edition_number}" in response.headers["location"]

    def test_no_public_edition_returns_404(
        self,
        client: TestClient,
        tenant_row: TenantModel,
        db: Session,
    ) -> None:
        offer = create_product_model(_TENANT_ID, archetype="programa")
        db.add(offer)
        db.flush()
        response = client.get(f"/api/v1/public/tenants/{_TENANT_SLUG}/offers/{offer.id}")
        assert response.status_code == 404


class TestEditionLanding:
    def test_serves_edition_landing(
        self,
        client: TestClient,
        offer_with_edition: tuple[uuid.UUID, int],
    ) -> None:
        offer_id, edition_number = offer_with_edition
        response = client.get(
            f"/api/v1/public/tenants/{_TENANT_SLUG}/offers/{offer_id}/ediciones/{edition_number}",
        )
        assert response.status_code == 200
        assert response.json()["slug"] == "programa-jul"

    def test_bogus_edition_number_returns_404(
        self,
        client: TestClient,
        offer_with_edition: tuple[uuid.UUID, int],
    ) -> None:
        offer_id, _ = offer_with_edition
        response = client.get(
            f"/api/v1/public/tenants/{_TENANT_SLUG}/offers/{offer_id}/ediciones/99",
        )
        assert response.status_code == 404
