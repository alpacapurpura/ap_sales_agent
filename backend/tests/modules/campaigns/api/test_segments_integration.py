"""Integration tests: segments_router ↔ SegmentService contract (no AsyncMock service).

Verifies that router calls service with correct kwargs and builds DTO correctly from
the tuple returned by resolve() / estimate_size(). This test catches the class of bug
found in F-2 (PR-4 REVIEW) where router called svc.resolve(request=body, ...) — a kwarg
that the service does not accept.

All repos and outbox_service are still mocked (no Postgres required). Only the
SegmentService itself is REAL — so the router ↔ service kwarg contract is exercised.
"""

from __future__ import annotations

import datetime as dt
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.modules.campaigns.application.services.cache import SimpleTTLCache
from src.modules.campaigns.application.services.segment_service import (
    SegmentNotFoundError,
    SegmentService,
)
from src.modules.campaigns.domain.enums import SegmentType
from src.modules.campaigns.domain.segment import Segment
from src.modules.campaigns.domain.segment_filter import PredefinedSegmentFilter
from src.shared.domain.datetime_utils import utc_now

pytestmark = pytest.mark.asyncio

TENANT_ID = uuid4()
USER_ID = uuid4()
SEGMENT_ID = uuid4()
NOW = dt.datetime.now(tz=dt.timezone.utc)


def _patch_session() -> AsyncMock:
    """Return AsyncMock that satisfies AsyncSession interface minimally."""
    return AsyncMock()


# ── Fake User ──────────────────────────────────────────────────────────────────


class _FakeUser:
    """Minimal user substitute for dependency override."""

    id: UUID = USER_ID
    tenant_id: UUID = TENANT_ID
    email: str = "integration@example.com"


def _get_fake_user() -> _FakeUser:
    return _FakeUser()


# ── Helper: build a real SegmentService with mocked repos ─────────────────────


def _build_real_segment_service(
    *,
    repo_mock: AsyncMock,
    lead_query_port_mock: AsyncMock,
) -> SegmentService:
    """Return a real SegmentService wired with minimal mocks.

    Snapshot repo and outbox are always mocked (not under test here).
    SegmentFilterEvaluator is REAL (pure Python — no deps).
    """
    from src.modules.campaigns.application.segment_filter_evaluator import (
        SegmentFilterEvaluator,
    )

    return SegmentService(
        repo=repo_mock,
        snapshot_repo=AsyncMock(),
        lead_query_port=lead_query_port_mock,
        filter_evaluator=SegmentFilterEvaluator(),
        outbox_service=AsyncMock(),
        cache=SimpleTTLCache(),
    )


def _make_segment_domain(segment_id: UUID | None = None) -> Segment:
    """Build a minimal Segment domain object."""
    now = utc_now()
    return Segment(
        id=segment_id or SEGMENT_ID,
        tenant_id=TENANT_ID,
        name="Leads fríos",
        description=None,
        segment_type=SegmentType.DYNAMIC,
        filter_dsl=PredefinedSegmentFilter(
            temperature=["COLD"],
        ),
        created_at=now,
        updated_at=now,
    )


# ── App + client fixture ──────────────────────────────────────────────────────


@pytest.fixture()
async def client() -> AsyncClient:  # type: ignore[override]
    """AsyncClient with auth overridden but service NOT mocked."""
    from src.main import app
    from src.modules.iam.api.dependencies import get_current_user

    app.dependency_overrides[get_current_user] = _get_fake_user

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.pop(get_current_user, None)


# ── Integration tests ─────────────────────────────────────────────────────────


