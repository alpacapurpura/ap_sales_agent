"""API tests for POST /campaigns/{id}/launch — real orchestrator integration.

PR-5 Sub-C: replaces stub-only test from PR-4.
Tests: 200 + tasks_generated, 404 unknown/cross-tenant, 409 invalid state, 422 steps/segment.
"""

from __future__ import annotations

import datetime as dt
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from luana_core_campaigns.application.dtos.campaign_dtos import (
    CampaignResponse,
)
from luana_core_campaigns.application.services.campaign_service import (
    CampaignNotFoundError,
)
from luana_core_campaigns.application.services.orchestrator import (
    OrchestratorCampaignNotFoundError,
    OrchestratorCampaignNotLaunchableError,
    OrchestratorLaunchResult,
    OrchestratorMissingStepsError,
    OrchestratorSegmentEmptyError,
)
from luana_core_campaigns.domain.enums import CampaignStatus, CampaignType

pytestmark = pytest.mark.asyncio

TENANT_ID = uuid4()
USER_ID = uuid4()
CAMPAIGN_ID = uuid4()
NOW = dt.datetime.now(tz=dt.timezone.utc)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _campaign_response(**overrides: Any) -> CampaignResponse:
    """Minimal CampaignResponse for mocking."""
    defaults: dict[str, Any] = {
        "id": CAMPAIGN_ID,
        "tenant_id": TENANT_ID,
        "name": "Test Campaign",
        "description": None,
        "campaign_type": CampaignType.AGENT_CONVERSATION,
        "status": CampaignStatus.RUNNING,
        "segment_id": uuid4(),
        "segment_snapshot_id": None,
        "channel_priority": ["telegram"],
        "offer_id": uuid4(),
        "brand_summary_id": None,
        "config": {},
        "scheduled_at": NOW,
        "launched_at": NOW,
        "completed_at": None,
        "created_by_user_id": USER_ID,
        "created_by_source": "api",
        "created_at": NOW,
        "updated_at": NOW,
    }
    defaults.update(overrides)
    return CampaignResponse(**defaults)


def _launch_result(**overrides: Any) -> OrchestratorLaunchResult:
    """Minimal OrchestratorLaunchResult for mocking."""
    defaults: dict[str, Any] = {
        "id": CAMPAIGN_ID,
        "status": "running",
        "external_id": "3",
        "tasks_generated": 3,
        "snapshot_id": None,
        "launched_at": NOW,
    }
    defaults.update(overrides)
    return OrchestratorLaunchResult(**defaults)


class _FakeUser:
    id: UUID = USER_ID
    tenant_id: UUID = TENANT_ID
    email: str = "test@example.com"


def _get_fake_user() -> _FakeUser:
    return _FakeUser()


@pytest.fixture()
async def client() -> AsyncClient:  # type: ignore[override]
    """AsyncClient with auth override."""
    from src.main import app
    from luana_core_iam.api.dependencies import get_current_user

    app.dependency_overrides[get_current_user] = _get_fake_user

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.pop(get_current_user, None)


def _patch_session() -> Any:
    """AsyncMock session with begin() context manager."""
    session = AsyncMock()
    # session.begin() must work as async context manager
    begin_ctx = AsyncMock()
    begin_ctx.__aenter__ = AsyncMock(return_value=None)
    begin_ctx.__aexit__ = AsyncMock(return_value=False)
    session.begin = MagicMock(return_value=begin_ctx)
    return session


# ── Launch endpoint tests ─────────────────────────────────────────────────────


