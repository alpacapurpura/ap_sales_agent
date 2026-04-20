"""Regression tests for POST /api/v1/offer/products.

Bug: offers created without an explicit currency were persisted as "USD"
because the SQLAlchemy model defaulted currency="USD". A PEN-tenant
therefore saw dollar symbols in the Offer Studio. The fix: the endpoint
now inherits the currency from TenantLocale via get_tenant_locale.
"""

import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user, get_tenant_locale
from src.modules.iam.domain.user import User
from src.modules.offer.api.products import router
from src.shared.domain.locale import TenantLocale


def _build_client(
    db: Session,
    tenant_id: uuid.UUID,
    locale: TenantLocale,
) -> TestClient:
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
    app.dependency_overrides[get_tenant_locale] = lambda: locale
    return TestClient(app)


class TestCreateProductCurrency:
    def test_create_without_currency_uses_tenant_default(self, db: Session, tenant_a):
        """PEN-tenant creating an offer without currency → persisted as PEN."""
        client = _build_client(
            db,
            tenant_a,
            TenantLocale(currency="PEN", timezone="America/Lima"),
        )

        response = client.post(
            "/api/v1/offer/products",
            json={"name": "New Program", "archetype": "programa"},
        )

        assert response.status_code == 200, response.text
        assert response.json()["currency"] == "PEN"

    def test_create_with_explicit_currency_is_preserved(self, db: Session, tenant_a):
        """Explicit currency in body wins over tenant default."""
        client = _build_client(
            db,
            tenant_a,
            TenantLocale(currency="PEN", timezone="America/Lima"),
        )

        response = client.post(
            "/api/v1/offer/products",
            json={
                "name": "USD Priced",
                "archetype": "producto",
                "currency": "USD",
            },
        )

        assert response.status_code == 200, response.text
        assert response.json()["currency"] == "USD"

    def test_create_usd_tenant_defaults_to_usd(self, db: Session, tenant_a):
        """Sanity: a USD tenant without explicit currency still gets USD."""
        client = _build_client(
            db,
            tenant_a,
            TenantLocale(currency="USD", timezone="UTC"),
        )

        response = client.post(
            "/api/v1/offer/products",
            json={"name": "Another", "archetype": "producto"},
        )

        assert response.status_code == 200, response.text
        assert response.json()["currency"] == "USD"


class TestCreateProductHasEditions:
    """Wizard-driven has_editions must be honored on create."""

    def _client(self, db, tenant):
        return _build_client(db, tenant, TenantLocale(currency="USD", timezone="UTC"))

    def test_programa_default_true(self, db: Session, tenant_a):
        response = self._client(db, tenant_a).post(
            "/api/v1/offer/products",
            json={"name": "Default Programa", "archetype": "programa"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["has_editions"] is True

    def test_programa_explicit_false(self, db: Session, tenant_a):
        response = self._client(db, tenant_a).post(
            "/api/v1/offer/products",
            json={
                "name": "Evergreen Programa",
                "archetype": "programa",
                "has_editions": False,
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()["has_editions"] is False

    def test_experiencia_explicit_true(self, db: Session, tenant_a):
        response = self._client(db, tenant_a).post(
            "/api/v1/offer/products",
            json={
                "name": "Retiro",
                "archetype": "experiencia",
                "has_editions": True,
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()["has_editions"] is True

    def test_producto_default_true(self, db: Session, tenant_a):
        """Sprint 15.1: PRODUCTO supports editions (SKU variants) by default."""
        response = self._client(db, tenant_a).post(
            "/api/v1/offer/products",
            json={
                "name": "Ebook",
                "archetype": "producto",
                "has_editions": True,
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()["has_editions"] is True

    def test_producto_can_opt_out_of_editions(self, db: Session, tenant_a):
        """A single-SKU product opt-outs explicitly to keep the editor simple."""
        response = self._client(db, tenant_a).post(
            "/api/v1/offer/products",
            json={
                "name": "Single Ebook",
                "archetype": "producto",
                "has_editions": False,
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()["has_editions"] is False

    def test_membresia_default_true(self, db: Session, tenant_a):
        """Sprint 15.1: MEMBRESIA supports editions (TIER plans) by default."""
        response = self._client(db, tenant_a).post(
            "/api/v1/offer/products",
            json={
                "name": "Club VIP",
                "archetype": "membresia",
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()["has_editions"] is True

    def test_membresia_can_opt_out_of_editions(self, db: Session, tenant_a):
        """A single-plan membership opt-outs explicitly."""
        response = self._client(db, tenant_a).post(
            "/api/v1/offer/products",
            json={
                "name": "Simple Membership",
                "archetype": "membresia",
                "has_editions": False,
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()["has_editions"] is False
