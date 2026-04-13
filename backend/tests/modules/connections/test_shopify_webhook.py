"""Tests for Shopify webhook handler.

Covers: checkout_initiated journey_event creation, idempotency,
error handling (always 200 OK), and tenant resolution from shop_domain.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers: mock payloads
# ---------------------------------------------------------------------------


def _checkout_payload(email: str = "buyer@example.com", token: str = "tok_123") -> dict:
    return {
        "email": email,
        "token": token,
        "total_price": "49.99",
        "currency": "USD",
        "line_items": [{"title": "Course", "quantity": 1}],
        "billing_address": {"name": "Test Buyer"},
    }


def _order_payload(email: str = "buyer@example.com", order_id: int = 999) -> dict:
    return {
        "id": order_id,
        "email": email,
        "checkout_token": "tok_123",
        "total_price": "49.99",
        "currency": "USD",
        "line_items": [{"title": "Course", "quantity": 1}],
        "billing_address": {"name": "Test Buyer"},
    }


# ---------------------------------------------------------------------------
# Mock profile helper
# ---------------------------------------------------------------------------


def _mock_profile():
    profile = MagicMock()
    profile.id = uuid.uuid4()
    profile.lead_source = None
    return profile


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_checkout_created_creates_journey_event():
    """_handle_checkout_created creates a JourneyEventModel with event_name='checkout_initiated'."""
    tenant_id = uuid.uuid4()
    payload = _checkout_payload()
    profile = _mock_profile()

    mock_db = MagicMock()
    # Make idempotency check return None (no duplicate)
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    with (
        patch(
            "src.modules.crm.application.services.customer_service.CustomerService.identify",
            return_value=profile,
        ),
        patch(
            "src.modules.crm.application.services.lifecycle_service.LifecycleService.recalculate_score",
            return_value=None,
        ),
    ):
        from src.modules.connections.api.marketing_webhooks import (
            _handle_checkout_created,
        )

        await _handle_checkout_created(mock_db, tenant_id, payload)

    # Verify JourneyEventModel was added to session
    mock_db.add.assert_called_once()
    event = mock_db.add.call_args[0][0]
    assert event.event_name == "checkout_initiated"
    assert event.event_type == "track"
    assert event.properties["source"] == "shopify"
    assert event.properties["checkout_token"] == "tok_123"
    assert event.properties["total_price"] == 49.99
    assert event.tenant_id == tenant_id

    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_checkout_created_idempotent():
    """Duplicate checkout_token should NOT create a second journey_event."""
    tenant_id = uuid.uuid4()
    payload = _checkout_payload()

    mock_db = MagicMock()
    # Idempotency check returns an existing event ID
    mock_db.execute.return_value.scalar_one_or_none.return_value = uuid.uuid4()

    from src.modules.connections.api.marketing_webhooks import _handle_checkout_created

    await _handle_checkout_created(mock_db, tenant_id, payload)

    # Should NOT add or commit anything
    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()


@pytest.mark.asyncio
async def test_shopify_webhook_returns_200_on_error():
    """The shopify_webhook endpoint always returns 200 even on processing errors."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from src.core.database import get_db
    from src.modules.connections.api.dependencies.webhook_security import (
        verify_shopify_signature,
    )
    from src.modules.connections.api.marketing_webhooks import router

    app = FastAPI()
    app.include_router(router, prefix="/webhooks")

    # Override dependencies to skip HMAC verification and DB
    mock_db = MagicMock()
    app.dependency_overrides[verify_shopify_signature] = lambda: True
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)

    # Send request with a topic but no matching tenant -> returns 200 with "ignored"
    response = client.post(
        "/webhooks/shopify",
        json={"email": "test@example.com"},
        headers={
            "X-Shopify-Hmac-Sha256": "fake",
            "X-Shopify-Topic": "checkouts/create",
            "X-Shopify-Shop-Domain": "nonexistent.myshopify.com",
        },
    )

    # Must always be 200
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_tenant_resolution_from_shop_domain():
    """_resolve_tenant looks up tenant_id via connections table."""
    from src.modules.connections.api.marketing_webhooks import (
        _resolve_tenant,
        _shop_tenant_cache,
    )

    tenant_id = uuid.uuid4()
    shop_domain = "test-shop.myshopify.com"

    # Clear cache for test isolation
    _shop_tenant_cache.clear()

    mock_db = MagicMock()

    # The function calls db.execute twice: first for tenant list, second for config
    mock_db.execute.side_effect = [
        MagicMock(all=MagicMock(return_value=[(tenant_id,)])),
        MagicMock(
            scalar_one_or_none=MagicMock(return_value={"shop_domain": shop_domain}),
        ),
    ]

    result = await _resolve_tenant(mock_db, shop_domain)
    assert result == tenant_id

    # Verify it's cached
    assert _shop_tenant_cache[shop_domain] == tenant_id

    # Clean up
    _shop_tenant_cache.clear()


@pytest.mark.asyncio
async def test_checkout_created_no_email_skips():
    """Checkout without email should be silently skipped."""
    tenant_id = uuid.uuid4()
    payload = {"token": "tok_noemail", "total_price": "10.00"}  # no email

    mock_db = MagicMock()

    from src.modules.connections.api.marketing_webhooks import _handle_checkout_created

    await _handle_checkout_created(mock_db, tenant_id, payload)

    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()
