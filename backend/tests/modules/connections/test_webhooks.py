import base64
import hashlib
import hmac
import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Ensure backend path is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))


@pytest.fixture(scope="module")
def app():
    from src.main import app as _app

    return _app


@pytest.fixture(scope="module")
def client(app):
    return TestClient(app)


# Helper functions to generate signatures
def generate_shopify_signature(secret, body):
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def generate_meta_signature(secret, body):
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


@pytest.fixture
def mock_settings():
    with patch(
        "src.modules.connections.api.dependencies.webhook_security.settings"
    ) as mock:
        mock.SHOPIFY_API_SECRET = "test_shopify_secret"  # noqa: S105
        mock.META_APP_SECRET = "test_meta_secret"  # noqa: S105
        yield mock


@pytest.fixture
def mock_db(app):
    from src.core.database import get_db

    mock_session = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_session
    yield mock_session
    app.dependency_overrides = {}


# --- Shopify Tests ---


def test_shopify_signature_valid(client, mock_settings, mock_db):
    payload = {"test": "shopify_data"}
    body = json.dumps(payload).encode("utf-8")
    signature = generate_shopify_signature(mock_settings.SHOPIFY_API_SECRET, body)

    headers = {"X-Shopify-Hmac-Sha256": signature, "Content-Type": "application/json"}

    # Note: Using the actual mounted path found in main.py
    response = client.post(
        "/api/v1/connections/marketing-webhooks/shopify", content=body, headers=headers
    )

    # Valid signature must not return 401 (signature error)
    assert response.status_code == 200
    assert response.json().get("status") != "invalid_signature"


def test_shopify_signature_invalid(client, mock_settings, mock_db):
    payload = {"test": "shopify_data"}
    body = json.dumps(payload).encode("utf-8")

    headers = {
        "X-Shopify-Hmac-Sha256": "invalid_signature",
        "Content-Type": "application/json",
    }

    response = client.post(
        "/api/v1/connections/marketing-webhooks/shopify", content=body, headers=headers
    )

    # Expect 401 per implementation in webhook_security.py
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Shopify signature"


def test_shopify_compliance_data_request_valid(client, mock_settings, mock_db):
    payload = {
        "shop_id": 954889,
        "shop_domain": "johns-apparel.myshopify.com",
        "orders_requested": [299938, 280263, 220458],
        "customer": {
            "id": 191167,
            "email": "john@example.com",
            "phone": "+1-234-567-8910",
        },
    }
    body = json.dumps(payload).encode("utf-8")
    signature = generate_shopify_signature(mock_settings.SHOPIFY_API_SECRET, body)

    headers = {"X-Shopify-Hmac-Sha256": signature, "Content-Type": "application/json"}

    response = client.post(
        "/api/v1/connections/shopify/compliance/customers/data_request",
        content=body,
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "received"


def test_shopify_compliance_customers_redact_valid(client, mock_settings, mock_db):
    payload = {
        "shop_id": 954889,
        "shop_domain": "johns-apparel.myshopify.com",
        "customer": {
            "id": 191167,
            "email": "john@example.com",
            "phone": "+1-234-567-8910",
        },
        "orders_to_redact": [299938, 280263, 220458],
    }
    body = json.dumps(payload).encode("utf-8")
    signature = generate_shopify_signature(mock_settings.SHOPIFY_API_SECRET, body)

    headers = {"X-Shopify-Hmac-Sha256": signature, "Content-Type": "application/json"}

    response = client.post(
        "/api/v1/connections/shopify/compliance/customers/redact",
        content=body,
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "received"


def test_shopify_compliance_shop_redact_valid(client, mock_settings, mock_db):
    payload = {"shop_id": 954889, "shop_domain": "johns-apparel.myshopify.com"}
    body = json.dumps(payload).encode("utf-8")
    signature = generate_shopify_signature(mock_settings.SHOPIFY_API_SECRET, body)

    headers = {"X-Shopify-Hmac-Sha256": signature, "Content-Type": "application/json"}

    response = client.post(
        "/api/v1/connections/shopify/compliance/shop/redact",
        content=body,
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "received"


def test_shopify_compliance_invalid_hmac_returns_401(client, mock_settings, mock_db):
    payload = {"shop_id": 954889, "shop_domain": "johns-apparel.myshopify.com"}
    body = json.dumps(payload).encode("utf-8")

    headers = {
        "X-Shopify-Hmac-Sha256": "invalid_signature",
        "Content-Type": "application/json",
    }

    response = client.post(
        "/api/v1/connections/shopify/compliance/shop/redact",
        content=body,
        headers=headers,
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Shopify signature"


# --- Meta Tests ---


def test_meta_signature_valid(client, mock_settings, mock_db):
    # Mock DB query result
    # It queries: db.query(ChannelConnectionModel).filter(...).all()
    # We want it to return empty list so it goes to "ignored" path, or return a connection.
    # Let's return empty list for simplicity as we just test signature here.
    mock_db.query.return_value.filter.return_value.all.return_value = []

    payload = {
        "object": "instagram",
        "entry": [{"id": "123456789", "time": 12345678, "changes": []}],
    }
    body = json.dumps(payload).encode("utf-8")
    signature = generate_meta_signature(mock_settings.META_APP_SECRET, body)

    headers = {"X-Hub-Signature-256": signature, "Content-Type": "application/json"}

    response = client.post(
        "/api/v1/connections/meta/webhook", content=body, headers=headers
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ignored", "reason": "unknown_account"}


def test_meta_signature_invalid(client, mock_settings, mock_db):
    payload = {"object": "instagram"}
    body = json.dumps(payload).encode("utf-8")

    headers = {
        "X-Hub-Signature-256": "sha256=invalid_signature",
        "Content-Type": "application/json",
    }

    response = client.post(
        "/api/v1/connections/meta/webhook", content=body, headers=headers
    )

    # Expect 401 per implementation in webhook_security.py
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Meta signature"
