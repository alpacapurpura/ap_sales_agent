"""Tests for CRM NPS API endpoints.

CRM-15: POST /api/v1/crm/nps/surveys, GET /api/v1/crm/nps/survey/{token},
POST /api/v1/crm/nps/survey/{token}/respond, GET /api/v1/crm/nps/summary,
GET /api/v1/crm/nps/candidates.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
USER_ID = uuid.uuid4()
SURVEY_TOKEN = "nps-test-token-123"

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
    from src.modules.iam.api.dependencies import get_current_user

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


def _make_survey(**overrides: Any) -> MagicMock:
    """Build a mock NPS survey."""
    survey = MagicMock()
    survey.id = uuid.uuid4()
    survey.token = SURVEY_TOKEN
    survey.status = "pending"
    survey.delivery_channel = "universal_link"
    survey.offer_id = uuid.uuid4()
    survey.customer_id = uuid.uuid4()
    survey.tenant_id = TENANT_ID
    for key, value in overrides.items():
        setattr(survey, key, value)
    return survey


def _make_nps_response(**overrides: Any) -> MagicMock:
    """Build a mock NPS response record."""
    resp = MagicMock()
    resp.id = uuid.uuid4()
    resp.score = 9
    for key, value in overrides.items():
        setattr(resp, key, value)
    return resp


# ---------------------------------------------------------------------------
# Tests: POST /api/v1/crm/nps/surveys  # noqa: ERA001
# ---------------------------------------------------------------------------


class TestCreateSurvey:
    """POST /api/v1/crm/nps/surveys — create NPS survey."""

    @pytest.mark.asyncio
    async def test_create_survey_success(self, client: AsyncClient) -> None:
        """Valid request → 200 + survey with token URL."""
        from src.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()
        mock_survey = _make_survey()

        with (
            patch("src.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "src.modules.crm.application.services.nps_service.NpsService.create_survey",
                return_value=mock_survey,
            ),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.post(
                    "/api/v1/crm/nps/surveys",
                    json={"delivery_channel": "universal_link"},
                )

                assert response.status_code == 200
                body = response.json()
                assert body["token"] == SURVEY_TOKEN
                assert body["survey_url"] == f"/nps/survey/{SURVEY_TOKEN}"
            finally:
                app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Tests: GET /api/v1/crm/nps/survey/{token}  # noqa: ERA001
# ---------------------------------------------------------------------------


class TestGetSurvey:
    """GET /api/v1/crm/nps/survey/{token} — public survey retrieval."""

    @pytest.mark.asyncio
    async def test_get_survey_success(self, client: AsyncClient) -> None:
        """Valid token → 200 + survey details."""
        from src.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()
        mock_survey = _make_survey()

        with (
            patch("src.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "src.modules.crm.application.services.nps_service.NpsService.get_survey_by_token",
                return_value=mock_survey,
            ),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.get(f"/api/v1/crm/nps/survey/{SURVEY_TOKEN}")

                assert response.status_code == 200
                body = response.json()
                assert body["token"] == SURVEY_TOKEN
                assert body["status"] == "pending"
            finally:
                app.dependency_overrides.pop(get_db, None)

    @pytest.mark.asyncio
    async def test_get_survey_not_found(self, client: AsyncClient) -> None:
        """Unknown token → 404."""
        from src.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()

        with (
            patch("src.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "src.modules.crm.application.services.nps_service.NpsService.get_survey_by_token",
                return_value=None,
            ),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.get(f"/api/v1/crm/nps/survey/{SURVEY_TOKEN}")

                assert response.status_code == 404
            finally:
                app.dependency_overrides.pop(get_db, None)

    @pytest.mark.asyncio
    async def test_get_survey_expired(self, client: AsyncClient) -> None:
        """Expired survey → 410."""
        from src.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()
        mock_survey = _make_survey(status="expired")

        with (
            patch("src.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "src.modules.crm.application.services.nps_service.NpsService.get_survey_by_token",
                return_value=mock_survey,
            ),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.get(f"/api/v1/crm/nps/survey/{SURVEY_TOKEN}")

                assert response.status_code == 410
            finally:
                app.dependency_overrides.pop(get_db, None)

    @pytest.mark.asyncio
    async def test_get_survey_already_responded(self, client: AsyncClient) -> None:
        """Already responded → 409."""
        from src.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()
        mock_survey = _make_survey(status="responded")

        with (
            patch("src.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "src.modules.crm.application.services.nps_service.NpsService.get_survey_by_token",
                return_value=mock_survey,
            ),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.get(f"/api/v1/crm/nps/survey/{SURVEY_TOKEN}")

                assert response.status_code == 409
            finally:
                app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Tests: POST /api/v1/crm/nps/survey/{token}/respond  # noqa: ERA001
# ---------------------------------------------------------------------------


class TestSubmitNpsResponse:
    """POST /api/v1/crm/nps/survey/{token}/respond — submit NPS score."""

    @pytest.mark.asyncio
    async def test_submit_success(self, client: AsyncClient) -> None:
        """Valid score → 200 + confirmation."""
        from src.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()
        mock_survey = _make_survey()
        mock_response = _make_nps_response()

        with (
            patch("src.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "src.modules.crm.application.services.nps_service.NpsService.get_survey_by_token",
                return_value=mock_survey,
            ),
            patch(
                "src.modules.crm.application.services.nps_service.NpsService.submit_response",
                return_value=mock_response,
            ),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.post(
                    f"/api/v1/crm/nps/survey/{SURVEY_TOKEN}/respond",
                    json={"score": 9, "feedback_text": "Great product!"},
                )

                assert response.status_code == 200
                body = response.json()
                assert body["score"] == 9
                assert body["status"] == "responded"
            finally:
                app.dependency_overrides.pop(get_db, None)

    @pytest.mark.asyncio
    async def test_submit_invalid_score(self, client: AsyncClient) -> None:
        """Score out of range → 400."""
        from src.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()
        mock_survey = _make_survey()

        with (
            patch("src.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "src.modules.crm.application.services.nps_service.NpsService.get_survey_by_token",
                return_value=mock_survey,
            ),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.post(
                    f"/api/v1/crm/nps/survey/{SURVEY_TOKEN}/respond",
                    json={"score": 11},
                )

                assert response.status_code == 400
            finally:
                app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Tests: GET /api/v1/crm/nps/summary  # noqa: ERA001
# ---------------------------------------------------------------------------


class TestGetNpsSummary:
    """GET /api/v1/crm/nps/summary — NPS metrics."""

    @pytest.mark.asyncio
    async def test_summary_returns_metrics(self, client: AsyncClient) -> None:
        """Happy path → 200 + NPS summary."""
        from src.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()
        summary_data = {
            "nps_score": 45.0,
            "standard_nps": 45.0,
            "promoter_count": 10,
            "passive_count": 5,
            "detractor_count": 3,
            "total_responses": 18,
            "surveys_sent": 50,
            "response_rate_pct": 36.0,
        }

        with (
            patch("src.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "src.modules.crm.application.services.nps_service.NpsService.get_nps_summary",
                return_value=summary_data,
            ),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.get("/api/v1/crm/nps/summary")

                assert response.status_code == 200
                body = response.json()
                assert body["nps_score"] == 45.0
                assert body["promoter_count"] == 10
            finally:
                app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Tests: GET /api/v1/crm/nps/candidates  # noqa: ERA001
# ---------------------------------------------------------------------------


class TestGetEvangelistCandidates:
    """GET /api/v1/crm/nps/candidates — high NPS not yet evangelists."""

    @pytest.mark.asyncio
    async def test_candidates_returns_list(self, client: AsyncClient) -> None:
        """Happy path → 200 + candidate list."""
        from src.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()
        candidates = [
            {
                "customer_id": str(uuid.uuid4()),
                "full_name": "Happy Customer",
                "nps_score": 10,
                "responded_at": "2024-01-15T10:00:00Z",
            },
        ]

        with (
            patch("src.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "src.modules.crm.application.services.nps_service.NpsService.get_evangelist_candidates",
                return_value=candidates,
            ),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.get("/api/v1/crm/nps/candidates")

                assert response.status_code == 200
                body = response.json()
                assert len(body) == 1
                assert body[0]["nps_score"] == 10
            finally:
                app.dependency_overrides.pop(get_db, None)

    @pytest.mark.asyncio
    async def test_candidates_empty_returns_empty_list(self, client: AsyncClient) -> None:
        """No candidates → empty list."""
        from src.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()

        with (
            patch("src.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "src.modules.crm.application.services.nps_service.NpsService.get_evangelist_candidates",
                return_value=[],
            ),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.get("/api/v1/crm/nps/candidates")

                assert response.status_code == 200
                assert response.json() == []
            finally:
                app.dependency_overrides.pop(get_db, None)
