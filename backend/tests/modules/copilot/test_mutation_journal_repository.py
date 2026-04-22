"""Tests for MutationJournalRepository — insert, fetch, mark_reverted."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.modules.copilot.infrastructure.repositories.mutation_journal_repository import (
    MutationJournalRepository,
)


@pytest.fixture
def repo(db):
    return MutationJournalRepository(db)


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def conversation_id():
    return uuid4()


class TestMutationJournalInsert:
    """insert() stores journal entries correctly."""

    def test_insert_returns_row_with_id(self, repo, db, tenant_id, conversation_id) -> None:
        """insert() returns a model row with an auto-generated id."""
        row = repo.insert(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            message_id=uuid4(),
            domain="brand",
            entity_id=None,
            field_path="value_proposition",
            old_value=None,
            new_value={"text": "New proposition"},
        )
        db.commit()

        assert row.id is not None
        assert row.tenant_id == tenant_id
        assert row.domain == "brand"
        assert row.field_path == "value_proposition"
        assert row.reverted_at is None

    def test_insert_stores_old_and_new_value(self, repo, db, tenant_id, conversation_id) -> None:
        """old_value and new_value are preserved as JSONB."""
        entity_id = uuid4()
        row = repo.insert(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            message_id=uuid4(),
            domain="offer",
            entity_id=entity_id,
            field_path="price",
            old_value={"amount": 100},
            new_value={"amount": 200},
        )
        db.commit()

        assert row.old_value == {"amount": 100}
        assert row.new_value == {"amount": 200}


class TestFetchByConversation:
    """fetch_by_conversation() retrieves entries for a conversation."""

    def test_returns_entries_for_conversation(self, repo, db, tenant_id, conversation_id) -> None:
        """Entries for the conversation are returned."""
        repo.insert(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            message_id=uuid4(),
            domain="brand",
            entity_id=None,
            field_path="name",
            old_value="Old",
            new_value="New",
        )
        db.commit()

        rows = repo.fetch_by_conversation(tenant_id=tenant_id, conversation_id=conversation_id)
        assert len(rows) == 1
        assert rows[0].field_path == "name"

    def test_excludes_other_conversation(self, repo, db, tenant_id, conversation_id) -> None:
        """Entries from another conversation are not returned."""
        other_conv = uuid4()
        repo.insert(
            tenant_id=tenant_id,
            conversation_id=other_conv,
            message_id=uuid4(),
            domain="offer",
            entity_id=None,
            field_path="title",
            old_value=None,
            new_value="X",
        )
        db.commit()

        rows = repo.fetch_by_conversation(tenant_id=tenant_id, conversation_id=conversation_id)
        assert rows == []

    def test_excludes_other_tenant(self, repo, db, tenant_id, conversation_id) -> None:
        """Cross-tenant entries are never returned."""
        other_tenant = uuid4()
        repo.insert(
            tenant_id=other_tenant,
            conversation_id=conversation_id,
            message_id=uuid4(),
            domain="brand",
            entity_id=None,
            field_path="bio",
            old_value=None,
            new_value="X",
        )
        db.commit()

        rows = repo.fetch_by_conversation(tenant_id=tenant_id, conversation_id=conversation_id)
        assert rows == []


class TestMarkReverted:
    """mark_reverted() sets reverted_at on specified entries."""

    def test_mark_reverted_sets_timestamp(self, repo, db, tenant_id, conversation_id) -> None:
        """mark_reverted() populates reverted_at."""
        row = repo.insert(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            message_id=uuid4(),
            domain="brand",
            entity_id=None,
            field_path="headline",
            old_value="Old headline",
            new_value="New headline",
        )
        db.commit()

        repo.mark_reverted(tenant_id=tenant_id, entry_ids=[row.id])
        db.commit()

        db.refresh(row)
        assert row.reverted_at is not None

    def test_mark_reverted_only_affects_specified_ids(self, repo, db, tenant_id, conversation_id) -> None:
        """Only specified IDs are reverted; others remain un-reverted."""
        row_a = repo.insert(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            message_id=uuid4(),
            domain="brand",
            entity_id=None,
            field_path="field_a",
            old_value=None,
            new_value="A",
        )
        row_b = repo.insert(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            message_id=uuid4(),
            domain="brand",
            entity_id=None,
            field_path="field_b",
            old_value=None,
            new_value="B",
        )
        db.commit()

        repo.mark_reverted(tenant_id=tenant_id, entry_ids=[row_a.id])
        db.commit()

        db.refresh(row_a)
        db.refresh(row_b)
        assert row_a.reverted_at is not None
        assert row_b.reverted_at is None

    def test_mark_reverted_wrong_tenant_no_op(self, repo, db, tenant_id, conversation_id) -> None:
        """Wrong tenant cannot revert another tenant's entries."""
        row = repo.insert(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            message_id=uuid4(),
            domain="brand",
            entity_id=None,
            field_path="x",
            old_value=None,
            new_value="y",
        )
        db.commit()

        repo.mark_reverted(tenant_id=uuid4(), entry_ids=[row.id])
        db.commit()

        db.refresh(row)
        assert row.reverted_at is None
