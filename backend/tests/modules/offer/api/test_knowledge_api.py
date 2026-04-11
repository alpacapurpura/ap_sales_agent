"""Integration tests for the offer Knowledge CRUD router."""

import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.offer.api.knowledge import router
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


class TestListKnowledgeSources:
    def test_empty_list_returns_zero_total(
        self, db: Session, tenant_a: uuid.UUID
    ) -> None:
        model = create_product_model(tenant_a, name="KnEmpty")
        db.add(model)
        db.flush()
        client = _build_client(db, tenant_a)

        response = client.get(f"/api/v1/offer/products/{model.id}/knowledge")

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 0
        assert body["items"] == []


class TestAddKnowledgeUrl:
    def test_url_source_is_persisted(self, db: Session, tenant_a: uuid.UUID) -> None:
        model = create_product_model(tenant_a, name="KnUrl")
        db.add(model)
        db.flush()
        client = _build_client(db, tenant_a)

        response = client.post(
            f"/api/v1/offer/products/{model.id}/knowledge/url",
            json={
                "url": "https://example.com/guide",
                "type": "url_article",
                "name": "Guide",
            },
        )

        assert response.status_code == 201, response.text
        body = response.json()
        assert body["source_url"] == "https://example.com/guide"
        assert body["type"] == "url_article"
        assert body["name"] == "Guide"

        list_response = client.get(f"/api/v1/offer/products/{model.id}/knowledge")
        assert list_response.status_code == 200
        assert list_response.json()["total"] == 1


class TestDeleteKnowledgeSource:
    def test_unknown_source_returns_404(self, db: Session, tenant_a: uuid.UUID) -> None:
        model = create_product_model(tenant_a, name="KnDel")
        db.add(model)
        db.flush()
        client = _build_client(db, tenant_a)

        response = client.delete(
            f"/api/v1/offer/products/{model.id}/knowledge/{uuid.uuid4()}"
        )

        assert response.status_code == 404
