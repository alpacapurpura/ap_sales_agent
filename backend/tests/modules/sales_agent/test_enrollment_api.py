"""API route tests for enrollments (Phase 5)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from luana_core_platform.core.database import get_db
from luana_core_iam.api.dependencies import get_current_user
from luana_core_sales_agent.api.enrollments import router as enrollments_router
from tests.modules.offer.conftest import create_product_model

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

_TENANT = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


class _StubUser:
    def __init__(self, tenant_id: uuid.UUID) -> None:
        self.tenant_id = tenant_id
        self.id = uuid.uuid4()


@pytest.fixture
def client(db: Session) -> TestClient:
    app = FastAPI()
    app.include_router(enrollments_router, prefix="/api/v1/sales-agent")
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: _StubUser(_TENANT)
    return TestClient(app)


@pytest.fixture
def offer_id(db: Session) -> uuid.UUID:
    model = create_product_model(_TENANT, archetype="programa")
    db.add(model)
    db.flush()
    return model.id


class TestCreate:
    def test_post_returns_201(self, client: TestClient, offer_id: uuid.UUID) -> None:
        payload: dict[str, Any] = {
            "offer_id": str(offer_id),
            "contact_id": str(uuid.uuid4()),
            "edition_id": str(uuid.uuid4()),
            "status": "intent",
        }
        response = client.post("/api/v1/sales-agent/enrollments", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "intent"
        assert data["offer_id"] == str(offer_id)


class TestList:
    def test_filter_by_status(self, client: TestClient, offer_id: uuid.UUID) -> None:
        # Create one waitlist + one intent.
        client.post(
            "/api/v1/sales-agent/enrollments",
            json={
                "offer_id": str(offer_id),
                "contact_id": str(uuid.uuid4()),
                "edition_id": None,
            },
        )
        client.post(
            "/api/v1/sales-agent/enrollments",
            json={
                "offer_id": str(offer_id),
                "contact_id": str(uuid.uuid4()),
                "edition_id": str(uuid.uuid4()),
            },
        )

        response = client.get(
            "/api/v1/sales-agent/enrollments",
            params={"status": "waitlist"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["items"][0]["status"] == "waitlist"


class TestMarkPaid:
    def test_sets_paid_at(self, client: TestClient, offer_id: uuid.UUID) -> None:
        create_resp = client.post(
            "/api/v1/sales-agent/enrollments",
            json={
                "offer_id": str(offer_id),
                "contact_id": str(uuid.uuid4()),
                "edition_id": str(uuid.uuid4()),
            },
        )
        enrollment_id = create_resp.json()["id"]

        # Advance to PAYMENT_PENDING first.
        client.patch(
            f"/api/v1/sales-agent/enrollments/{enrollment_id}/status",
            json={"status": "payment_pending"},
        )
        paid_resp = client.post(
            f"/api/v1/sales-agent/enrollments/{enrollment_id}/mark-paid",
            json={"provider": "manual", "transaction_id": "tx_test"},
        )
        assert paid_resp.status_code == 200
        assert paid_resp.json()["status"] == "paid"
        assert paid_resp.json()["paid_at"] is not None


class TestWaitlistFilter:
    def test_endpoint_returns_only_waitlist(
        self,
        client: TestClient,
        offer_id: uuid.UUID,
    ) -> None:
        client.post(
            "/api/v1/sales-agent/enrollments",
            json={
                "offer_id": str(offer_id),
                "contact_id": str(uuid.uuid4()),
                "edition_id": None,
            },
        )
        client.post(
            "/api/v1/sales-agent/enrollments",
            json={
                "offer_id": str(offer_id),
                "contact_id": str(uuid.uuid4()),
                "edition_id": str(uuid.uuid4()),
            },
        )
        response = client.get(
            "/api/v1/sales-agent/enrollments/waitlist",
            params={"offer_id": str(offer_id)},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 1
        assert body["items"][0]["status"] == "waitlist"
