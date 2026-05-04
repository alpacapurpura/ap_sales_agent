"""Tests for CRM sales API endpoints.

CRM-15: POST /api/v1/crm/sales/, GET /api/v1/crm/sales/ticker.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.modules.crm.domain.enums import SaleStage, SaleStatus

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
USER_ID = uuid.uuid4()
CUSTOMER_ID = uuid.uuid4()
OFFER_ID = uuid.uuid4()
SALE_ID = uuid.uuid4()

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


def _make_sale_model(**overrides: Any) -> MagicMock:
    """Build a mock SaleModel for response."""
    sale = MagicMock()
    sale.id = SALE_ID
    sale.tenant_id = TENANT_ID
    sale.customer_id = CUSTOMER_ID
    sale.offer_id = OFFER_ID
    sale.transaction_id = "txn-123"
    sale.amount = 99.0
    sale.currency = "USD"
    sale.status = "COMPLETED"
    sale.status = SaleStatus.COMPLETED
    sale.stage = SaleStage.CONVERSION
    sale.source = "MANUAL"
    sale.payment_method = "STRIPE"
    sale.metadata = {}
    sale.occurred_at = datetime.now(timezone.utc)
    sale.created_at = datetime.now(timezone.utc)
    for key, value in overrides.items():
        setattr(sale, key, value)
    return sale


def _make_customer_model(**overrides: Any) -> MagicMock:
    """Build a mock CustomerProfileModel."""
    customer = MagicMock()
    customer.id = CUSTOMER_ID
    customer.full_name = "Test Customer"
    for key, value in overrides.items():
        setattr(customer, key, value)
    return customer


# ---------------------------------------------------------------------------
# Tests: POST /api/v1/crm/sales/
# ---------------------------------------------------------------------------


class TestCreateSale:
    """POST /api/v1/crm/sales/ — create a new sale record."""

    @pytest.mark.asyncio
    async def test_create_sale_success(self, client: AsyncClient) -> None:
        """Valid body → 201 + SaleResponse."""
        from src.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()
        mock_sale = _make_sale_model()

        with (
            patch("src.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "src.modules.crm.application.services.sale_service.SaleService.create_sale",
                return_value=mock_sale,
            ),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.post(
                    "/api/v1/crm/sales/",
                    json={
                        "customer_id": str(CUSTOMER_ID),
                        "offer_id": str(OFFER_ID),
                        "amount": 99.0,
                        "payment_method": "STRIPE",
                    },
                )

                assert response.status_code == 200
                body = response.json()
                assert body["amount"] == 99.0
                assert body["customer_id"] == str(CUSTOMER_ID)
                assert body["offer_id"] == str(OFFER_ID)
            finally:
                app.dependency_overrides.pop(get_db, None)

    @pytest.mark.asyncio
    async def test_create_sale_with_optional_fields(self, client: AsyncClient) -> None:
        """Include transaction_id, source, metadata → persisted."""
        from src.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()
        mock_sale = _make_sale_model(transaction_id="txn-custom", source="api")

        with (
            patch("src.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "src.modules.crm.application.services.sale_service.SaleService.create_sale",
                return_value=mock_sale,
            ),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.post(
                    "/api/v1/crm/sales/",
                    json={
                        "customer_id": str(CUSTOMER_ID),
                        "offer_id": str(OFFER_ID),
                        "amount": 50.0,
                        "payment_method": "PAYPAL",
                        "transaction_id": "txn-custom",
                        "source": "api",
                        "metadata": {"campaign": "summer"},
                    },
                )

                assert response.status_code == 200
            finally:
                app.dependency_overrides.pop(get_db, None)

    @pytest.mark.asyncio
    async def test_create_sale_missing_required_fields(self, client: AsyncClient) -> None:
        """Missing required fields → 422."""
        response = await client.post(
            "/api/v1/crm/sales/",
            json={"amount": 99.0},
        )

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Tests: GET /api/v1/crm/sales/ticker  # noqa: ERA001
# ---------------------------------------------------------------------------


class TestGetTicker:
    """GET /api/v1/crm/sales/ticker — recent sales ticker."""

    @pytest.mark.asyncio
    async def test_ticker_default_range(self, client: AsyncClient) -> None:
        """Default 30d range → returns ticker items."""
        from src.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()
        mock_sale = _make_sale_model()
        mock_customer = _make_customer_model()

        with (
            patch("src.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "src.modules.crm.infrastructure.repositories.sale_repository.SaleRepository.get_sales_by_date_range",
                return_value=[mock_sale],
            ),
        ):
            mock_session.execute.return_value.scalars.return_value.all.return_value = [mock_customer]
            mock_session.execute.return_value.mappings.return_value.all.return_value = []

            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.get("/api/v1/crm/sales/ticker")

                assert response.status_code == 200
                body = response.json()
                assert len(body) == 1
                assert body[0]["amount"] == 99.0
            finally:
                app.dependency_overrides.pop(get_db, None)

    @pytest.mark.asyncio
    async def test_ticker_today_range(self, client: AsyncClient) -> None:
        """range=today → returns today's sales."""
        from src.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()

        with (
            patch("src.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "src.modules.crm.infrastructure.repositories.sale_repository.SaleRepository.get_sales_by_date_range",
                return_value=[],
            ),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.get("/api/v1/crm/sales/ticker", params={"range": "today"})

                assert response.status_code == 200
                assert response.json() == []
            finally:
                app.dependency_overrides.pop(get_db, None)

    @pytest.mark.asyncio
    async def test_ticker_all_range(self, client: AsyncClient) -> None:
        """range=all → returns all sales."""
        from src.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()

        with (
            patch("src.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "src.modules.crm.infrastructure.repositories.sale_repository.SaleRepository.get_sales_by_date_range",
                return_value=[],
            ),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.get("/api/v1/crm/sales/ticker", params={"range": "all"})

                assert response.status_code == 200
                assert response.json() == []
            finally:
                app.dependency_overrides.pop(get_db, None)

    @pytest.mark.asyncio
    async def test_ticker_week_range(self, client: AsyncClient) -> None:
        """range=week → returns this week's sales."""
        from src.core.database import get_db
        from src.main import app

        mock_session = _make_mock_session()

        with (
            patch("src.core.database.SessionLocal", return_value=mock_session),
            patch.object(mock_session, "__enter__", return_value=mock_session),
            patch.object(mock_session, "__exit__", return_value=False),
            patch(
                "src.modules.crm.infrastructure.repositories.sale_repository.SaleRepository.get_sales_by_date_range",
                return_value=[],
            ),
        ):
            app.dependency_overrides[get_db] = lambda: mock_session

            try:
                response = await client.get("/api/v1/crm/sales/ticker", params={"range": "week"})

                assert response.status_code == 200
                assert response.json() == []
            finally:
                app.dependency_overrides.pop(get_db, None)
