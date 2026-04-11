"""Integration tests for ``GET /offer/products/{id}/campaigns``."""

import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.offer.api.campaigns import router


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


class TestGetCampaigns:
    def test_returns_empty_view_with_correct_shape(
        self, db: Session, tenant_a: uuid.UUID
    ) -> None:
        client = _build_client(db, tenant_a)

        response = client.get(f"/api/v1/offer/products/{uuid.uuid4()}/campaigns")

        assert response.status_code == 200
        body = response.json()
        assert "kpis" in body
        assert "campaigns" in body
        assert body["campaigns"] == []
        assert body["kpis"]["active_count"] == 0
        assert body["kpis"]["spend_7d"] == 0.0
        assert body["kpis"]["leads_7d"] == 0

    def test_accepts_filter_query_params(
        self, db: Session, tenant_a: uuid.UUID
    ) -> None:
        client = _build_client(db, tenant_a)

        response = client.get(
            f"/api/v1/offer/products/{uuid.uuid4()}/campaigns",
            params={"status": "active", "channel": "meta", "period": "7d"},
        )

        assert response.status_code == 200
