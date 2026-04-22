"""Tests for /api/v1/copilot/conversations endpoints."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.database import get_db
from src.modules.copilot.api.conversations import router
from src.modules.iam.api.dependencies import get_current_user, get_tenant_context


def _build_client(tenant_id, user_id=None):
    """Build a TestClient with mocked auth dependencies."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/copilot")
    uid = user_id or uuid4()
    mock_db = MagicMock()

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=uid,
        tenant_id=tenant_id,
    )
    app.dependency_overrides[get_tenant_context] = lambda: tenant_id

    return TestClient(app), uid, mock_db


class TestListConversations:
    """GET /api/v1/copilot/conversations → 200 ConversationListResponse."""

    def test_returns_200_with_empty_list(self) -> None:
        """GET conversations returns 200 with empty items list."""
        tenant_id = uuid4()
        client, _uid, _mock_db = _build_client(tenant_id)

        with patch("src.modules.copilot.api.conversations.ConversationRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.list_paginated.return_value = {"items": [], "next_cursor": None}
            mock_repo_cls.return_value = mock_repo

            resp = client.get(
                "/api/v1/copilot/conversations",
                headers={"X-Tenant-ID": str(tenant_id)},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert data["items"] == []
        assert data["next_cursor"] is None

    def test_returns_conversation_list(self) -> None:
        """GET conversations returns list of ConversationSummary items."""
        tenant_id = uuid4()
        client, _uid, _mock_db = _build_client(tenant_id)
        conv_id = uuid4()

        with patch("src.modules.copilot.api.conversations.ConversationRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_conv = MagicMock()
            mock_conv.id = conv_id
            mock_conv.title = "Conversación de prueba"
            mock_conv.title_auto_generated = False
            mock_conv.updated_at = "2026-04-21T00:00:00Z"
            mock_conv.message_count = 4
            mock_conv.total_tokens = 1200
            mock_conv.last_tier_used = "mini"
            mock_conv.procedure_state = None
            mock_conv.archived_at = None

            mock_repo.list_paginated.return_value = {
                "items": [mock_conv],
                "next_cursor": None,
            }
            mock_repo_cls.return_value = mock_repo

            resp = client.get(
                "/api/v1/copilot/conversations",
                headers={"X-Tenant-ID": str(tenant_id)},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1


class TestCreateConversation:
    """POST /api/v1/copilot/conversations → 201 ConversationSummary."""

    def test_create_returns_201(self) -> None:
        """POST creates a new conversation and returns 201."""
        tenant_id = uuid4()
        client, _uid, _mock_db = _build_client(tenant_id)
        new_id = uuid4()

        with patch("src.modules.copilot.api.conversations.ConversationRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_conv = MagicMock()
            mock_conv.id = new_id
            mock_conv.title = None
            mock_conv.title_auto_generated = False
            mock_conv.updated_at = "2026-04-21T00:00:00Z"
            mock_conv.message_count = 0
            mock_conv.total_tokens = 0
            mock_conv.last_tier_used = None
            mock_conv.procedure_state = None
            mock_conv.archived_at = None
            mock_repo.create.return_value = mock_conv
            mock_repo_cls.return_value = mock_repo

            resp = client.post(
                "/api/v1/copilot/conversations",
                headers={"X-Tenant-ID": str(tenant_id)},
            )

        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data


class TestPatchConversation:
    """PATCH /api/v1/copilot/conversations/{id} → 200 ConversationSummary."""

    def test_patch_title_returns_200(self) -> None:
        """PATCH updates title and returns 200."""
        tenant_id = uuid4()
        client, _uid, _mock_db = _build_client(tenant_id)
        conv_id = uuid4()

        with patch("src.modules.copilot.api.conversations.ConversationRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_conv = MagicMock()
            mock_conv.id = conv_id
            mock_conv.title = "Nuevo título"
            mock_conv.title_auto_generated = False
            mock_conv.updated_at = "2026-04-21T00:00:00Z"
            mock_conv.message_count = 2
            mock_conv.total_tokens = 400
            mock_conv.last_tier_used = "nano"
            mock_conv.procedure_state = None
            mock_conv.archived_at = None
            mock_repo.get_by_id.return_value = mock_conv
            mock_repo_cls.return_value = mock_repo

            resp = client.patch(
                f"/api/v1/copilot/conversations/{conv_id}",
                json={"title": "Nuevo título"},
                headers={"X-Tenant-ID": str(tenant_id)},
            )

        assert resp.status_code == 200

    def test_patch_nonexistent_returns_404(self) -> None:
        """PATCH on nonexistent conversation returns 404."""
        tenant_id = uuid4()
        client, _uid, _mock_db = _build_client(tenant_id)

        with patch("src.modules.copilot.api.conversations.ConversationRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_cls.return_value = mock_repo

            resp = client.patch(
                f"/api/v1/copilot/conversations/{uuid4()}",
                json={"title": "X"},
                headers={"X-Tenant-ID": str(tenant_id)},
            )

        assert resp.status_code == 404


class TestDeleteConversation:
    """DELETE /api/v1/copilot/conversations/{id} → 204."""

    def test_delete_returns_204(self) -> None:
        """DELETE archives the conversation and returns 204."""
        tenant_id = uuid4()
        client, _uid, _mock_db = _build_client(tenant_id)
        conv_id = uuid4()

        with patch("src.modules.copilot.api.conversations.ConversationRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_conv = MagicMock()
            mock_conv.archived_at = None
            mock_repo.archive.return_value = mock_conv
            mock_repo_cls.return_value = mock_repo

            resp = client.delete(
                f"/api/v1/copilot/conversations/{conv_id}",
                headers={"X-Tenant-ID": str(tenant_id)},
            )

        assert resp.status_code == 204

    def test_delete_nonexistent_returns_404(self) -> None:
        """DELETE on nonexistent conversation returns 404."""
        tenant_id = uuid4()
        client, _uid, _mock_db = _build_client(tenant_id)

        with patch("src.modules.copilot.api.conversations.ConversationRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.archive.return_value = None
            mock_repo_cls.return_value = mock_repo

            resp = client.delete(
                f"/api/v1/copilot/conversations/{uuid4()}",
                headers={"X-Tenant-ID": str(tenant_id)},
            )

        assert resp.status_code == 404


class TestRevertConversation:
    """POST /api/v1/copilot/conversations/{id}/revert → 200 RevertResponse."""

    def test_revert_returns_200(self) -> None:
        """POST /revert returns 200 with reverted_count."""
        tenant_id = uuid4()
        client, _uid, _mock_db = _build_client(tenant_id)
        conv_id = uuid4()

        with (
            patch("src.modules.copilot.api.conversations.ConversationRepository") as mock_repo_cls,
            patch("src.modules.copilot.api.conversations.MutationJournalRepository") as mock_journal_cls,
        ):
            mock_conv = MagicMock()
            mock_conv.id = conv_id
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_conv
            mock_repo_cls.return_value = mock_repo

            mock_journal = MagicMock()
            mock_journal.fetch_by_conversation.return_value = []
            mock_journal_cls.return_value = mock_journal

            resp = client.post(
                f"/api/v1/copilot/conversations/{conv_id}/revert",
                json={},
                headers={"X-Tenant-ID": str(tenant_id)},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "reverted_count" in data
        assert "failed" in data

    def test_revert_nonexistent_conversation_404(self) -> None:
        """Revert on nonexistent conversation returns 404."""
        tenant_id = uuid4()
        client, _uid, _mock_db = _build_client(tenant_id)

        with patch("src.modules.copilot.api.conversations.ConversationRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_cls.return_value = mock_repo

            resp = client.post(
                f"/api/v1/copilot/conversations/{uuid4()}/revert",
                json={},
                headers={"X-Tenant-ID": str(tenant_id)},
            )

        assert resp.status_code == 404


class TestTenantIsolation:
    """Tenant isolation: endpoints cannot be called across tenants."""

    def test_endpoints_require_tenant_id(self) -> None:
        """A user with no tenant_id cannot access conversations."""
        app = FastAPI()
        app.include_router(router, prefix="/api/v1/copilot")
        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
            id=uuid4(),
            tenant_id=None,
        )
        app.dependency_overrides[get_tenant_context] = lambda: None

        client = TestClient(app)
        resp = client.get("/api/v1/copilot/conversations")
        assert resp.status_code in (401, 422, 403)
