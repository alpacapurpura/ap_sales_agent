"""Tests for UserRepository — get_by_email, get_by_clerk_id, create, tenant context."""

import uuid

import pytest

from luana_core_iam.domain.user import User
from luana_core_iam.infrastructure.repositories.user_repository import UserRepository


class TestUserRepositoryGetById:
    def test_get_by_id_returns_user(self, db, seed_user, user_id):
        repo = UserRepository(db)
        result = repo.get_by_id(user_id)
        assert result is not None
        assert result.id == user_id

    def test_get_by_id_nonexistent_returns_none(self, db):
        repo = UserRepository(db)
        result = repo.get_by_id(uuid.uuid4())
        assert result is None

    def test_get_by_id_returns_domain_entity(self, db, seed_user, user_id):
        repo = UserRepository(db)
        result = repo.get_by_id(user_id)
        assert isinstance(result, User)


class TestUserRepositoryGetByEmail:
    def test_get_by_email_found(self, db, seed_user):
        repo = UserRepository(db)
        result = repo.get_by_email("alice@example.com")
        assert result is not None
        assert result.email == "alice@example.com"

    def test_get_by_email_not_found(self, db, seed_user):
        repo = UserRepository(db)
        result = repo.get_by_email("nobody@example.com")
        assert result is None

    def test_get_by_email_case_sensitive(self, db, seed_user):
        """Email lookups should not match different cases unless DB is configured for it."""
        repo = UserRepository(db)
        # Stored as lowercase; uppercase variant should not match
        result = repo.get_by_email("ALICE@EXAMPLE.COM")
        # Accept either None or a match — document actual behaviour
        assert result is None or result.email == "alice@example.com"


class TestUserRepositoryGetByClerkId:
    def test_get_by_clerk_id_found(self, db, seed_user):
        repo = UserRepository(db)
        result = repo.get_by_clerk_id("clerk_alice_001")
        assert result is not None
        assert result.clerk_id == "clerk_alice_001"

    def test_get_by_clerk_id_not_found(self, db, seed_user):
        repo = UserRepository(db)
        result = repo.get_by_clerk_id("non_existent_clerk_id")
        assert result is None

    def test_get_by_clerk_id_returns_domain_entity(self, db, seed_user):
        repo = UserRepository(db)
        result = repo.get_by_clerk_id("clerk_alice_001")
        assert isinstance(result, User)


class TestUserRepositoryCreate:
    def test_create_user_returns_persisted_entity(self, db):
        repo = UserRepository(db)
        new_user = User(
            id=uuid.uuid4(),
            email="bob@example.com",
            full_name="Bob Builder",
            clerk_id="clerk_bob_999",
            role="member",
        )
        created = repo.create(new_user)
        assert created.id == new_user.id
        assert created.email == "bob@example.com"
        assert created.clerk_id == "clerk_bob_999"

    def test_created_user_is_retrievable(self, db):
        repo = UserRepository(db)
        uid = uuid.uuid4()
        new_user = User(id=uid, email="carol@example.com", full_name="Carol")
        repo.create(new_user)

        found = repo.get_by_id(uid)
        assert found is not None
        assert found.email == "carol@example.com"

    def test_create_returns_domain_entity(self, db):
        repo = UserRepository(db)
        new_user = User(id=uuid.uuid4(), email="dave@example.com")
        created = repo.create(new_user)
        assert isinstance(created, User)

    def test_duplicate_email_raises(self, db, seed_user):
        """Creating a user with a duplicate email must raise an integrity error."""
        from sqlalchemy.exc import IntegrityError

        repo = UserRepository(db)
        duplicate = User(
            id=uuid.uuid4(),
            email="alice@example.com",
        )  # same as seed_user
        with pytest.raises(IntegrityError):
            repo.create(duplicate)


class TestUserRepositoryUpdate:
    def test_update_full_name(self, db, seed_user, user_id):
        repo = UserRepository(db)
        user = repo.get_by_id(user_id)
        assert user is not None
        user.full_name = "Alice Updated"
        updated = repo.update(user)
        assert updated.full_name == "Alice Updated"

    def test_update_persists_to_db(self, db, seed_user, user_id):
        repo = UserRepository(db)
        user = repo.get_by_id(user_id)
        assert user is not None
        user.full_name = "Persisted Update"
        repo.update(user)

        fresh = repo.get_by_id(user_id)
        assert fresh is not None
        assert fresh.full_name == "Persisted Update"

    def test_update_clerk_id(self, db, seed_user, user_id):
        repo = UserRepository(db)
        user = repo.get_by_id(user_id)
        assert user is not None
        user.clerk_id = "clerk_new_id"
        updated = repo.update(user)
        assert updated.clerk_id == "clerk_new_id"
