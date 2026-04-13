"""Tests for UserTenantRepository — get_tenants_for_user, tenant isolation."""

import uuid

from src.modules.iam.domain.tenant import Tenant
from src.modules.iam.infrastructure.repositories.user_tenant_repository import (
    UserTenantRepository,
)


class TestUserTenantRepository:
    def test_get_tenants_for_user_returns_linked_tenant(
        self,
        db,
        seed_user_tenant_link,
        user_id,
    ):
        repo = UserTenantRepository(db)
        results = repo.get_tenants_for_user(user_id)
        assert len(results) == 1
        tenant, role = results[0]
        assert isinstance(tenant, Tenant)
        assert role == "admin"

    def test_get_tenants_for_user_returns_correct_tenant(
        self,
        db,
        seed_user_tenant_link,
        user_id,
        tenant_id,
    ):
        repo = UserTenantRepository(db)
        results = repo.get_tenants_for_user(user_id)
        assert len(results) == 1
        tenant, _ = results[0]
        assert tenant.id == tenant_id

    def test_get_tenants_for_user_no_links_returns_empty(self, db):
        """A user with no tenant links gets an empty list."""
        repo = UserTenantRepository(db)
        results = repo.get_tenants_for_user(uuid.uuid4())
        assert results == []

    def test_get_tenants_for_user_only_active_links(
        self,
        db,
        seed_user,
        seed_tenant,
        user_id,
        tenant_id,
    ):
        """Inactive user-tenant links must be excluded."""
        from src.modules.iam.infrastructure.models.user_tenant_model import (
            UserTenantModel,
        )

        inactive_link = UserTenantModel(
            user_id=user_id,
            tenant_id=tenant_id,
            role="member",
            is_active=False,
        )
        db.add(inactive_link)
        db.commit()

        repo = UserTenantRepository(db)
        results = repo.get_tenants_for_user(user_id)
        # No active links were created, so result must be empty
        assert results == []

    def test_get_tenants_for_user_only_active_tenants(
        self,
        db,
        seed_user,
        user_id,
        tenant_id,
    ):
        """Links to inactive tenants must be excluded."""
        from src.modules.iam.infrastructure.models.user_tenant_model import (
            UserTenantModel,
        )
        from tests.factories import TenantFactory

        inactive_tenant = TenantFactory.build(
            id=tenant_id,
            name="Inactive Tenant",
            slug="inactive-tenant-repo",
            is_active=False,
            config_json={},
        )
        db.add(inactive_tenant)
        db.flush()

        link = UserTenantModel(
            user_id=user_id,
            tenant_id=tenant_id,
            role="admin",
            is_active=True,
        )
        db.add(link)
        db.commit()

        repo = UserTenantRepository(db)
        results = repo.get_tenants_for_user(user_id)
        assert results == []

    def test_returns_domain_entities(self, db, seed_user_tenant_link, user_id):
        repo = UserTenantRepository(db)
        results = repo.get_tenants_for_user(user_id)
        for tenant, role in results:
            assert isinstance(tenant, Tenant)
            assert isinstance(role, str)
