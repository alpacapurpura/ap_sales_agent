"""Tests for GET /api/v1/copilot/conversations/{id}/mutations.

The endpoint is consumed by ``ProposalCard`` to repaint per-field
"applied" status after a refresh — without it the card always re-renders
pending and the user sees the same proposal twice.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from luana_core_platform.core.database import get_db
from luana_core_copilot.api.conversations import router
from luana_core_iam.api.dependencies import get_current_user, get_tenant_context


def _build_client(tenant_id):
    """Wire FastAPI test client with mocked auth/db deps."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/copilot")
    user_id = uuid4()
    mock_db = MagicMock()

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=user_id,
        tenant_id=tenant_id,
    )
    app.dependency_overrides[get_tenant_context] = lambda: tenant_id

    return TestClient(app), user_id, mock_db


def _conv_stub(conv_id, tenant_id):
    """Return a dummy conversation row that the repo lookup will yield."""
    return SimpleNamespace(id=conv_id, tenant_id=tenant_id, title=None)


def _row_stub(*, message_id, field_path, domain="buyer_persona", entity_id=None):
    return SimpleNamespace(
        id=uuid4(),
        message_id=message_id,
        domain=domain,
        entity_id=entity_id,
        field_path=field_path,
        applied_at=datetime.now(UTC),
    )


class TestListMutationsContract:
    """Endpoint exists, requires auth, and returns the journal list shape."""

    def test_returns_404_when_conversation_missing(self) -> None:
        tenant_id = uuid4()
        conv_id = uuid4()
        client, _uid, _db = _build_client(tenant_id)

        with patch(
            "luana_core_copilot.api.conversations.ConversationRepository",
        ) as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_cls.return_value = mock_repo

            resp = client.get(
                f"/api/v1/copilot/conversations/{conv_id}/mutations",
                headers={"X-Tenant-ID": str(tenant_id)},
            )

        assert resp.status_code == 404

    def test_returns_401_without_tenant(self) -> None:
        conv_id = uuid4()
        app = FastAPI()
        app.include_router(router, prefix="/api/v1/copilot")
        mock_db = MagicMock()
        mock_user = SimpleNamespace(id=uuid4(), tenant_id=None)

        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_tenant_context] = lambda: None
        client = TestClient(app)

        resp = client.get(f"/api/v1/copilot/conversations/{conv_id}/mutations")
        assert resp.status_code == 401


class TestListMutationsHappyPath:
    """Active rows are returned; reverted rows are filtered out by the repo."""

    def test_returns_active_entries(self) -> None:
        tenant_id = uuid4()
        conv_id = uuid4()
        msg_id = uuid4()
        client, _uid, _db = _build_client(tenant_id)

        rows = [
            _row_stub(message_id=msg_id, field_path="pain_points"),
            _row_stub(message_id=msg_id, field_path="demographics.age_range"),
        ]

        with (
            patch(
                "luana_core_copilot.api.conversations.ConversationRepository",
            ) as mock_repo_cls,
            patch(
                "luana_core_copilot.api.conversations.MutationJournalRepository",
            ) as mock_journal_cls,
        ):
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = _conv_stub(conv_id, tenant_id)
            mock_repo_cls.return_value = mock_repo

            mock_journal = MagicMock()
            mock_journal.fetch_by_conversation.return_value = rows
            mock_journal_cls.return_value = mock_journal

            resp = client.get(
                f"/api/v1/copilot/conversations/{conv_id}/mutations",
                headers={"X-Tenant-ID": str(tenant_id)},
            )

            kwargs = mock_journal.fetch_by_conversation.call_args.kwargs
            assert kwargs["tenant_id"] == tenant_id
            assert kwargs["conversation_id"] == conv_id
            assert kwargs["include_reverted"] is False
            assert kwargs["message_id"] is None

        assert resp.status_code == 200
        body = resp.json()
        assert len(body["entries"]) == 2
        paths = {e["field_path"] for e in body["entries"]}
        assert paths == {"pain_points", "demographics.age_range"}

    def test_message_id_query_param_narrows_lookup(self) -> None:
        tenant_id = uuid4()
        conv_id = uuid4()
        msg_id = uuid4()
        other_msg_id = uuid4()
        client, _uid, _db = _build_client(tenant_id)

        with (
            patch(
                "luana_core_copilot.api.conversations.ConversationRepository",
            ) as mock_repo_cls,
            patch(
                "luana_core_copilot.api.conversations.MutationJournalRepository",
            ) as mock_journal_cls,
        ):
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = _conv_stub(conv_id, tenant_id)
            mock_repo_cls.return_value = mock_repo

            mock_journal = MagicMock()
            mock_journal.fetch_by_conversation.return_value = [
                _row_stub(message_id=msg_id, field_path="pain_points"),
            ]
            mock_journal_cls.return_value = mock_journal

            resp = client.get(
                f"/api/v1/copilot/conversations/{conv_id}/mutations",
                params={"message_id": str(msg_id)},
                headers={"X-Tenant-ID": str(tenant_id)},
            )

            kwargs = mock_journal.fetch_by_conversation.call_args.kwargs
            assert kwargs["message_id"] == msg_id
            # The handler must NEVER look up another tenant's data.
            assert kwargs["tenant_id"] == tenant_id

        assert resp.status_code == 200
        body = resp.json()
        assert len(body["entries"]) == 1
        assert body["entries"][0]["message_id"] == str(msg_id)
        # Sanity: a different message_id would have come from a different
        # call — we never echo it here.
        assert body["entries"][0]["message_id"] != str(other_msg_id)
