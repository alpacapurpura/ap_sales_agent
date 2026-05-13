"""TDD — POST /api/v1/copilot/suggestions/accept endpoint.

Tests written RED first per ``tdd-mandatory.md``.

# [COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from luana_core_iam.api.dependencies import get_current_user, get_tenant_context


def _build_client(tenant_id: UUID | None, user_id: UUID | None = None) -> TestClient:
    """Build TestClient with mocked auth for accept endpoint."""
    from luana_core_copilot.api.suggestions import router

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/copilot")

    uid = user_id or uuid4()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=uid,
        tenant_id=tenant_id,
    )
    app.dependency_overrides[get_tenant_context] = lambda: tenant_id

    return TestClient(app)


def _valid_accept_body(suggestion_id: UUID | None = None) -> dict:
    """Return a valid accept request body."""
    return {
        "suggestion_id": str(suggestion_id or uuid4()),
        "conversation_id": None,
        "current_route": "offer-studio",
        "category": "action",
        "source_module": "offer",
        "accepted_at": datetime.now(tz=timezone.utc).isoformat(),
    }


class TestAcceptHappyPath:
    """POST /suggestions/accept → 202 ok=True."""

    def test_accept_happy_path_returns_202_ok_true(self) -> None:
        """Body válido → 202 + ok=True + EventBus.publish llamado."""
        from luana_core_copilot.domain.events import SuggestionAccepted

        tenant_id = uuid4()
        client = _build_client(tenant_id)

        with patch("luana_core_copilot.api.suggestions.EventBus") as mock_bus:
            resp = client.post(
                "/api/v1/copilot/suggestions/accept",
                json=_valid_accept_body(),
                headers={"X-Tenant-ID": str(tenant_id)},
            )

        assert resp.status_code == 202
        data = resp.json()
        assert data["ok"] is True
        mock_bus.publish.assert_called_once()
        call_args = mock_bus.publish.call_args
        event = call_args[0][0]
        assert isinstance(event, SuggestionAccepted)

    def test_accept_publishes_event_with_correct_payload(self) -> None:
        """Verificar campos del SuggestionAccepted event matchean request."""
        from luana_core_copilot.domain.events import SuggestionAccepted

        tenant_id = uuid4()
        user_id = uuid4()
        suggestion_id = uuid4()
        client = _build_client(tenant_id, user_id=user_id)

        body = _valid_accept_body(suggestion_id)
        body["source_module"] = "brand"
        body["category"] = "clarify"

        with patch("luana_core_copilot.api.suggestions.EventBus") as mock_bus:
            resp = client.post(
                "/api/v1/copilot/suggestions/accept",
                json=body,
                headers={"X-Tenant-ID": str(tenant_id)},
            )

        assert resp.status_code == 202
        event: SuggestionAccepted = mock_bus.publish.call_args[0][0]
        assert event.payload["suggestion_id"] == str(suggestion_id)
        assert event.payload["source_module"] == "brand"
        assert event.payload["category"] == "clarify"
        assert event.tenant_id == tenant_id


class TestAcceptValidation:
    """Validation + error handling tests."""

    def test_accept_invalid_uuid_returns_422(self) -> None:
        """suggestion_id no UUID → 422 (Pydantic validation)."""
        tenant_id = uuid4()
        client = _build_client(tenant_id)

        body = _valid_accept_body()
        body["suggestion_id"] = "not-a-uuid"

        resp = client.post(
            "/api/v1/copilot/suggestions/accept",
            json=body,
            headers={"X-Tenant-ID": str(tenant_id)},
        )
        assert resp.status_code == 422

    def test_accept_missing_tenant_returns_401(self) -> None:
        """Sin X-Tenant-ID (tenant None) → 401."""
        client = _build_client(tenant_id=None)

        resp = client.post(
            "/api/v1/copilot/suggestions/accept",
            json=_valid_accept_body(),
        )
        assert resp.status_code == 401

    def test_accept_event_publish_failure_returns_ok_false(self) -> None:
        """EventBus.publish raises → 202 + ok=False + warning logged."""
        tenant_id = uuid4()
        client = _build_client(tenant_id)

        with (
            patch("luana_core_copilot.api.suggestions.EventBus") as mock_bus,
            patch("luana_core_copilot.api.suggestions.logger") as mock_logger,
        ):
            mock_bus.publish.side_effect = RuntimeError("Redis unavailable")

            resp = client.post(
                "/api/v1/copilot/suggestions/accept",
                json=_valid_accept_body(),
                headers={"X-Tenant-ID": str(tenant_id)},
            )

        assert resp.status_code == 202
        data = resp.json()
        assert data["ok"] is False
        mock_logger.warning.assert_called()
