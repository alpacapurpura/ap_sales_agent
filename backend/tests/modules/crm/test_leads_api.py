"""Tests for CRM leads API endpoints.

CRM-15: GET /api/v1/crm/leads/search, GET /api/v1/crm/leads/{lead_id}.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
OTHER_TENANT_ID = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")
USER_ID = uuid.uuid4()
LEAD_ID = uuid.uuid4()

# ---------------------------------------------------------------------------
# Fake User dependency
# ---------------------------------------------------------------------------


class _FakeUser:
    """Minimal user substitute for dependency override."""

    id: uuid.UUID = USER_ID
    tenant_id: uuid.UUID = TENANT_ID
    email: str = "test@example.com"


class _FakeUserOtherTenant:
    """User from a different tenant for isolation tests."""

    id: uuid.UUID = USER_ID
    tenant_id: uuid.UUID = OTHER_TENANT_ID
    email: str = "other@example.com"


def _get_fake_user() -> _FakeUser:
    return _FakeUser()


def _get_fake_user_other_tenant() -> _FakeUserOtherTenant:
    return _FakeUserOtherTenant()


# ---------------------------------------------------------------------------
# App + client fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
async def client() -> AsyncClient:  # type: ignore[override]
    """AsyncClient pointed at the FastAPI app with auth overridden."""
    from src.main import app
    from luana_core_iam.api.dependencies import get_current_user

    app.dependency_overrides[get_current_user] = _get_fake_user

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.pop(get_current_user, None)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_session() -> MagicMock:
    """Return a MagicMock that satisfies Session interface."""
    return MagicMock()


def _make_lead_domain(
    lead_id: uuid.UUID | None = None,
    tenant_id: uuid.UUID = TENANT_ID,
    telegram_id: str | None = "tg-123",
) -> Any:
    """Build a real Lead domain object for response serialization."""
    from luana_core_crm.domain.lead import Lead, UserProfile

    return Lead(
        id=lead_id or LEAD_ID,
        tenant_id=tenant_id,
        telegram_id=telegram_id,
        profile_data=UserProfile(name="Test Lead"),
        fit_score=5,
        intent_score=3,
        temperature="warm",
        is_blacklisted=False,
        conversation_summary="Interested in course",
        key_objections_history=[],
        style_profile={},
        custom_system_instruction=None,
    )


# ---------------------------------------------------------------------------
# Tests: GET /api/v1/crm/leads/search  # noqa: ERA001
# ---------------------------------------------------------------------------


class TestSearchLeads:
    """GET /api/v1/crm/leads/search — placeholder returns empty list."""

    @pytest.mark.asyncio
    async def test_search_returns_empty_list(self, client: AsyncClient) -> None:
        """Search endpoint returns 200 with empty list (placeholder)."""
        response = await client.get("/api/v1/crm/leads/search", params={"q": "john"})

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_search_requires_min_length_2(self, client: AsyncClient) -> None:
        """Query param shorter than 2 chars → 422."""
        response = await client.get("/api/v1/crm/leads/search", params={"q": "a"})

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_search_with_long_query(self, client: AsyncClient) -> None:
        """Long query string still returns empty list."""
        response = await client.get(
            "/api/v1/crm/leads/search",
            params={"q": "john doe marketing course"},
        )

        assert response.status_code == 200
        assert response.json() == []


# ---------------------------------------------------------------------------
# Tests: GET /api/v1/crm/leads/{lead_id}  # noqa: ERA001
# ---------------------------------------------------------------------------


class TestGetLead:
    """GET /api/v1/crm/leads/{lead_id} — retrieve specific lead."""

    @pytest.mark.asyncio
    async def test_get_existing_lead(self, client: AsyncClient) -> None:
        """Valid lead_id → 200 + lead data."""
        from luana_core_platform.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()
        mock_lead = _make_lead_domain()

        with (
            patch("luana_core_platform.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "luana_core_crm.application.services.lead_service.LeadService.get_lead",
                return_value=mock_lead,
            ),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.get(f"/api/v1/crm/leads/{LEAD_ID}")

                assert response.status_code == 200
            finally:
                app.dependency_overrides.pop(get_db, None)

    @pytest.mark.asyncio
    async def test_get_lead_invalid_uuid(self, client: AsyncClient) -> None:
        """Invalid UUID format → 400."""
        response = await client.get("/api/v1/crm/leads/not-a-uuid")

        assert response.status_code == 400
        assert "Invalid UUID format" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_lead_not_found(self, client: AsyncClient) -> None:
        """Lead does not exist → 404."""
        from luana_core_platform.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()

        with (
            patch("luana_core_platform.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "luana_core_crm.application.services.lead_service.LeadService.get_lead",
                return_value=None,
            ),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.get(f"/api/v1/crm/leads/{LEAD_ID}")

                assert response.status_code == 404
                assert "Lead not found" in response.json()["detail"]
            finally:
                app.dependency_overrides.pop(get_db, None)

    @pytest.mark.asyncio
    async def test_get_lead_tenant_isolation(self, client: AsyncClient) -> None:
        """Lead belongs to different tenant → 404."""
        from luana_core_platform.core.database import get_db
        from src.main import app
        from luana_core_iam.api.dependencies import get_current_user

        mock_session = _make_mock_session()
        mock_lead = _make_lead_domain(tenant_id=OTHER_TENANT_ID)

        with (
            patch("luana_core_platform.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "luana_core_crm.application.services.lead_service.LeadService.get_lead",
                return_value=mock_lead,
            ),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session
            app.dependency_overrides[get_current_user] = _get_fake_user

            try:
                response = await client.get(f"/api/v1/crm/leads/{LEAD_ID}")

                assert response.status_code == 404
            finally:
                app.dependency_overrides.pop(get_db, None)
                app.dependency_overrides.pop(get_current_user, None)
