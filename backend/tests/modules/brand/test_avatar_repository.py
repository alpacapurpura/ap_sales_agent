"""Tests for AvatarRepository -- CRUD + tenant isolation."""

import uuid

from src.modules.brand.domain import Avatar
from src.modules.brand.infrastructure.repositories.avatar_repository import (
    AvatarRepository,
)
from tests.modules.conftest import TENANT_A, TENANT_B


class TestAvatarRepository:
    def test_create_and_retrieve(self, db, sample_avatar):
        repo = AvatarRepository(db)
        created = repo.create(sample_avatar)
        assert created.name == "Ideal Customer"

        retrieved = repo.get_by_id(created.id)
        assert retrieved is not None
        assert retrieved.name == "Ideal Customer"

    def test_get_by_tenant(self, db, sample_avatar):
        repo = AvatarRepository(db)
        repo.create(sample_avatar)

        results = repo.get_by_tenant(TENANT_A)
        assert len(results) >= 1
        assert all(str(a.tenant_id) == str(TENANT_A) for a in results)

    def test_tenant_isolation(self, db, sample_avatar):
        repo = AvatarRepository(db)
        repo.create(sample_avatar)

        results = repo.get_by_tenant(TENANT_B)
        assert len(results) == 0

    def test_scope_filter(self, db, tenant_id, user_id):
        repo = AvatarRepository(db)
        global_av = Avatar(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            name="Global",
            scope="GLOBAL",
            is_default=False,
        )
        offer_av = Avatar(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            name="Offer",
            scope="OFFER",
            is_default=False,
        )
        repo.create(global_av)
        repo.create(offer_av)

        global_results = repo.get_by_tenant(tenant_id, scope="GLOBAL")
        assert all(a.scope == "GLOBAL" for a in global_results)

    def test_update(self, db, sample_avatar):
        repo = AvatarRepository(db)
        created = repo.create(sample_avatar)

        updated = repo.update(created.id, {"name": "Updated Name"})
        assert updated is not None
        assert updated.name == "Updated Name"

    def test_update_nonexistent(self, db):
        repo = AvatarRepository(db)
        result = repo.update(uuid.uuid4(), {"name": "X"})
        assert result is None

    def test_delete(self, db, sample_avatar):
        repo = AvatarRepository(db)
        created = repo.create(sample_avatar)

        assert repo.delete(created.id) is True
        assert repo.get_by_id(created.id) is None

    def test_delete_nonexistent(self, db):
        repo = AvatarRepository(db)
        assert repo.delete(uuid.uuid4()) is False

    def test_set_global_default(self, db, tenant_id, user_id):
        repo = AvatarRepository(db)
        a1 = Avatar(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            name="A1",
            scope="GLOBAL",
            is_default=True,
        )
        a2 = Avatar(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            name="A2",
            scope="GLOBAL",
            is_default=False,
        )
        repo.create(a1)
        repo.create(a2)

        result = repo.set_global_default(tenant_id, a2.id)
        assert result is not None
        assert result.is_default is True

        # Verify a1 is no longer default
        a1_check = repo.get_by_id(a1.id)
        assert a1_check.is_default is False
