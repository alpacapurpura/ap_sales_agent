"""Tests for plan approval/rejection stub endpoints."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from luana_core_platform.core.database import get_db
from luana_core_copilot.api.plan import router
from luana_core_iam.api.dependencies import get_current_user, get_tenant_context


def _build_client(tenant_id):
    """Build a TestClient with mocked auth dependencies."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/copilot")
    uid = uuid4()
    mock_db = MagicMock()

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=uid,
        tenant_id=tenant_id,
    )
    app.dependency_overrides[get_tenant_context] = lambda: tenant_id

    return TestClient(app)


class TestPlanApprove:
    """POST /api/v1/copilot/plan/{plan_id}/approve → 202."""

    def test_approve_returns_202(self) -> None:
        """POST approve returns 202 Accepted."""
        tenant_id = uuid4()
        client = _build_client(tenant_id)
        plan_id = uuid4()

        resp = client.post(
            f"/api/v1/copilot/plan/{plan_id}/approve",
            headers={"X-Tenant-ID": str(tenant_id)},
        )

        assert resp.status_code == 202

    def test_approve_response_has_plan_id(self) -> None:
        """Approve response includes plan_id."""
        tenant_id = uuid4()
        client = _build_client(tenant_id)
        plan_id = uuid4()

        resp = client.post(
            f"/api/v1/copilot/plan/{plan_id}/approve",
            headers={"X-Tenant-ID": str(tenant_id)},
        )

        data = resp.json()
        assert "plan_id" in data


class TestPlanReject:
    """POST /api/v1/copilot/plan/{plan_id}/reject → 202."""

    def test_reject_returns_202(self) -> None:
        """POST reject returns 202 Accepted."""
        tenant_id = uuid4()
        client = _build_client(tenant_id)
        plan_id = uuid4()

        resp = client.post(
            f"/api/v1/copilot/plan/{plan_id}/reject",
            headers={"X-Tenant-ID": str(tenant_id)},
        )

        assert resp.status_code == 202

    def test_reject_response_has_plan_id(self) -> None:
        """Reject response includes plan_id."""
        tenant_id = uuid4()
        client = _build_client(tenant_id)
        plan_id = uuid4()

        resp = client.post(
            f"/api/v1/copilot/plan/{plan_id}/reject",
            headers={"X-Tenant-ID": str(tenant_id)},
        )

        data = resp.json()
        assert "plan_id" in data
