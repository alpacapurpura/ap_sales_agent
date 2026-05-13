"""TDD — POST /api/v1/copilot/suggestions endpoint.

Tests written RED first per ``tdd-mandatory.md``.

# [COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
"""

from __future__ import annotations

import ast
import importlib
import inspect
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from luana_core_iam.api.dependencies import get_current_user, get_tenant_context


def _build_client(tenant_id: UUID, user_id: UUID | None = None) -> tuple[TestClient, UUID]:
    """Build TestClient with mocked auth dependencies for suggestions router."""
    from luana_core_copilot.api.suggestions import router

    app = FastAPI()
    app.include_router(router, prefix="/api/v1/copilot")

    uid = user_id or uuid4()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=uid,
        tenant_id=tenant_id,
    )
    app.dependency_overrides[get_tenant_context] = lambda: tenant_id

    return TestClient(app), uid


class TestSuggestionsHappyPath:
    """POST /suggestions → 200 con chips."""

    def test_suggestions_happy_path_returns_chips(self) -> None:
        """OfferSuggestionProvider mockeado retorna 3 chips → 200 + length 3 + breakdown."""
        from luana_core_copilot.domain.suggestion import Suggestion, SuggestionCategory

        tenant_id = uuid4()
        client, _uid = _build_client(tenant_id)

        chips = [
            Suggestion(
                id=uuid4(),
                label=f"Chip {i}",
                prompt=f"Prompt {i}",
                confidence=0.9 - i * 0.1,
                category=SuggestionCategory.ACTION,
                source_module="offer",
            )
            for i in range(3)
        ]

        with (
            patch("luana_core_copilot.api.suggestions.get_default_engine") as mock_engine_fn,
            patch("luana_core_copilot.api.suggestions.EventBus"),
        ):
            mock_engine = MagicMock()
            mock_engine.get_suggestions.return_value = (chips, {"offer": 3}, 5)
            mock_engine_fn.return_value = mock_engine

            resp = client.post(
                "/api/v1/copilot/suggestions",
                json={"current_route": "offer-studio"},
                headers={"X-Tenant-ID": str(tenant_id)},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["suggestions"]) == 3
        assert data["breakdown"] == {"offer": 3}
        assert data["latency_ms"] >= 0

    def test_suggestions_empty_engine_returns_empty_200(self) -> None:
        """Engine retorna [] → 200 + suggestions=[] (D-10: best-effort)."""
        tenant_id = uuid4()
        client, _uid = _build_client(tenant_id)

        with (
            patch("luana_core_copilot.api.suggestions.get_default_engine") as mock_engine_fn,
            patch("luana_core_copilot.api.suggestions.EventBus"),
        ):
            mock_engine = MagicMock()
            mock_engine.get_suggestions.return_value = ([], {}, 2)
            mock_engine_fn.return_value = mock_engine

            resp = client.post(
                "/api/v1/copilot/suggestions",
                json={},
                headers={"X-Tenant-ID": str(tenant_id)},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["suggestions"] == []
        assert data["breakdown"] == {}

    def test_suggestions_engine_exception_returns_empty_200(self) -> None:
        """Engine raises → 200 + suggestions=[] + structlog warning (D-10)."""
        tenant_id = uuid4()
        client, _uid = _build_client(tenant_id)

        with (
            patch("luana_core_copilot.api.suggestions.get_default_engine") as mock_engine_fn,
            patch("luana_core_copilot.api.suggestions.EventBus"),
            patch("luana_core_copilot.api.suggestions.logger") as mock_logger,
        ):
            mock_engine = MagicMock()
            mock_engine.get_suggestions.side_effect = RuntimeError("DB connection failed")
            mock_engine_fn.return_value = mock_engine

            resp = client.post(
                "/api/v1/copilot/suggestions",
                json={"current_route": "offer-studio"},
                headers={"X-Tenant-ID": str(tenant_id)},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["suggestions"] == []
        mock_logger.warning.assert_called()


class TestSuggestionsValidation:
    """Validation gate tests (422, 401)."""

    def test_suggestions_missing_tenant_header_returns_401(self) -> None:
        """Sin X-Tenant-ID (tenant_id None) → 401."""
        from luana_core_copilot.api.suggestions import router

        app = FastAPI()
        app.include_router(router, prefix="/api/v1/copilot")

        uid = uuid4()
        # Override: tenant_id returns None to simulate missing/invalid header
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
            id=uid,
            tenant_id=None,
        )
        app.dependency_overrides[get_tenant_context] = lambda: None

        client = TestClient(app)
        resp = client.post(
            "/api/v1/copilot/suggestions",
            json={},
        )
        assert resp.status_code == 401

    def test_suggestions_invalid_route_too_long_returns_422(self) -> None:
        """current_route con 201 chars → 422 (Pydantic max_length=200)."""
        tenant_id = uuid4()
        client, _uid = _build_client(tenant_id)

        resp = client.post(
            "/api/v1/copilot/suggestions",
            json={"current_route": "a" * 201},
            headers={"X-Tenant-ID": str(tenant_id)},
        )
        assert resp.status_code == 422


class TestSuggestionsObservability:
    """Observability + domain event emission tests."""

    def test_suggestions_emits_shown_event_always(self) -> None:
        """EventBus.publish llamado con SuggestionShown incluso con 0 chips (D-11)."""
        from luana_core_copilot.domain.events import SuggestionShown

        tenant_id = uuid4()
        client, _uid = _build_client(tenant_id)

        with (
            patch("luana_core_copilot.api.suggestions.get_default_engine") as mock_engine_fn,
            patch("luana_core_copilot.api.suggestions.EventBus") as mock_bus,
        ):
            mock_engine = MagicMock()
            mock_engine.get_suggestions.return_value = ([], {}, 3)
            mock_engine_fn.return_value = mock_engine

            resp = client.post(
                "/api/v1/copilot/suggestions",
                json={},
                headers={"X-Tenant-ID": str(tenant_id)},
            )

        assert resp.status_code == 200
        mock_bus.publish.assert_called_once()
        call_args = mock_bus.publish.call_args
        event = call_args[0][0]
        assert isinstance(event, SuggestionShown)
        assert event.event_name == "copilot_suggestion_shown"

    def test_suggestions_response_excludes_metadata(self) -> None:
        """Engine retorna chip con metadata → response NO contiene `metadata` (D-6)."""
        from luana_core_copilot.domain.suggestion import Suggestion, SuggestionCategory

        tenant_id = uuid4()
        client, _uid = _build_client(tenant_id)

        chip = Suggestion(
            id=uuid4(),
            label="Configura tu oferta",
            prompt="Quiero configurar mi oferta",
            confidence=0.8,
            category=SuggestionCategory.ACTION,
            source_module="offer",
            metadata={"internal_key": "secret_value"},
        )

        with (
            patch("luana_core_copilot.api.suggestions.get_default_engine") as mock_engine_fn,
            patch("luana_core_copilot.api.suggestions.EventBus"),
        ):
            mock_engine = MagicMock()
            mock_engine.get_suggestions.return_value = ([chip], {"offer": 1}, 4)
            mock_engine_fn.return_value = mock_engine

            resp = client.post(
                "/api/v1/copilot/suggestions",
                json={"current_route": "offer-studio"},
                headers={"X-Tenant-ID": str(tenant_id)},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["suggestions"]) == 1
        suggestion_json = data["suggestions"][0]
        assert "metadata" not in suggestion_json

    def test_suggestions_response_model_is_declared(self) -> None:
        """Router decorator declara response_model=SuggestionsResponse."""
        import src.modules.copilot.api.suggestions as mod

        source = inspect.getsource(mod)
        tree = ast.parse(source)

        found_response_model = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for kw in node.keywords:
                    if kw.arg == "response_model":
                        found_response_model = True
                        break

        assert found_response_model, "response_model= not declared in suggestions router"
