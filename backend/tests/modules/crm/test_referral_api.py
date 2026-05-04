"""Tests for CRM referral API endpoints.

CRM-15: GET /api/v1/crm/referrals, POST /api/v1/crm/referrals/promote,
POST /api/v1/crm/referrals/generate.
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
CUSTOMER_ID = uuid.uuid4()

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


def _make_referral_code(**overrides: Any) -> MagicMock:
    """Build a mock referral code object."""
    code = MagicMock()
    code.id = uuid.uuid4()
    code.customer_id = CUSTOMER_ID
    code.code = "REF-ABC123"
    code.source = "internal"
    code.is_active = True
    for key, value in overrides.items():
        setattr(code, key, value)
    return code


def _make_profile(**overrides: Any) -> MagicMock:
    """Build a mock customer profile."""
    profile = MagicMock()
    profile.id = CUSTOMER_ID
    profile.lifecycle_stage = MagicMock()
    profile.lifecycle_stage.value = "evangelist"
    for key, value in overrides.items():
        setattr(profile, key, value)
    return profile


# ---------------------------------------------------------------------------
# Tests: GET /api/v1/crm/referrals  # noqa: ERA001
# ---------------------------------------------------------------------------


class TestListReferralCodes:
    """GET /api/v1/crm/referrals — list active referral codes."""

    @pytest.mark.asyncio
    async def test_list_returns_codes(self, client: AsyncClient) -> None:
        """Happy path: returns list of referral codes."""
        from src.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()
        mock_code = _make_referral_code()

        with (
            patch("src.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "src.modules.crm.application.services.referral_service.ReferralService.get_codes_by_tenant",
                return_value=[mock_code],
            ),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.get("/api/v1/crm/referrals")

                assert response.status_code == 200
                body = response.json()
                assert len(body) == 1
                assert body[0]["code"] == "REF-ABC123"
                assert body[0]["is_active"] is True
            finally:
                app.dependency_overrides.pop(get_db, None)

    @pytest.mark.asyncio
    async def test_list_empty_returns_empty_list(self, client: AsyncClient) -> None:
        """No codes → empty list."""
        from src.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()

        with (
            patch("src.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "src.modules.crm.application.services.referral_service.ReferralService.get_codes_by_tenant",
                return_value=[],
            ),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.get("/api/v1/crm/referrals")

                assert response.status_code == 200
                assert response.json() == []
            finally:
                app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Tests: POST /api/v1/crm/referrals/promote  # noqa: ERA001
# ---------------------------------------------------------------------------


class TestPromoteToEvangelist:
    """POST /api/v1/crm/referrals/promote — promote customer to evangelist."""

    @pytest.mark.asyncio
    async def test_promote_success(self, client: AsyncClient) -> None:
        """Valid customer_id → 200 + promotion details."""
        from src.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()
        mock_profile = _make_profile()
        mock_code = _make_referral_code()

        with (
            patch("src.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "src.modules.crm.application.services.lifecycle_service.LifecycleService.promote_to_evangelist",
                return_value=(mock_profile, mock_code),
            ),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.post(
                    "/api/v1/crm/referrals/promote",
                    json={"customer_id": str(CUSTOMER_ID)},
                )

                assert response.status_code == 200
                body = response.json()
                assert body["profile_id"] == str(CUSTOMER_ID)
                assert body["referral_code"] == "REF-ABC123"
                assert body["lifecycle_stage"] == "evangelist"
            finally:
                app.dependency_overrides.pop(get_db, None)

    @pytest.mark.asyncio
    async def test_promote_invalid_uuid(self, client: AsyncClient) -> None:
        """Invalid customer_id → 400."""
        response = await client.post(
            "/api/v1/crm/referrals/promote",
            json={"customer_id": "not-a-uuid"},
        )

        assert response.status_code == 400
        assert "Invalid customer_id format" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_promote_profile_not_found(self, client: AsyncClient) -> None:
        """Profile not found → 404."""
        from src.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()

        with (
            patch("src.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "src.modules.crm.application.services.lifecycle_service.LifecycleService.promote_to_evangelist",
                side_effect=ValueError("Profile not found"),
            ),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.post(
                    "/api/v1/crm/referrals/promote",
                    json={"customer_id": str(CUSTOMER_ID)},
                )

                assert response.status_code == 404
            finally:
                app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Tests: POST /api/v1/crm/referrals/generate  # noqa: ERA001
# ---------------------------------------------------------------------------


class TestGenerateReferralCode:
    """POST /api/v1/crm/referrals/generate — generate code for evangelist."""

    @pytest.mark.asyncio
    async def test_generate_success(self, client: AsyncClient) -> None:
        """Valid request → 201 + referral code."""
        from src.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()
        mock_code = _make_referral_code()

        with (
            patch("src.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "src.modules.crm.application.services.referral_service.ReferralService.get_code_by_customer",
                return_value=None,
            ),
            patch(
                "src.modules.crm.application.services.referral_service.ReferralService.generate_code",
                return_value=mock_code,
            ),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.post(
                    "/api/v1/crm/referrals/generate",
                    json={"customer_id": str(CUSTOMER_ID)},
                )

                assert response.status_code == 200
                body = response.json()
                assert body["code"] == "REF-ABC123"
            finally:
                app.dependency_overrides.pop(get_db, None)

    @pytest.mark.asyncio
    async def test_generate_invalid_uuid(self, client: AsyncClient) -> None:
        """Invalid customer_id → 400."""
        response = await client.post(
            "/api/v1/crm/referrals/generate",
            json={"customer_id": "not-a-uuid"},
        )

        assert response.status_code == 400
        assert "Invalid customer_id format" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_generate_already_has_code(self, client: AsyncClient) -> None:
        """Customer already has code → 409."""
        from src.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()
        existing_code = _make_referral_code(code="EXISTING-CODE")

        with (
            patch("src.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "src.modules.crm.application.services.referral_service.ReferralService.get_code_by_customer",
                return_value=existing_code,
            ),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.post(
                    "/api/v1/crm/referrals/generate",
                    json={"customer_id": str(CUSTOMER_ID)},
                )

                assert response.status_code == 409
                assert "already has referral code" in response.json()["detail"]
            finally:
                app.dependency_overrides.pop(get_db, None)
