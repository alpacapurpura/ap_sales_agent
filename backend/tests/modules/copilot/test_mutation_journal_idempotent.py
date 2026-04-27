"""Idempotent upsert behavior on MutationJournalRepository (B22-FP1 AC5)."""

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


class TestUpsertIdempotent:
    """upsert_idempotent() — same natural key returns existing active row."""

    def test_first_call_inserts_new_row(self, repo, db, tenant_id, conversation_id) -> None:
        msg_id = uuid4()
        row, status = repo.upsert_idempotent(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            message_id=msg_id,
            domain="brand",
            entity_id=None,
            field_path="identity.brand_name",
            old_value=None,
            new_value="Visionarias",
        )
        db.commit()

        assert row.id is not None
        assert row.field_path == "identity.brand_name"
        assert row.new_value == "Visionarias"
        assert status == "applied"

    def test_repeat_call_returns_existing_row(self, repo, db, tenant_id, conversation_id) -> None:
        """Same (tenant, conv, message, field_path) twice → 1 row, 2nd call status=existing."""
        msg_id = uuid4()
        first, status_first = repo.upsert_idempotent(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            message_id=msg_id,
            domain="brand",
            entity_id=None,
            field_path="identity.brand_name",
            old_value=None,
            new_value="Visionarias",
        )
        db.commit()

        second, status_second = repo.upsert_idempotent(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            message_id=msg_id,
            domain="brand",
            entity_id=None,
            field_path="identity.brand_name",
            old_value=None,
            new_value="Visionarias",
        )
        db.commit()

        assert first.id == second.id
        assert status_first == "applied"
        assert status_second == "existing"

        rows = repo.fetch_by_conversation(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
        )
        assert len(rows) == 1

    def test_reverted_row_does_not_block_new_insert(self, repo, db, tenant_id, conversation_id) -> None:
        """If a prior row was reverted, a fresh apply re-inserts (active row check)."""
        msg_id = uuid4()
        first, _status = repo.upsert_idempotent(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            message_id=msg_id,
            domain="brand",
            entity_id=None,
            field_path="identity.brand_name",
            old_value=None,
            new_value="Visionarias",
        )
        db.commit()

        repo.mark_reverted(tenant_id=tenant_id, entry_ids=[first.id])
        db.commit()

        second, status_second = repo.upsert_idempotent(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            message_id=msg_id,
            domain="brand",
            entity_id=None,
            field_path="identity.brand_name",
            old_value=None,
            new_value="Visionarias 2",
        )
        db.commit()

        assert second.id != first.id
        assert status_second == "applied"

    def test_different_field_path_inserts_new_row(self, repo, db, tenant_id, conversation_id) -> None:
        """Different field_path = different natural key = new row."""
        msg_id = uuid4()
        row_a, _ = repo.upsert_idempotent(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            message_id=msg_id,
            domain="brand",
            entity_id=None,
            field_path="identity.brand_name",
            old_value=None,
            new_value="A",
        )
        row_b, _ = repo.upsert_idempotent(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            message_id=msg_id,
            domain="brand",
            entity_id=None,
            field_path="identity.tagline",
            old_value=None,
            new_value="B",
        )
        db.commit()

        assert row_a.id != row_b.id
        assert row_a.field_path == "identity.brand_name"
        assert row_b.field_path == "identity.tagline"
