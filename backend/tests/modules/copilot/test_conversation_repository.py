"""Tests for extended ConversationRepository methods (list_paginated, archive, etc.)."""

from __future__ import annotations

import base64
import json
from uuid import uuid4

import pytest

from luana_core_copilot.infrastructure.models.conversation_model import (
    CopilotConversationModel,
)
from luana_core_copilot.infrastructure.repositories.conversation_repository import (
    ConversationRepository,
)


@pytest.fixture
def repo(db):
    """Return a ConversationRepository bound to the test session."""
    return ConversationRepository(db)


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def user_id():
    return uuid4()


def _make_conv(db, *, tenant_id, user_id, title: str | None = None) -> CopilotConversationModel:
    """Helper: create and flush a conversation row."""
    conv = CopilotConversationModel(
        id=uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        title=title,
        messages=[],
    )
    db.add(conv)
    db.flush()
    return conv


class TestListPaginated:
    """list_paginated returns cursor-paginated results filtered by tenant+user."""

    def test_returns_empty_for_new_tenant(self, repo, tenant_id, user_id) -> None:
        """No rows → empty items, no next_cursor."""
        page = repo.list_paginated(tenant_id=tenant_id, user_id=user_id)
        assert page["items"] == []
        assert page["next_cursor"] is None

    def test_returns_conversations_for_tenant_user(self, repo, db, tenant_id, user_id) -> None:
        """Conversations are returned for correct tenant+user."""
        _make_conv(db, tenant_id=tenant_id, user_id=user_id, title="Chat A")
        _make_conv(db, tenant_id=tenant_id, user_id=user_id, title="Chat B")
        db.commit()

        page = repo.list_paginated(tenant_id=tenant_id, user_id=user_id)
        assert len(page["items"]) == 2

    def test_excludes_other_tenant(self, repo, db, tenant_id, user_id) -> None:
        """Conversations from another tenant are not visible."""
        other_tenant = uuid4()
        _make_conv(db, tenant_id=other_tenant, user_id=user_id)
        db.commit()

        page = repo.list_paginated(tenant_id=tenant_id, user_id=user_id)
        assert page["items"] == []

    def test_excludes_archived_by_default(self, repo, db, tenant_id, user_id) -> None:
        """Archived conversations are excluded when include_archived=False."""
        conv = _make_conv(db, tenant_id=tenant_id, user_id=user_id)
        db.commit()
        repo.archive(conversation_id=conv.id, tenant_id=tenant_id, user_id=user_id)
        db.commit()

        page = repo.list_paginated(tenant_id=tenant_id, user_id=user_id, include_archived=False)
        assert page["items"] == []

    def test_includes_archived_when_requested(self, repo, db, tenant_id, user_id) -> None:
        """Archived conversations appear when include_archived=True."""
        conv = _make_conv(db, tenant_id=tenant_id, user_id=user_id)
        db.commit()
        repo.archive(conversation_id=conv.id, tenant_id=tenant_id, user_id=user_id)
        db.commit()

        page = repo.list_paginated(tenant_id=tenant_id, user_id=user_id, include_archived=True)
        assert len(page["items"]) == 1

    def test_respects_limit(self, repo, db, tenant_id, user_id) -> None:
        """limit parameter constrains result count."""
        for _ in range(5):
            _make_conv(db, tenant_id=tenant_id, user_id=user_id)
        db.commit()

        page = repo.list_paginated(tenant_id=tenant_id, user_id=user_id, limit=3)
        assert len(page["items"]) <= 3

    def test_returns_next_cursor_when_more_results(self, repo, db, tenant_id, user_id) -> None:
        """next_cursor is set when more items exist."""
        for _ in range(4):
            _make_conv(db, tenant_id=tenant_id, user_id=user_id)
        db.commit()

        page = repo.list_paginated(tenant_id=tenant_id, user_id=user_id, limit=2)
        assert page["next_cursor"] is not None

    def test_no_next_cursor_when_all_fetched(self, repo, db, tenant_id, user_id) -> None:
        """next_cursor is None when all items fit in one page."""
        _make_conv(db, tenant_id=tenant_id, user_id=user_id)
        db.commit()

        page = repo.list_paginated(tenant_id=tenant_id, user_id=user_id, limit=10)
        assert page["next_cursor"] is None


