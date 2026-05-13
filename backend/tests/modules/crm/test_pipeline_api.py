"""Tests for CRM pipeline API endpoints.

CRM-15: GET /api/v1/crm/pipeline/pipeline, PUT /api/v1/crm/pipeline/{profile_id}/stage,
GET /api/v1/crm/pipeline/{profile_id}/transitions.
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
USER_ID = uuid.uuid4()
PROFILE_ID = uuid.uuid4()
LEAD_ID = uuid.uuid4()

# ---------------------------------------------------------------------------
# Fake User dependency
# ---------------------------------------------------------------------------


class _FakeUser:
    """Minimal user substitute for dependency override."""

    id: uuid.UUID = USER_ID
    tenant_id: uuid.UUID = TENANT_ID
    email: str = "test@example.com"


def _get_fake_user() -> _FakeUser:
    return _FakeUser()


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


def _make_lead_orm(**overrides: Any) -> MagicMock:
    """Build a mock LeadModel for pipeline view."""
    lead = MagicMock()
    lead.id = LEAD_ID
    lead.tenant_id = TENANT_ID
    lead.intent_score = 75
    lead.temperature = "warm"
    lead.last_interaction_date = datetime.now(timezone.utc)
    lead.customer = None
    lead.profile_data = {"name": "Test Lead"}
    lead.is_blacklisted = False
    for key, value in overrides.items():
        setattr(lead, key, value)
    return lead


def _make_profile_orm(**overrides: Any) -> MagicMock:
    """Build a mock CustomerProfileModel."""
    profile = MagicMock()
    profile.id = PROFILE_ID
    profile.tenant_id = TENANT_ID
    profile.lifecycle_stage = MagicMock()
    profile.lifecycle_stage.value = "lead"
    for key, value in overrides.items():
        setattr(profile, key, value)
    return profile


def _make_transition(**overrides: Any) -> MagicMock:
    """Build a mock LifecycleTransitionModel."""
    t = MagicMock()
    t.id = uuid.uuid4()
    t.from_stage = MagicMock()
    t.from_stage.value = "subscriber"
    t.to_stage = MagicMock()
    t.to_stage.value = "lead"
    t.reason = "Score threshold"
    t.triggered_by = "scoring_rule"
    t.score_at_transition = 15.0
    t.transition_metadata = {"score": 15.0}
    t.occurred_at = datetime.now(timezone.utc)
    for key, value in overrides.items():
        setattr(t, key, value)
    return t


# ---------------------------------------------------------------------------
# Tests: GET /api/v1/crm/pipeline/pipeline  # noqa: ERA001
# ---------------------------------------------------------------------------


class TestGetPipeline:
    """GET /api/v1/crm/pipeline/pipeline — high-intent leads view."""

    @pytest.mark.asyncio
    async def test_pipeline_returns_items(self, client: AsyncClient) -> None:
        """Happy path: returns pipeline items."""
        from luana_core_platform.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()
        mock_lead = _make_lead_orm()
        mock_scalar_result = MagicMock()
        mock_scalar_result.all.return_value = [mock_lead]
        mock_session.execute.return_value.scalars.return_value = mock_scalar_result

        with (
            patch("luana_core_platform.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.get("/api/v1/crm/pipeline/pipeline")

                assert response.status_code == 200
                body = response.json()
                assert len(body) == 1
                assert body[0]["intent_score"] == 75
            finally:
                app.dependency_overrides.pop(get_db, None)

    @pytest.mark.asyncio
    async def test_pipeline_empty_returns_empty_list(self, client: AsyncClient) -> None:
        """No leads → empty list."""
        from luana_core_platform.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()
        mock_scalar_result = MagicMock()
        mock_scalar_result.all.return_value = []
        mock_session.execute.return_value.scalars.return_value = mock_scalar_result

        with (
            patch("luana_core_platform.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.get("/api/v1/crm/pipeline/pipeline")

                assert response.status_code == 200
                assert response.json() == []
            finally:
                app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Tests: PUT /api/v1/crm/pipeline/{profile_id}/stage  # noqa: ERA001
# ---------------------------------------------------------------------------


class TestOverrideStage:
    """PUT /api/v1/crm/pipeline/{profile_id}/stage — manual stage override."""

    @pytest.mark.asyncio
    async def test_override_success(self, client: AsyncClient) -> None:
        """Valid request → 200 + override details."""
        from luana_core_platform.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()
        mock_profile = _make_profile_orm()
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = mock_profile
        mock_session.execute.return_value.scalars.return_value = mock_scalars

        with (
            patch("luana_core_platform.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "luana_core_crm.application.services.lifecycle_service.LifecycleService.force_stage",
            ),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.put(
                    f"/api/v1/crm/pipeline/pipeline/{PROFILE_ID}/stage",
                    json={"new_stage": "mql", "note": "Manual promotion"},
                )

                assert response.status_code == 200
                body = response.json()
                assert body["profile_id"] == str(PROFILE_ID)
                assert body["new_stage"] == "mql"
                assert body["previous_stage"] == "lead"
            finally:
                app.dependency_overrides.pop(get_db, None)

    @pytest.mark.asyncio
    async def test_override_invalid_stage(self, client: AsyncClient) -> None:
        """Invalid stage value → 400."""
        response = await client.put(
            f"/api/v1/crm/pipeline/pipeline/{PROFILE_ID}/stage",
            json={"new_stage": "invalid_stage", "note": ""},
        )

        assert response.status_code == 400
        assert "Invalid stage" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_override_profile_not_found(self, client: AsyncClient) -> None:
        """Profile not found → 404."""
        from luana_core_platform.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()
        mock_scalars = MagicMock()
        mock_scalars.first.return_value = None
        mock_session.execute.return_value.scalars.return_value = mock_scalars

        with (
            patch("luana_core_platform.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.put(
                    f"/api/v1/crm/pipeline/pipeline/{PROFILE_ID}/stage",
                    json={"new_stage": "customer", "note": ""},
                )

                assert response.status_code == 404
            finally:
                app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Tests: GET /api/v1/crm/pipeline/{profile_id}/transitions  # noqa: ERA001
# ---------------------------------------------------------------------------


class TestGetTransitions:
    """GET /api/v1/crm/pipeline/{profile_id}/transitions — audit trail."""

    @pytest.mark.asyncio
    async def test_transitions_returns_records(self, client: AsyncClient) -> None:
        """Happy path: returns transition records."""
        from luana_core_platform.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()
        mock_transition = _make_transition()

        with (
            patch("luana_core_platform.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "luana_core_crm.infrastructure.repositories.lifecycle_repository.LifecycleRepository.get_transitions_by_profile",
                return_value=[mock_transition],
            ),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.get(
                    f"/api/v1/crm/pipeline/pipeline/{PROFILE_ID}/transitions",
                )

                assert response.status_code == 200
                body = response.json()
                assert len(body) == 1
                assert body[0]["to_stage"] == "lead"
                assert body[0]["triggered_by"] == "scoring_rule"
            finally:
                app.dependency_overrides.pop(get_db, None)

    @pytest.mark.asyncio
    async def test_transitions_empty_returns_empty_list(self, client: AsyncClient) -> None:
        """No transitions → empty list."""
        from luana_core_platform.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()

        with (
            patch("luana_core_platform.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "luana_core_crm.infrastructure.repositories.lifecycle_repository.LifecycleRepository.get_transitions_by_profile",
                return_value=[],
            ),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.get(
                    f"/api/v1/crm/pipeline/pipeline/{PROFILE_ID}/transitions",
                )

                assert response.status_code == 200
                assert response.json() == []
            finally:
                app.dependency_overrides.pop(get_db, None)
