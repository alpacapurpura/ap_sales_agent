"""Regression tests for Telegram webhook header convention.

Bug origin: PR-1 PI-5 used `Header(convert_underscores=False)` for the
`X-Telegram-Bot-Api-Secret-Token` parameter. Telegram sends the header in
HTTP dash-form (`X-Telegram-Bot-Api-Secret-Token`); FastAPI with
`convert_underscores=False` only matches a literal underscore-form name,
so every real Telegram webhook returned 401 in production.

These tests POST against the actual endpoint with both forms to lock the
behaviour: dash-form (Telegram) MUST be accepted, missing or wrong tokens
MUST be 401.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.copilot.api.telegram import router

_VALID_SECRET = "test-webhook-secret-token-fixture"


def _build_client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _payload_private_chat() -> dict:
    """Minimal valid Telegram update payload (private chat)."""
    return {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "date": 0,
            "chat": {"id": 123, "type": "private"},
            "from": {"id": 123, "is_bot": False, "first_name": "Test"},
            "text": "hello",
        },
    }


def _patch_settings_secret(monkeypatch) -> None:
    from src.core import config as cfg

    monkeypatch.setattr(
        cfg.settings,
        "COPILOT_TELEGRAM_WEBHOOK_SECRET_TOKEN",
        _VALID_SECRET,
    )


@patch("src.modules.copilot.api.telegram.get_arq_pool", new_callable=AsyncMock)
def test_webhook_accepts_dash_form_header_telegram_real_world(mock_arq, monkeypatch):
    """Telegram sends `X-Telegram-Bot-Api-Secret-Token` (dashes). MUST be 200."""
    _patch_settings_secret(monkeypatch)
    mock_arq.return_value.enqueue_job = AsyncMock()
    client = _build_client()

    resp = client.post(
        "/api/v1/copilot/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": _VALID_SECRET},
        json=_payload_private_chat(),
    )

    assert resp.status_code == 200, (
        f"Telegram dash-form header MUST authenticate. "
        f"Got {resp.status_code}: {resp.text}. "
        "If 401: regression of `Header(convert_underscores=False)` bug "
        "from PR-1. Remove the kwarg — FastAPI converts underscore param "
        "names to dash header names by default."
    )


@patch("src.modules.copilot.api.telegram.get_arq_pool", new_callable=AsyncMock)
def test_webhook_rejects_missing_secret_header(mock_arq, monkeypatch):
    _patch_settings_secret(monkeypatch)
    client = _build_client()

    resp = client.post(
        "/api/v1/copilot/telegram/webhook",
        json=_payload_private_chat(),
    )

    assert resp.status_code == 401


@patch("src.modules.copilot.api.telegram.get_arq_pool", new_callable=AsyncMock)
def test_webhook_rejects_wrong_secret_header(mock_arq, monkeypatch):
    _patch_settings_secret(monkeypatch)
    client = _build_client()

    resp = client.post(
        "/api/v1/copilot/telegram/webhook",
        headers={"X-Telegram-Bot-Api-Secret-Token": "WRONG-SECRET"},
        json=_payload_private_chat(),
    )

    assert resp.status_code == 401
