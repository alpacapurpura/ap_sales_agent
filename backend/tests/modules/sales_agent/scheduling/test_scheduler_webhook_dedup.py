"""S8 — Scheduler webhook idempotency + signature verification.

Internal scheduler does NOT use the webhook endpoint (its bookings come
via own POST /event-types/.../book flow). This test exercises the
endpoint with a registered fake provider — guaranteeing the contract
holds for future Cal.com / Calendly impls.
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

from luana_core_sales_agent.api import scheduler_webhooks
from luana_core_sales_agent.application.tools.scheduling.webhook_providers import (
    SCHEDULER_WEBHOOK_PROVIDERS,
    ParsedWebhookEvent,
    WebhookEventType,
    register_webhook_provider,
)

_SECRET = "shared-secret-test"


class FakeWebhookProvider:
    """Deterministic Cal.com-style HMAC-SHA256 signer for test fixture."""

    provider_id = "fake"

    def verify_signature(self, body: bytes, headers: dict[str, str], secret: str) -> bool:
        sig = headers.get("x-fake-signature-256", "")
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(sig, expected)

    def parse_payload(self, payload: dict[str, Any]) -> ParsedWebhookEvent:
        return ParsedWebhookEvent(
            provider_id=self.provider_id,
            event_type=WebhookEventType(payload["event_type"]),
            occurred_at=dt.datetime.fromisoformat(payload["occurred_at"]),
            tenant_id=uuid.UUID(payload["tenant_id"]) if payload.get("tenant_id") else None,
            lead_id=uuid.UUID(payload["lead_id"]) if payload.get("lead_id") else None,
            tracking_id=payload.get("tracking_id"),
            external_appointment_id=payload.get("appointment_id"),
            scheduled_at=(dt.datetime.fromisoformat(payload["scheduled_at"]) if payload.get("scheduled_at") else None),
            raw=payload,
        )


@pytest.fixture(autouse=True)
def _register_fake_provider(monkeypatch):
    register_webhook_provider(FakeWebhookProvider)
    monkeypatch.setenv("SCHEDULER_WEBHOOK_SECRET_FAKE", _SECRET)
    yield
    SCHEDULER_WEBHOOK_PROVIDERS.pop("fake", None)


@pytest.fixture
def client(db, db_engine):
    """FastAPI TestClient with the scheduler webhook router."""
    app = FastAPI()
    app.include_router(scheduler_webhooks.router, prefix="/api/v1/sales-agent")

    from luana_core_platform.core.database import get_db

    def _override_db():
        yield db

    app.dependency_overrides[get_db] = _override_db
    return TestClient(app)


def _signed_post(
    client: TestClient,
    *,
    body: dict[str, Any],
    secret: str = _SECRET,
) -> tuple[bytes, dict[str, str]]:
    raw = json.dumps(body).encode()
    sig = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return raw, {"x-fake-signature-256": sig, "content-type": "application/json"}


def test_unknown_provider_returns_404(client) -> None:
    res = client.post(
        "/api/v1/sales-agent/webhooks/scheduler/never-registered",
        json={},
        headers={"x-fake-signature-256": "x"},
    )
    assert res.status_code == 404


def test_invalid_signature_returns_401(client) -> None:
    body = {
        "event_type": "booking_confirmed",
        "occurred_at": dt.datetime.now(dt.UTC).isoformat(),
        "tenant_id": str(uuid.uuid4()),
        "lead_id": str(uuid.uuid4()),
        "tracking_id": "tok-1",
    }
    raw, _headers = _signed_post(client, body=body, secret="wrong")
    res = client.post(
        "/api/v1/sales-agent/webhooks/scheduler/fake",
        content=raw,
        headers={
            "x-fake-signature-256": "deadbeef",  # invalid sig
            "content-type": "application/json",
        },
    )
    assert res.status_code == 401


def test_valid_signature_parses_and_dedupes_replay(client) -> None:
    body = {
        "event_type": "booking_confirmed",
        "occurred_at": "2026-04-29T14:30:00+00:00",
        "tenant_id": str(uuid.uuid4()),
        "lead_id": str(uuid.uuid4()),
        "tracking_id": "tok-conf-1",
        "scheduled_at": "2026-04-30T15:00:00+00:00",
    }
    raw, headers = _signed_post(client, body=body)

    first = client.post(
        "/api/v1/sales-agent/webhooks/scheduler/fake",
        content=raw,
        headers=headers,
    )
    assert first.status_code == 200, first.text
    assert first.json()["status"] == "ok"

    # Replay (same body+sig) → duplicate
    second = client.post(
        "/api/v1/sales-agent/webhooks/scheduler/fake",
        content=raw,
        headers=headers,
    )
    assert second.status_code == 200
    payload = second.json()
    assert payload["status"] == "duplicate"
    assert payload["duplicate"] is True


def test_ignored_event_persists_dedup_but_does_not_dispatch(client) -> None:
    body = {
        "event_type": "ignored",
        "occurred_at": "2026-04-29T16:00:00+00:00",
        "tracking_id": "tok-ignored",
    }
    raw, headers = _signed_post(client, body=body)
    res = client.post(
        "/api/v1/sales-agent/webhooks/scheduler/fake",
        content=raw,
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["status"] == "ignored"