class TestArchive:
    """archive() sets archived_at, does not delete."""

    def test_archive_sets_archived_at(self, repo, db, tenant_id, user_id) -> None:
        """archive() populates archived_at on the row."""
        conv = _make_conv(db, tenant_id=tenant_id, user_id=user_id)
        db.commit()

        result = repo.archive(conversation_id=conv.id, tenant_id=tenant_id, user_id=user_id)
        db.commit()

        assert result is not None
        assert result.archived_at is not None

    def test_archive_wrong_tenant_returns_none(self, repo, db, tenant_id, user_id) -> None:
        """archive() on wrong tenant returns None (no cross-tenant mutation)."""
        conv = _make_conv(db, tenant_id=tenant_id, user_id=user_id)
        db.commit()

        result = repo.archive(conversation_id=conv.id, tenant_id=uuid4(), user_id=user_id)
        assert result is None

    def test_row_still_exists_after_archive(self, repo, db, tenant_id, user_id) -> None:
        """Archived conversations are NOT hard-deleted."""
        conv = _make_conv(db, tenant_id=tenant_id, user_id=user_id)
        db.commit()
        repo.archive(conversation_id=conv.id, tenant_id=tenant_id, user_id=user_id)
        db.commit()

        # Even with deleted_at check disabled (raw query)
        from sqlalchemy import select

        from luana_core_copilot.infrastructure.models.conversation_model import (
            CopilotConversationModel,
        )

        stmt = select(CopilotConversationModel).where(CopilotConversationModel.id == conv.id)
        row = db.execute(stmt).scalars().first()
        assert row is not None
        assert row.archived_at is not None


class TestUpdateSummary:
    """update_summary() writes summary + total_tokens + clears dirty flag."""

    def test_update_summary_stores_text(self, repo, db, tenant_id, user_id) -> None:
        """update_summary() persists the summary text."""
        conv = _make_conv(db, tenant_id=tenant_id, user_id=user_id)
        db.commit()

        repo.update_summary(
            conversation_id=conv.id,
            tenant_id=tenant_id,
            summary="Resumen de prueba",
            total_tokens=1500,
        )
        db.commit()

        db.refresh(conv)
        assert conv.summary == "Resumen de prueba"

    def test_update_summary_wrong_tenant_no_op(self, repo, db, tenant_id, user_id) -> None:
        """update_summary() is a no-op for wrong tenant."""
        conv = _make_conv(db, tenant_id=tenant_id, user_id=user_id)
        db.commit()

        repo.update_summary(
            conversation_id=conv.id,
            tenant_id=uuid4(),
            summary="Hacked summary",
            total_tokens=0,
        )
        db.commit()

        db.refresh(conv)
        assert conv.summary is None


class TestIncrementMessageCount:
    """increment_message_count() adds delta to message_count."""

    def test_increment_adds_to_count(self, repo, db, tenant_id, user_id) -> None:
        """message_count goes from 0 to delta after increment."""
        conv = _make_conv(db, tenant_id=tenant_id, user_id=user_id)
        db.commit()

        repo.increment_message_count(conversation_id=conv.id, tenant_id=tenant_id, delta=2)
        db.commit()

        db.refresh(conv)
        assert conv.message_count == 2

    def test_increment_accumulates(self, repo, db, tenant_id, user_id) -> None:
        """Multiple increments accumulate."""
        conv = _make_conv(db, tenant_id=tenant_id, user_id=user_id)
        db.commit()

        repo.increment_message_count(conversation_id=conv.id, tenant_id=tenant_id, delta=1)
        repo.increment_message_count(conversation_id=conv.id, tenant_id=tenant_id, delta=1)
        db.commit()

        db.refresh(conv)
        assert conv.message_count == 2
