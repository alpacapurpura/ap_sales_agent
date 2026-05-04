"""Tests for CRM CDP API endpoints.

CRM-15: POST /api/v1/crm/cdp/identify — customer identification via CDP.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.modules.crm.domain.customer import CustomerProfile

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
USER_ID = uuid.uuid4()

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


def _make_customer_profile(**overrides: Any) -> CustomerProfile:
    """Build a minimal CustomerProfile for mocking."""
    defaults: dict[str, Any] = {
        "id": uuid.uuid4(),
        "tenant_id": TENANT_ID,
        "primary_email": "identified@example.com",
        "full_name": "Identified User",
        "identities": [],
    }
    defaults.update(overrides)
    return CustomerProfile(**defaults)


# ---------------------------------------------------------------------------
# Tests: POST /api/v1/crm/cdp/identify  # noqa: ERA001
# ---------------------------------------------------------------------------


class TestIdentifyCustomer:
    """POST /api/v1/crm/cdp/identify — customer identification."""

    @pytest.mark.asyncio
    async def test_identify_with_traits_only(self, client: AsyncClient) -> None:
        """Happy path: traits dict → CustomerProfile returned."""
        from src.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()
        mock_profile = _make_customer_profile()

        with (
            patch("src.core.database.SessionLocal", return_value=mock_session),
            patch.object(
                mock_session,
                "__enter__",
                return_value=mock_session,
            ),
            patch.object(
                mock_session,
                "__exit__",
                return_value=False,
            ),
            patch(
                "src.modules.crm.application.services.customer_service.CustomerService.identify",
                return_value=mock_profile,
            ),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.post(
                    "/api/v1/crm/cdp/identify",
                    json={"traits": {"email": "test@example.com", "name": "Test"}},
                )

                assert response.status_code == 200
                body = response.json()
                assert body["primary_email"] == "identified@example.com"
            finally:
                app.dependency_overrides.pop(get_db, None)

    @pytest.mark.asyncio
    async def test_identify_with_user_id(self, client: AsyncClient) -> None:
        """userId in payload → passed as user_id identity."""
        from src.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()
        mock_profile = _make_customer_profile(full_name="User ID Customer")

        with (
            patch("src.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "src.modules.crm.application.services.customer_service.CustomerService.identify",
                return_value=mock_profile,
            ) as mock_identify,
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.post(
                    "/api/v1/crm/cdp/identify",
                    json={"traits": {"name": "Test"}, "userId": "usr-12345"},
                )

                assert response.status_code == 200
                call_kwargs = mock_identify.call_args
                assert call_kwargs[0][0] == TENANT_ID
                assert call_kwargs[0][1] == {"name": "Test"}
                assert call_kwargs[0][2] == {"user_id": "usr-12345"}
            finally:
                app.dependency_overrides.pop(get_db, None)

    @pytest.mark.asyncio
    async def test_identify_empty_payload(self, client: AsyncClient) -> None:
        """Empty payload → defaults to empty traits and no identities."""
        from src.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()
        mock_profile = _make_customer_profile()

        with (
            patch("src.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "src.modules.crm.application.services.customer_service.CustomerService.identify",
                return_value=mock_profile,
            ) as mock_identify,
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.post(
                    "/api/v1/crm/cdp/identify",
                    json={},
                )

                assert response.status_code == 200
                call_kwargs = mock_identify.call_args
                assert call_kwargs[0][1] == {}
                assert call_kwargs[0][2] == {}
            finally:
                app.dependency_overrides.pop(get_db, None)