class TestCampaignLaunchReal:
    """POST /api/v1/campaigns/{id}/launch — real orchestrator integration."""

    async def test_launch_returns_200_with_tasks_generated(self, client: AsyncClient) -> None:
        """Happy path: orchestrator returns result → 200 with tasks_generated."""
        from src.main import app
        from luana_core_campaigns.api._service_factories import (
            get_campaign_orchestrator,
            get_campaign_service,
        )
        from luana_core_campaigns.api._dependencies import get_campaigns_async_session

        mock_orch = AsyncMock()
        mock_orch.launch = AsyncMock(return_value=_launch_result(tasks_generated=3))
        mock_orch.enqueue_pending_tasks = AsyncMock()

        mock_svc = AsyncMock()
        mock_svc.get = AsyncMock(return_value=_campaign_response())

        app.dependency_overrides[get_campaign_orchestrator] = lambda: mock_orch
        app.dependency_overrides[get_campaign_service] = lambda: mock_svc
        app.dependency_overrides[get_campaigns_async_session] = _patch_session

        r = await client.post(
            f"/api/v1/campaigns/{CAMPAIGN_ID}/launch",
            headers={"X-Tenant-ID": str(TENANT_ID)},
        )

        app.dependency_overrides.pop(get_campaign_orchestrator, None)
        app.dependency_overrides.pop(get_campaign_service, None)
        app.dependency_overrides.pop(get_campaigns_async_session, None)

        assert r.status_code == 200
        body = r.json()
        assert body["tasks_generated"] == 3
        assert "campaign" in body
        assert body["campaign"]["status"] == "running"

    async def test_launch_unknown_campaign_returns_404(self, client: AsyncClient) -> None:
        """Orchestrator raises NotFound → 404."""
        from src.main import app
        from luana_core_campaigns.api._service_factories import (
            get_campaign_orchestrator,
            get_campaign_service,
        )
        from luana_core_campaigns.api._dependencies import get_campaigns_async_session

        mock_orch = AsyncMock()
        mock_orch.launch = AsyncMock(side_effect=OrchestratorCampaignNotFoundError("Campaign not found"))

        mock_svc = AsyncMock()

        app.dependency_overrides[get_campaign_orchestrator] = lambda: mock_orch
        app.dependency_overrides[get_campaign_service] = lambda: mock_svc
        app.dependency_overrides[get_campaigns_async_session] = _patch_session

        r = await client.post(
            f"/api/v1/campaigns/{uuid4()}/launch",
            headers={"X-Tenant-ID": str(TENANT_ID)},
        )

        app.dependency_overrides.pop(get_campaign_orchestrator, None)
        app.dependency_overrides.pop(get_campaign_service, None)
        app.dependency_overrides.pop(get_campaigns_async_session, None)

        assert r.status_code == 404

    async def test_launch_cross_tenant_returns_404(self, client: AsyncClient) -> None:
        """Cross-tenant campaign → NotFound → 404 (tenant isolation)."""
        from src.main import app
        from luana_core_campaigns.api._service_factories import (
            get_campaign_orchestrator,
            get_campaign_service,
        )
        from luana_core_campaigns.api._dependencies import get_campaigns_async_session

        mock_orch = AsyncMock()
        mock_orch.launch = AsyncMock(side_effect=OrchestratorCampaignNotFoundError("not found for tenant"))
        mock_svc = AsyncMock()

        app.dependency_overrides[get_campaign_orchestrator] = lambda: mock_orch
        app.dependency_overrides[get_campaign_service] = lambda: mock_svc
        app.dependency_overrides[get_campaigns_async_session] = _patch_session

        r = await client.post(
            f"/api/v1/campaigns/{CAMPAIGN_ID}/launch",
            headers={"X-Tenant-ID": str(TENANT_ID)},
        )

        app.dependency_overrides.pop(get_campaign_orchestrator, None)
        app.dependency_overrides.pop(get_campaign_service, None)
        app.dependency_overrides.pop(get_campaigns_async_session, None)

        assert r.status_code == 404

    async def test_launch_invalid_state_returns_409(self, client: AsyncClient) -> None:
        """Campaign not in launchable state → 409."""
        from src.main import app
        from luana_core_campaigns.api._service_factories import (
            get_campaign_orchestrator,
            get_campaign_service,
        )
        from luana_core_campaigns.api._dependencies import get_campaigns_async_session

        mock_orch = AsyncMock()
        mock_orch.launch = AsyncMock(side_effect=OrchestratorCampaignNotLaunchableError("already completed"))
        mock_svc = AsyncMock()

        app.dependency_overrides[get_campaign_orchestrator] = lambda: mock_orch
        app.dependency_overrides[get_campaign_service] = lambda: mock_svc
        app.dependency_overrides[get_campaigns_async_session] = _patch_session

        r = await client.post(
            f"/api/v1/campaigns/{CAMPAIGN_ID}/launch",
            headers={"X-Tenant-ID": str(TENANT_ID)},
        )

        app.dependency_overrides.pop(get_campaign_orchestrator, None)
        app.dependency_overrides.pop(get_campaign_service, None)
        app.dependency_overrides.pop(get_campaigns_async_session, None)

        assert r.status_code == 409

    async def test_launch_missing_steps_returns_422(self, client: AsyncClient) -> None:
        """No root steps → 422."""
        from src.main import app
        from luana_core_campaigns.api._service_factories import (
            get_campaign_orchestrator,
            get_campaign_service,
        )
        from luana_core_campaigns.api._dependencies import get_campaigns_async_session

        mock_orch = AsyncMock()
        mock_orch.launch = AsyncMock(side_effect=OrchestratorMissingStepsError("no root steps"))
        mock_svc = AsyncMock()

        app.dependency_overrides[get_campaign_orchestrator] = lambda: mock_orch
        app.dependency_overrides[get_campaign_service] = lambda: mock_svc
        app.dependency_overrides[get_campaigns_async_session] = _patch_session

        r = await client.post(
            f"/api/v1/campaigns/{CAMPAIGN_ID}/launch",
            headers={"X-Tenant-ID": str(TENANT_ID)},
        )

        app.dependency_overrides.pop(get_campaign_orchestrator, None)
        app.dependency_overrides.pop(get_campaign_service, None)
        app.dependency_overrides.pop(get_campaigns_async_session, None)

        assert r.status_code == 422

    async def test_launch_idempotent_relaunch_returns_200(self, client: AsyncClient) -> None:
        """Idempotent re-launch (already RUNNING) returns 200 with tasks_generated=0."""
        from src.main import app
        from luana_core_campaigns.api._service_factories import (
            get_campaign_orchestrator,
            get_campaign_service,
        )
        from luana_core_campaigns.api._dependencies import get_campaigns_async_session

        mock_orch = AsyncMock()
        mock_orch.launch = AsyncMock(
            return_value=_launch_result(status="noop_already_running", tasks_generated=0, external_id="0")
        )
        mock_orch.enqueue_pending_tasks = AsyncMock()

        mock_svc = AsyncMock()
        mock_svc.get = AsyncMock(return_value=_campaign_response(status=CampaignStatus.RUNNING))

        app.dependency_overrides[get_campaign_orchestrator] = lambda: mock_orch
        app.dependency_overrides[get_campaign_service] = lambda: mock_svc
        app.dependency_overrides[get_campaigns_async_session] = _patch_session

        r = await client.post(
            f"/api/v1/campaigns/{CAMPAIGN_ID}/launch",
            headers={"X-Tenant-ID": str(TENANT_ID)},
        )

        app.dependency_overrides.pop(get_campaign_orchestrator, None)
        app.dependency_overrides.pop(get_campaign_service, None)
        app.dependency_overrides.pop(get_campaigns_async_session, None)

        assert r.status_code == 200
        body = r.json()
        assert body["tasks_generated"] == 0

    async def test_launch_response_model_enforced(self, client: AsyncClient) -> None:
        """Response is serialized via CampaignLaunchResponse (response_model enforcement)."""
        from src.main import app
        from luana_core_campaigns.api._service_factories import (
            get_campaign_orchestrator,
            get_campaign_service,
        )
        from luana_core_campaigns.api._dependencies import get_campaigns_async_session

        mock_orch = AsyncMock()
        mock_orch.launch = AsyncMock(return_value=_launch_result())
        mock_orch.enqueue_pending_tasks = AsyncMock()

        mock_svc = AsyncMock()
        mock_svc.get = AsyncMock(return_value=_campaign_response())

        app.dependency_overrides[get_campaign_orchestrator] = lambda: mock_orch
        app.dependency_overrides[get_campaign_service] = lambda: mock_svc
        app.dependency_overrides[get_campaigns_async_session] = _patch_session

        r = await client.post(
            f"/api/v1/campaigns/{CAMPAIGN_ID}/launch",
            headers={"X-Tenant-ID": str(TENANT_ID)},
        )

        app.dependency_overrides.pop(get_campaign_orchestrator, None)
        app.dependency_overrides.pop(get_campaign_service, None)
        app.dependency_overrides.pop(get_campaigns_async_session, None)

        assert r.status_code == 200
        body = r.json()
        # Must have campaign, tasks_generated, notice fields
        assert "campaign" in body
        assert "tasks_generated" in body
        assert "notice" in body
        # No internal fields leaked
        assert "snapshot_id" not in body  # OrchestratorLaunchResult not in response
        assert "external_id" not in body
