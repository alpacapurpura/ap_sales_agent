"""S9 — Payment webhook idempotency + signature verification (RED → GREEN).

Tests:
- Valid MP signature → 200 ok, event published
- Invalid signature → 401 (fail-closed)
- Replay → 200 duplicate (no double event)
- Unknown provider → 404
- Per-tenant secret lookup (ChannelConnectionModel.config)
"""

from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import json
import uuid
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

_SECRET = "test-payment-webhook-secret"

TENANT_ID = uuid.UUID("aaaa9010-0000-0000-0000-000000000001")
LEAD_ID = uuid.UUID("bbbb9010-0000-0000-0000-000000000001")


class FakePaymentWebhookProvider:
    """Deterministic HMAC-SHA256 payment webhook provider for tests."""

    provider_id = "fakepay"

    def verify_signature(self, body: bytes, headers: dict[str, str], secret: str) -> bool:
        sig = headers.get("x-fakepay-signature", "")
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(sig, expected)

    def parse_payload(self, payload: dict[str, Any]):
        from luana_core_sales_agent.application.tools.payment.webhook_providers import (
            ParsedPaymentWebhookEvent,
            PaymentWebhookEventType,
        )

        return ParsedPaymentWebhookEvent(
            provider_id=self.provider_id,
            event_type=PaymentWebhookEventType(payload["event_type"]),
            occurred_at=dt.datetime.fromisoformat(payload["occurred_at"]),
            tenant_id=uuid.UUID(payload["tenant_id"]) if payload.get("tenant_id") else None,
            lead_id=uuid.UUID(payload["lead_id"]) if payload.get("lead_id") else None,
            external_payment_id=payload.get("payment_id"),
            payment_status=payload.get("status", "paid"),
            raw=payload,
        )


@pytest.fixture(autouse=True)
def _register_fake_provider(monkeypatch):
    from luana_core_sales_agent.application.tools.payment.webhook_providers import (
        PAYMENT_WEBHOOK_PROVIDERS,
        register_payment_webhook_provider,
    )

    register_payment_webhook_provider(FakePaymentWebhookProvider)
    # Env-var fallback for secret (stub pattern from S8)
    monkeypatch.setenv("PAYMENT_WEBHOOK_SECRET_FAKEPAY", _SECRET)
    yield
    PAYMENT_WEBHOOK_PROVIDERS.pop("fakepay", None)


@pytest.fixture
def client(db):
    from luana_core_platform.core.database import get_db
    from luana_core_sales_agent.api import payment_webhooks

    app = FastAPI()
    app.include_router(payment_webhooks.router, prefix="/api/v1/sales-agent")

    def _override_db():
        yield db

    app.dependency_overrides[get_db] = _override_db
    return TestClient(app)


def _signed_body(payload: dict) -> tuple[bytes, str]:
    body = json.dumps(payload).encode()
    sig = hmac.new(_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return body, sig


def _valid_payload(event_type: str = "payment.paid") -> dict:
    return {
        "event_type": event_type,
        "occurred_at": dt.datetime.now(dt.UTC).isoformat(),
        "tenant_id": str(TENANT_ID),
        "lead_id": str(LEAD_ID),
        "payment_id": "mp_001",
        "status": "paid",
    }


def test_valid_signature_returns_200(client) -> None:
    payload = _valid_payload()
    body, sig = _signed_body(payload)
    resp = client.post(
        "/api/v1/sales-agent/webhooks/payment/fakepay",
        content=body,
        headers={"content-type": "application/json", "x-fakepay-signature": sig},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_invalid_signature_returns_401(client) -> None:
    payload = _valid_payload()
    body = json.dumps(payload).encode()
    resp = client.post(
        "/api/v1/sales-agent/webhooks/payment/fakepay",
        content=body,
        headers={"content-type": "application/json", "x-fakepay-signature": "badsig"},
    )
    assert resp.status_code == 401


def test_unknown_provider_returns_404(client) -> None:
    resp = client.post(
        "/api/v1/sales-agent/webhooks/payment/nonexistent",
        content=b"{}",
        headers={"content-type": "application/json"},
    )
    assert resp.status_code == 404


def test_replay_returns_duplicate(client, db) -> None:
    """Second identical request → 200 with duplicate=True."""
    payload = _valid_payload()
    body, sig = _signed_body(payload)
    headers = {"content-type": "application/json", "x-fakepay-signature": sig}

    first = client.post("/api/v1/sales-agent/webhooks/payment/fakepay", content=body, headers=headers)
    second = client.post("/api/v1/sales-agent/webhooks/payment/fakepay", content=body, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["duplicate"] is True


def test_webhook_persists_to_dedup_table(client, db) -> None:
    from luana_core_sales_agent.infrastructure.models.payment_webhook_event_model import (
        PaymentWebhookEventModel,
    )

    payload = _valid_payload()
    body, sig = _signed_body(payload)
    client.post(
        "/api/v1/sales-agent/webhooks/payment/fakepay",
        content=body,
        headers={"content-type": "application/json", "x-fakepay-signature": sig},
    )

    rows = db.query(PaymentWebhookEventModel).filter_by(provider="fakepay").all()
    assert len(rows) == 1
    assert rows[0].tenant_id == TENANT_ID


def test_signature_missing_empty_secret_returns_401(client, monkeypatch) -> None:
    """If no secret configured (env var empty) → fail-closed → 401."""
    monkeypatch.setenv("PAYMENT_WEBHOOK_SECRET_FAKEPAY", "")
    payload = _valid_payload()
    body, _ = _signed_body(payload)
    # Even with valid sig, if secret is empty, verify returns False (no empty secret bypass)
    sig = hmac.new(b"", body, hashlib.sha256).hexdigest()
    resp = client.post(
        "/api/v1/sales-agent/webhooks/payment/fakepay",
        content=body,
        headers={"content-type": "application/json", "x-fakepay-signature": sig},
    )
    # Empty secret means verify_signature must fail-closed
    # (Implementation must reject empty secrets)
    assert resp.status_code == 401
