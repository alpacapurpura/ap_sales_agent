"""Tests for conversation security: ownership check + 90-day retention."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.modules.copilot.infrastructure.models.conversation_model import (
    CopilotConversationModel,
)
from src.modules.copilot.infrastructure.repositories.conversation_repository import (
    ConversationRepository,
)


@pytest.fixture
def repo(db):
    return ConversationRepository(db)


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def other_user_id():
    return uuid4()


class TestConversationOwnershipCheck:
    """C2: Verify user_id ownership prevents cross-user access."""

    def test_get_by_id_filters_by_user_id(self, repo, db, tenant_id, user_id, other_user_id):
        """get_by_id must return None when user_id doesn't match."""
        conv = repo.create(
            conversation_id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
        )
        db.commit()

        # Same user: should find it
        found = repo.get_by_id(conv.id, tenant_id, user_id)
        assert found is not None
        assert found.id == conv.id

        # Different user: should NOT find it
        found = repo.get_by_id(conv.id, tenant_id, other_user_id)
        assert found is None

    def test_get_by_id_still_filters_by_tenant_id(self, repo, db, tenant_id, user_id):
        """get_by_id must still reject wrong tenant_id."""
        conv = repo.create(
            conversation_id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
        )
        db.commit()

        wrong_tenant = uuid4()
        found = repo.get_by_id(conv.id, wrong_tenant, user_id)
        assert found is None

    def test_append_messages_respects_ownership(self, repo, db, tenant_id, user_id, other_user_id):
        """append_messages must not modify another user's conversation."""
        conv = repo.create(
            conversation_id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
        )
        db.commit()

        # Other user tries to append — should silently fail (no crash)
        repo.append_messages(
            conv.id,
            tenant_id,
            [{"role": "user", "content": "injected"}],
            user_id=other_user_id,
        )
        db.commit()

        # Original conversation should have no messages added
        original = repo.get_by_id(conv.id, tenant_id, user_id)
        assert original is not None
        assert original.messages == []

    def test_append_messages_works_for_owner(self, repo, db, tenant_id, user_id):
        """append_messages works when user_id matches."""
        conv = repo.create(
            conversation_id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
        )
        db.commit()

        repo.append_messages(
            conv.id,
            tenant_id,
            [{"role": "user", "content": "hello"}],
            user_id=user_id,
        )
        db.commit()

        updated = repo.get_by_id(conv.id, tenant_id, user_id)
        assert len(updated.messages) == 1
        assert updated.messages[0]["content"] == "hello"

    def test_update_title_respects_ownership(self, repo, db, tenant_id, user_id, other_user_id):
        """update_title must not modify another user's conversation."""
        conv = repo.create(
            conversation_id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            title="Original",
        )
        db.commit()

        # Other user tries to update title
        repo.update_title(conv.id, tenant_id, "Hacked", user_id=other_user_id)
        db.commit()

        original = repo.get_by_id(conv.id, tenant_id, user_id)
        assert original.title == "Original"

    def test_update_title_works_for_owner(self, repo, db, tenant_id, user_id):
        """update_title works when user_id matches."""
        conv = repo.create(
            conversation_id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            title="Original",
        )
        db.commit()

        repo.update_title(conv.id, tenant_id, "New Title", user_id=user_id)
        db.commit()

        updated = repo.get_by_id(conv.id, tenant_id, user_id)
        assert updated.title == "New Title"


class TestConversationExpiry:
    """S3: Verify 90-day retention policy."""

    def test_new_conversation_has_expires_at(self, repo, db, tenant_id, user_id):
        """New conversations must get an expires_at ~90 days from now."""
        conv = repo.create(
            conversation_id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
        )
        db.commit()

        assert conv.expires_at is not None
        # SQLite loses timezone info, so compare as naive UTC
        expected = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=90)
        expires_naive = conv.expires_at.replace(tzinfo=None) if conv.expires_at.tzinfo else conv.expires_at
        # Allow 5-second tolerance for test execution time
        assert abs((expires_naive - expected).total_seconds()) < 5

    def test_cleanup_removes_expired_conversations(self, repo, db, tenant_id, user_id):
        """cleanup_expired_conversations soft-deletes expired rows."""
        # Create an expired conversation
        conv_expired = repo.create(
            conversation_id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
        )
        conv_expired.expires_at = datetime.now(UTC) - timedelta(days=1)
        db.flush()

        # Create a valid conversation
        conv_valid = repo.create(
            conversation_id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
        )
        db.commit()

        deleted_count = repo.cleanup_expired_conversations()
        db.commit()

        # Expired one should be soft-deleted (not returned by get_by_id)
        assert deleted_count == 1
        found_expired = repo.get_by_id(conv_expired.id, tenant_id, user_id)
        assert found_expired is None

        # Valid one should still exist
        found_valid = repo.get_by_id(conv_valid.id, tenant_id, user_id)
        assert found_valid is not None

    def test_cleanup_does_not_delete_non_expired(self, repo, db, tenant_id, user_id):
        """cleanup_expired_conversations ignores non-expired rows."""
        conv = repo.create(
            conversation_id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
        )
        db.commit()

        deleted_count = repo.cleanup_expired_conversations()
        db.commit()

        assert deleted_count == 0
        found = repo.get_by_id(conv.id, tenant_id, user_id)
        assert found is not None

    def test_cleanup_uses_soft_delete(self, repo, db, tenant_id, user_id):
        """Expired conversations must be soft-deleted (deleted_at set), not hard-deleted."""
        from sqlalchemy import select

        conv = repo.create(
            conversation_id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
        )
        conv.expires_at = datetime.now(UTC) - timedelta(days=1)
        db.flush()
        db.commit()

        repo.cleanup_expired_conversations()
        db.commit()

        # Query WITHOUT the soft-delete filter to confirm the row still exists
        stmt = select(CopilotConversationModel).where(
            CopilotConversationModel.id == conv.id,
        )
        row = db.execute(stmt).scalars().first()
        assert row is not None
        assert row.deleted_at is not None


class TestAdminMethodsNoUserFilter:
    """Admin methods (list_by_tenant, list_all_paginated, etc.) should NOT require user_id."""

    def test_list_by_tenant_returns_all_users(self, repo, db, tenant_id, user_id, other_user_id):
        """list_by_tenant shows conversations from all users in the tenant."""
        repo.create(conversation_id=uuid4(), tenant_id=tenant_id, user_id=user_id)
        repo.create(conversation_id=uuid4(), tenant_id=tenant_id, user_id=other_user_id)
        db.commit()

        results = repo.list_by_tenant(tenant_id)
        assert len(results) == 2
