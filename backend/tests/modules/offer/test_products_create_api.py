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