class TestResolveContractRouterToService:
    """Verify resolve_segment router → SegmentService.resolve() kwarg contract.

    F-2 regression guard: before fix, router passed request=body kwarg which
    does not exist on SegmentService.resolve(). This test uses the REAL service
    (not AsyncMock) so TypeError would surface immediately.
    """

    @pytest.mark.asyncio
    async def test_resolve_router_builds_dto_from_service_tuple(self, client: AsyncClient) -> None:
        """Router calls svc.resolve() with correct kwargs and builds SegmentResolveResponse."""
        from src.modules.campaigns.api._service_factories import get_segment_service
        from src.modules.campaigns.api._dependencies import get_campaigns_async_session
        from src.main import app

        lead_ids_returned = [uuid4(), uuid4(), uuid4()]
        repo_mock = AsyncMock()
        repo_mock.get_by_id.return_value = _make_segment_domain()
        lead_port_mock = AsyncMock()
        lead_port_mock.list_lead_ids_matching.return_value = (lead_ids_returned, 3)

        real_svc = _build_real_segment_service(
            repo_mock=repo_mock,
            lead_query_port_mock=lead_port_mock,
        )

        app.dependency_overrides[get_segment_service] = lambda: real_svc
        app.dependency_overrides[get_campaigns_async_session] = _patch_session

        r = await client.post(
            f"/api/v1/segments/{SEGMENT_ID}/resolve",
            json={"limit": 1000},
            headers={"X-Tenant-ID": str(TENANT_ID)},
        )

        app.dependency_overrides.pop(get_segment_service, None)
        app.dependency_overrides.pop(get_campaigns_async_session, None)

        # If F-2 bug is present → 500 (TypeError unexpected kwarg).
        # If fixed → 200 + valid SegmentResolveResponse shape.
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        body = r.json()
        assert body["lead_count"] == 3
        assert len(body["lead_ids"]) == 3
        assert body["segment_id"] == str(SEGMENT_ID)
        assert "truncated" in body
        assert body["truncated"] is False

    @pytest.mark.asyncio
    async def test_resolve_router_not_found_returns_404(self, client: AsyncClient) -> None:
        """Not found segment → real service raises SegmentNotFoundError → router maps to 404."""
        from src.modules.campaigns.api._service_factories import get_segment_service
        from src.modules.campaigns.api._dependencies import get_campaigns_async_session
        from src.main import app

        repo_mock = AsyncMock()
        repo_mock.get_by_id.return_value = None  # not found
        lead_port_mock = AsyncMock()

        real_svc = _build_real_segment_service(
            repo_mock=repo_mock,
            lead_query_port_mock=lead_port_mock,
        )

        app.dependency_overrides[get_segment_service] = lambda: real_svc
        app.dependency_overrides[get_campaigns_async_session] = _patch_session

        missing_id = uuid4()
        r = await client.post(
            f"/api/v1/segments/{missing_id}/resolve",
            json={"limit": 1000},
            headers={"X-Tenant-ID": str(TENANT_ID)},
        )

        app.dependency_overrides.pop(get_segment_service, None)
        app.dependency_overrides.pop(get_campaigns_async_session, None)

        assert r.status_code == 404


class TestEstimateSizeContractRouterToService:
    """Verify estimate_segment_size router → SegmentService.estimate_size() kwarg contract."""

    @pytest.mark.asyncio
    async def test_estimate_size_router_builds_dto_from_service_tuple(self, client: AsyncClient) -> None:
        """Router calls svc.estimate_size() correctly and builds SegmentEstimateSizeResponse."""
        from src.modules.campaigns.api._service_factories import get_segment_service
        from src.modules.campaigns.api._dependencies import get_campaigns_async_session
        from src.main import app

        repo_mock = AsyncMock()
        repo_mock.get_by_id.return_value = _make_segment_domain()
        repo_mock.update.return_value = None  # best-effort persist

        lead_port_mock = AsyncMock()
        lead_port_mock.count_leads_matching.return_value = 42

        real_svc = _build_real_segment_service(
            repo_mock=repo_mock,
            lead_query_port_mock=lead_port_mock,
        )

        app.dependency_overrides[get_segment_service] = lambda: real_svc
        app.dependency_overrides[get_campaigns_async_session] = _patch_session

        r = await client.get(
            f"/api/v1/segments/{SEGMENT_ID}/estimate-size",
            headers={"X-Tenant-ID": str(TENANT_ID)},
        )

        app.dependency_overrides.pop(get_segment_service, None)
        app.dependency_overrides.pop(get_campaigns_async_session, None)

        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
        body = r.json()
        assert body["estimated_size"] == 42
        assert body["segment_id"] == str(SEGMENT_ID)
        assert "cached_at" in body
        assert body["cache_hit"] is False  # first call → no cache
