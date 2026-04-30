"""API tests for campaigns, segments, and templates endpoints.

Uses AsyncMock stubs for service dependencies.
Tests: response_model enforcement, status codes, error → HTTP mapping, pagination.
"""

from __future__ import annotations

import datetime as dt
from typing import Any
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.modules.campaigns.application.dtos.campaign_dtos import (
    CampaignLaunchResponse,
    CampaignResponse,
)
from src.modules.campaigns.application.dtos.campaign_step_dtos import CampaignStepResponse
from src.modules.campaigns.application.dtos.campaign_template_dtos import (
    CampaignTemplateResponse,
)
from src.modules.campaigns.application.dtos.pagination import PaginatedResponse
from src.modules.campaigns.application.dtos.segment_dtos import (
    SegmentEstimateSizeResponse,
    SegmentResolveResponse,
    SegmentResponse,
    SegmentSnapshotResponse,
)
from src.modules.campaigns.application.services.campaign_service import (
    CampaignDuplicateNameError,
    CampaignNotFoundError,
    CampaignPlanLimitExceededError,
)
from src.modules.campaigns.application.services.segment_service import SegmentNotFoundError
from src.modules.campaigns.application.services.campaign_template_service import (
    CampaignTemplateNotFoundError,
)
from src.modules.campaigns.domain.enums import (
    CampaignStatus,
    CampaignType,
    SegmentType,
    StepType,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

TENANT_ID = uuid4()
USER_ID = uuid4()
CAMPAIGN_ID = uuid4()
SEGMENT_ID = uuid4()
TEMPLATE_ID = uuid4()
STEP_ID = uuid4()
NOW = dt.datetime.now(tz=dt.timezone.utc)


def _campaign_response(**overrides: Any) -> CampaignResponse:
    """Build a minimal CampaignResponse for mocking."""
    defaults: dict[str, Any] = {
        "id": CAMPAIGN_ID,
        "tenant_id": TENANT_ID,
        "name": "Test Campaign",
        "description": None,
        "campaign_type": CampaignType.EMAIL_BROADCAST,
        "status": CampaignStatus.DRAFT,
        "segment_id": None,
        "segment_snapshot_id": None,
        "channel_priority": [],
        "offer_id": None,
        "brand_summary_id": None,
        "config": {},
        "scheduled_at": None,
        "launched_at": None,
        "completed_at": None,
        "created_by_user_id": USER_ID,
        "created_by_source": "api",
        "created_at": NOW,
        "updated_at": NOW,
    }
    defaults.update(overrides)
    return CampaignResponse(**defaults)


def _segment_response(**overrides: Any) -> SegmentResponse:
    """Build a minimal SegmentResponse for mocking."""
    from src.modules.campaigns.domain.segment_filter import PredefinedSegmentFilter

    defaults: dict[str, Any] = {
        "id": SEGMENT_ID,
        "tenant_id": TENANT_ID,
        "name": "Test Segment",
        "description": None,
        "segment_type": SegmentType.DYNAMIC,
        "filter_dsl": PredefinedSegmentFilter(),
        "estimated_size": None,
        "last_calculated_at": None,
        "created_at": NOW,
        "updated_at": NOW,
    }
    defaults.update(overrides)
    return SegmentResponse(**defaults)


def _template_response(**overrides: Any) -> CampaignTemplateResponse:
    """Build a minimal CampaignTemplateResponse for mocking."""
    defaults: dict[str, Any] = {
        "id": TEMPLATE_ID,
        "tenant_id": None,  # global
        "slug": "welcome",
        "name": "Welcome",
        "description": "Welcome sequence",
        "campaign_type": CampaignType.EMAIL_DRIP,
        "template_body": {"steps": []},
        "recommended_segment_slugs": [],
        "tags": ["onboarding"],
        "version": 1,
        "created_at": NOW,
        "updated_at": NOW,
    }
    defaults.update(overrides)
    return CampaignTemplateResponse(**defaults)


def _step_response(**overrides: Any) -> CampaignStepResponse:
    """Build a minimal CampaignStepResponse."""
    defaults: dict[str, Any] = {
        "id": STEP_ID,
        "tenant_id": TENANT_ID,
        "campaign_id": CAMPAIGN_ID,
        "step_type": StepType.SEND_MESSAGE,
        "step_index": 0,
        "label": None,
        "next_step_ids": [],
        "step_config": {},
        "created_at": NOW,
        "updated_at": NOW,
    }
    defaults.update(overrides)
    return CampaignStepResponse(**defaults)


# ── Fake User dependency ──────────────────────────────────────────────────────


class _FakeUser:
    """Minimal user substitute for dependency override."""

    id: UUID = USER_ID
    tenant_id: UUID = TENANT_ID
    email: str = "test@example.com"


def _get_fake_user() -> _FakeUser:
    return _FakeUser()


# ── App + client fixture ──────────────────────────────────────────────────────


@pytest.fixture()
async def client() -> AsyncClient:  # type: ignore[override]
    """AsyncClient pointed at the FastAPI app with auth overridden."""
    from src.main import app
    from src.modules.iam.api.dependencies import get_current_user

    app.dependency_overrides[get_current_user] = _get_fake_user

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.pop(get_current_user, None)


# ── Helper: make fake session for DI override ─────────────────────────────────


def _patch_session() -> Any:
    """Return AsyncMock that satisfies AsyncSession interface minimally."""
    return AsyncMock()


# ── Campaign tests ────────────────────────────────────────────────────────────


class TestCampaignCreate:
    """POST /api/v1/campaigns/."""

    @pytest.mark.asyncio
    async def test_create_campaign_returns_201(self, client: AsyncClient) -> None:
        """Happy path: valid body → 201 + CampaignResponse shape."""
        from src.modules.campaigns.api._service_factories import get_campaign_service
        from src.modules.campaigns.api._dependencies import get_campaigns_async_session
        from src.main import app

        resp = _campaign_response()
        mock_svc = AsyncMock()
        mock_svc.create.return_value = resp
        app.dependency_overrides[get_campaign_service] = lambda: mock_svc
        app.dependency_overrides[get_campaigns_async_session] = _patch_session

        r = await client.post(
            "/api/v1/campaigns/",
            json={
                "name": "Lanzamiento Q3",
                "campaign_type": "email_broadcast",
            },
            headers={"X-Tenant-ID": str(TENANT_ID)},
        )
        app.dependency_overrides.pop(get_campaign_service, None)
        app.dependency_overrides.pop(get_campaigns_async_session, None)

        assert r.status_code == 201
        body = r.json()
        assert body["name"] == "Test Campaign"
        assert body["status"] == "draft"

    @pytest.mark.asyncio
    async def test_create_campaign_duplicate_name_returns_409(self, client: AsyncClient) -> None:
        """Duplicate name → 409."""
        from src.modules.campaigns.api._service_factories import get_campaign_service
        from src.modules.campaigns.api._dependencies import get_campaigns_async_session
        from src.main import app

        mock_svc = AsyncMock()
        mock_svc.create.side_effect = CampaignDuplicateNameError("Ya existe")
        app.dependency_overrides[get_campaign_service] = lambda: mock_svc
        app.dependency_overrides[get_campaigns_async_session] = _patch_session

        r = await client.post(
            "/api/v1/campaigns/",
            json={"name": "Dup", "campaign_type": "email_broadcast"},
            headers={"X-Tenant-ID": str(TENANT_ID)},
        )
        app.dependency_overrides.pop(get_campaign_service, None)
        app.dependency_overrides.pop(get_campaigns_async_session, None)

        assert r.status_code == 409

    @pytest.mark.asyncio
    async def test_create_campaign_plan_limit_returns_402(self, client: AsyncClient) -> None:
        """Plan limit exceeded → 402."""
        from src.modules.campaigns.api._service_factories import get_campaign_service
        from src.modules.campaigns.api._dependencies import get_campaigns_async_session
        from src.main import app

        mock_svc = AsyncMock()
        mock_svc.create.side_effect = CampaignPlanLimitExceededError("limit")
        app.dependency_overrides[get_campaign_service] = lambda: mock_svc
        app.dependency_overrides[get_campaigns_async_session] = _patch_session

        r = await client.post(
            "/api/v1/campaigns/",
            json={"name": "X", "campaign_type": "email_broadcast"},
            headers={"X-Tenant-ID": str(TENANT_ID)},
        )
        app.dependency_overrides.pop(get_campaign_service, None)
        app.dependency_overrides.pop(get_campaigns_async_session, None)

        assert r.status_code == 402


class TestCampaignList:
    """GET /api/v1/campaigns/."""

    @pytest.mark.asyncio
    async def test_list_returns_paginated(self, client: AsyncClient) -> None:
        """List endpoint returns PaginatedResponse shape."""
        from src.modules.campaigns.api._service_factories import get_campaign_service
        from src.modules.campaigns.api._dependencies import get_campaigns_async_session
        from src.main import app

        resp = PaginatedResponse[CampaignResponse](
            items=[_campaign_response()],
            total_count=1,
            limit=20,
            offset=0,
            has_more=False,
        )
        mock_svc = AsyncMock()
        mock_svc.list.return_value = resp
        app.dependency_overrides[get_campaign_service] = lambda: mock_svc
        app.dependency_overrides[get_campaigns_async_session] = _patch_session

        r = await client.get(
            "/api/v1/campaigns/",
            headers={"X-Tenant-ID": str(TENANT_ID)},
        )
        app.dependency_overrides.pop(get_campaign_service, None)
        app.dependency_overrides.pop(get_campaigns_async_session, None)

        assert r.status_code == 200
        body = r.json()
        assert "items" in body
        assert body["total_count"] == 1

    @pytest.mark.asyncio
    async def test_list_accepts_limit_offset(self, client: AsyncClient) -> None:
        """list endpoint accepts limit/offset query params."""
        from src.modules.campaigns.api._service_factories import get_campaign_service
        from src.modules.campaigns.api._dependencies import get_campaigns_async_session
        from src.main import app

        resp = PaginatedResponse[CampaignResponse](items=[], total_count=0, limit=5, offset=10, has_more=False)
        mock_svc = AsyncMock()
        mock_svc.list.return_value = resp
        app.dependency_overrides[get_campaign_service] = lambda: mock_svc
        app.dependency_overrides[get_campaigns_async_session] = _patch_session

        r = await client.get(
            "/api/v1/campaigns/?limit=5&offset=10",
            headers={"X-Tenant-ID": str(TENANT_ID)},
        )
        app.dependency_overrides.pop(get_campaign_service, None)
        app.dependency_overrides.pop(get_campaigns_async_session, None)

        assert r.status_code == 200


class TestCampaignGet:
    """GET /api/v1/campaigns/{id}."""

    @pytest.mark.asyncio
    async def test_get_existing_returns_200(self, client: AsyncClient) -> None:
        """Get by ID returns 200 + campaign body."""
        from src.modules.campaigns.api._service_factories import get_campaign_service
        from src.modules.campaigns.api._dependencies import get_campaigns_async_session
        from src.main import app

        mock_svc = AsyncMock()
        mock_svc.get.return_value = _campaign_response()
        app.dependency_overrides[get_campaign_service] = lambda: mock_svc
        app.dependency_overrides[get_campaigns_async_session] = _patch_session

        r = await client.get(
            f"/api/v1/campaigns/{CAMPAIGN_ID}",
            headers={"X-Tenant-ID": str(TENANT_ID)},
        )
        app.dependency_overrides.pop(get_campaign_service, None)
        app.dependency_overrides.pop(get_campaigns_async_session, None)

        assert r.status_code == 200
        assert r.json()["id"] == str(CAMPAIGN_ID)

    @pytest.mark.asyncio
    async def test_get_missing_returns_404(self, client: AsyncClient) -> None:
        """Not-found → 404."""
        from src.modules.campaigns.api._service_factories import get_campaign_service
        from src.modules.campaigns.api._dependencies import get_campaigns_async_session
        from src.main import app

        mock_svc = AsyncMock()
        mock_svc.get.side_effect = CampaignNotFoundError("not found")
        app.dependency_overrides[get_campaign_service] = lambda: mock_svc
        app.dependency_overrides[get_campaigns_async_session] = _patch_session

        r = await client.get(
            f"/api/v1/campaigns/{uuid4()}",
            headers={"X-Tenant-ID": str(TENANT_ID)},
        )
        app.dependency_overrides.pop(get_campaign_service, None)
        app.dependency_overrides.pop(get_campaigns_async_session, None)

        assert r.status_code == 404


class TestCampaignFSM:
    """FSM transition endpoints."""

    @pytest.mark.asyncio
    async def test_launch_returns_stub_notice(self, client: AsyncClient) -> None:
        """Launch endpoint returns CampaignLaunchResponse with notice field."""
        from src.modules.campaigns.api._service_factories import get_campaign_service
        from src.modules.campaigns.api._dependencies import get_campaigns_async_session
        from src.main import app

        camp = _campaign_response(status=CampaignStatus.RUNNING)
        mock_svc = AsyncMock()
        mock_svc.launch.return_value = camp
        app.dependency_overrides[get_campaign_service] = lambda: mock_svc
        app.dependency_overrides[get_campaigns_async_session] = _patch_session

        r = await client.post(
            f"/api/v1/campaigns/{CAMPAIGN_ID}/launch",
            headers={"X-Tenant-ID": str(TENANT_ID)},
        )
        app.dependency_overrides.pop(get_campaign_service, None)
        app.dependency_overrides.pop(get_campaigns_async_session, None)

        assert r.status_code == 200
        body = r.json()
        assert "notice" in body
        assert "STUB" in body["notice"]

    @pytest.mark.asyncio
    async def test_cancel_returns_200(self, client: AsyncClient) -> None:
        """Cancel transition returns 200 + campaign."""
        from src.modules.campaigns.api._service_factories import get_campaign_service
        from src.modules.campaigns.api._dependencies import get_campaigns_async_session
        from src.main import app

        mock_svc = AsyncMock()
        mock_svc.cancel.return_value = _campaign_response(status=CampaignStatus.CANCELED)
        app.dependency_overrides[get_campaign_service] = lambda: mock_svc
        app.dependency_overrides[get_campaigns_async_session] = _patch_session

        r = await client.post(
            f"/api/v1/campaigns/{CAMPAIGN_ID}/cancel",
            json={"reason": "Test cancel"},
            headers={"X-Tenant-ID": str(TENANT_ID)},
        )
        app.dependency_overrides.pop(get_campaign_service, None)
        app.dependency_overrides.pop(get_campaigns_async_session, None)

        assert r.status_code == 200
        assert r.json()["status"] == "canceled"


# ── Segment tests ─────────────────────────────────────────────────────────────


class TestSegmentCRUD:
    """Segment CRUD endpoints."""

    @pytest.mark.asyncio
    async def test_list_segments_returns_paginated(self, client: AsyncClient) -> None:
        """List returns paginated segments."""
        from src.modules.campaigns.api._service_factories import get_segment_service
        from src.modules.campaigns.api._dependencies import get_campaigns_async_session
        from src.main import app

        resp = PaginatedResponse[SegmentResponse](
            items=[_segment_response()],
            total_count=1,
            limit=20,
            offset=0,
            has_more=False,
        )
        mock_svc = AsyncMock()
        mock_svc.list_segments.return_value = resp
        app.dependency_overrides[get_segment_service] = lambda: mock_svc
        app.dependency_overrides[get_campaigns_async_session] = _patch_session

        r = await client.get(
            "/api/v1/segments/",
            headers={"X-Tenant-ID": str(TENANT_ID)},
        )
        app.dependency_overrides.pop(get_segment_service, None)
        app.dependency_overrides.pop(get_campaigns_async_session, None)

        assert r.status_code == 200
        assert r.json()["total_count"] == 1

    @pytest.mark.asyncio
    async def test_create_segment_returns_201(self, client: AsyncClient) -> None:
        """Create segment → 201."""
        from src.modules.campaigns.api._service_factories import get_segment_service
        from src.modules.campaigns.api._dependencies import get_campaigns_async_session
        from src.main import app

        mock_svc = AsyncMock()
        mock_svc.create.return_value = _segment_response()
        app.dependency_overrides[get_segment_service] = lambda: mock_svc
        app.dependency_overrides[get_campaigns_async_session] = _patch_session

        r = await client.post(
            "/api/v1/segments/",
            json={
                "name": "Leads Frios",
                "filter_dsl": {
                    "combinator": "all",
                },
            },
            headers={"X-Tenant-ID": str(TENANT_ID)},
        )
        app.dependency_overrides.pop(get_segment_service, None)
        app.dependency_overrides.pop(get_campaigns_async_session, None)

        assert r.status_code == 201

    @pytest.mark.asyncio
    async def test_get_segment_not_found_returns_404(self, client: AsyncClient) -> None:
        """Not found → 404."""
        from src.modules.campaigns.api._service_factories import get_segment_service
        from src.modules.campaigns.api._dependencies import get_campaigns_async_session
        from src.main import app

        mock_svc = AsyncMock()
        mock_svc.get.side_effect = SegmentNotFoundError("not found")
        app.dependency_overrides[get_segment_service] = lambda: mock_svc
        app.dependency_overrides[get_campaigns_async_session] = _patch_session

        r = await client.get(
            f"/api/v1/segments/{uuid4()}",
            headers={"X-Tenant-ID": str(TENANT_ID)},
        )
        app.dependency_overrides.pop(get_segment_service, None)
        app.dependency_overrides.pop(get_campaigns_async_session, None)

        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_resolve_segment_returns_uuid_list(self, client: AsyncClient) -> None:
        """Resolve → SegmentResolveResponse with lead_ids (no PII)."""
        from src.modules.campaigns.api._service_factories import get_segment_service
        from src.modules.campaigns.api._dependencies import get_campaigns_async_session
        from src.main import app

        lead_ids = [uuid4(), uuid4()]
        # Service returns tuple (lead_ids, lead_count, truncated) — router builds DTO.
        mock_svc = AsyncMock()
        mock_svc.resolve.return_value = (lead_ids, 2, False)
        app.dependency_overrides[get_segment_service] = lambda: mock_svc
        app.dependency_overrides[get_campaigns_async_session] = _patch_session

        r = await client.post(
            f"/api/v1/segments/{SEGMENT_ID}/resolve",
            json={"limit": 1000},
            headers={"X-Tenant-ID": str(TENANT_ID)},
        )
        app.dependency_overrides.pop(get_segment_service, None)
        app.dependency_overrides.pop(get_campaigns_async_session, None)

        assert r.status_code == 200
        body = r.json()
        assert body["lead_count"] == 2
        assert len(body["lead_ids"]) == 2

    @pytest.mark.asyncio
    async def test_estimate_size_returns_200(self, client: AsyncClient) -> None:
        """estimate-size endpoint returns size response."""
        from src.modules.campaigns.api._service_factories import get_segment_service
        from src.modules.campaigns.api._dependencies import get_campaigns_async_session
        from src.main import app

        # Service returns tuple (estimated_size, cached_at, cache_hit) — router builds DTO.
        mock_svc = AsyncMock()
        mock_svc.estimate_size.return_value = (150, NOW, True)
        app.dependency_overrides[get_segment_service] = lambda: mock_svc
        app.dependency_overrides[get_campaigns_async_session] = _patch_session

        r = await client.get(
            f"/api/v1/segments/{SEGMENT_ID}/estimate-size",
            headers={"X-Tenant-ID": str(TENANT_ID)},
        )
        app.dependency_overrides.pop(get_segment_service, None)
        app.dependency_overrides.pop(get_campaigns_async_session, None)

        assert r.status_code == 200
        assert r.json()["estimated_size"] == 150


# ── Template tests ────────────────────────────────────────────────────────────


class TestTemplateCatalog:
    """Template endpoints."""

    @pytest.mark.asyncio
    async def test_list_templates_returns_list(self, client: AsyncClient) -> None:
        """Templates list returns list of CampaignTemplateResponse."""
        from src.modules.campaigns.api._service_factories import get_template_service
        from src.modules.campaigns.api._dependencies import get_campaigns_async_session
        from src.main import app

        mock_svc = AsyncMock()
        mock_svc.list_available.return_value = [_template_response()]
        app.dependency_overrides[get_template_service] = lambda: mock_svc
        app.dependency_overrides[get_campaigns_async_session] = _patch_session

        r = await client.get(
            "/api/v1/templates/",
            headers={"X-Tenant-ID": str(TENANT_ID)},
        )
        app.dependency_overrides.pop(get_template_service, None)
        app.dependency_overrides.pop(get_campaigns_async_session, None)

        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) == 1

    @pytest.mark.asyncio
    async def test_get_template_not_found_returns_404(self, client: AsyncClient) -> None:
        """Not found → 404."""
        from src.modules.campaigns.api._service_factories import get_template_service
        from src.modules.campaigns.api._dependencies import get_campaigns_async_session
        from src.main import app

        mock_svc = AsyncMock()
        mock_svc.get.side_effect = CampaignTemplateNotFoundError("not found")
        app.dependency_overrides[get_template_service] = lambda: mock_svc
        app.dependency_overrides[get_campaigns_async_session] = _patch_session

        r = await client.get(
            f"/api/v1/templates/{uuid4()}",
            headers={"X-Tenant-ID": str(TENANT_ID)},
        )
        app.dependency_overrides.pop(get_template_service, None)
        app.dependency_overrides.pop(get_campaigns_async_session, None)

        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_clone_template_returns_201(self, client: AsyncClient) -> None:
        """Clone → 201 + CampaignResponse."""
        from src.modules.campaigns.api._service_factories import get_template_service
        from src.modules.campaigns.api._dependencies import get_campaigns_async_session
        from src.main import app

        mock_svc = AsyncMock()
        mock_svc.clone_to_campaign.return_value = _campaign_response()
        app.dependency_overrides[get_template_service] = lambda: mock_svc
        app.dependency_overrides[get_campaigns_async_session] = _patch_session

        r = await client.post(
            f"/api/v1/templates/{TEMPLATE_ID}/clone",
            json={
                "name": "Mi campaña desde template",
                "segment_id": str(SEGMENT_ID),
            },
            headers={"X-Tenant-ID": str(TENANT_ID)},
        )
        app.dependency_overrides.pop(get_template_service, None)
        app.dependency_overrides.pop(get_campaigns_async_session, None)

        assert r.status_code == 201
        assert r.json()["name"] == "Test Campaign"
