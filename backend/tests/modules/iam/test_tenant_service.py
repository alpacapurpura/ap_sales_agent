"""Tests for TenantService — create_tenant (slug conflict), update_tenant."""

import uuid

from luana_core_iam.application.services.tenant_service import TenantService
from luana_core_iam.domain.tenant import Tenant


class TestTenantServiceCreateTenant:
    def test_create_tenant_success(self, db):
        service = TenantService(db)
        tenant, error = service.create_tenant(
            name="New Corp",
            slug="new-corp",
            can_use_keys=False,
            company_name="New Corp Ltd",
            agent_persona="Helpful",
        )
        assert error is None
        assert tenant is not None
        assert tenant.name == "New Corp"
        assert tenant.slug == "new-corp"

    def test_create_tenant_returns_domain_entity(self, db):
        service = TenantService(db)
        tenant, _ = service.create_tenant(
            name="Domain Corp",
            slug="domain-corp",
            can_use_keys=False,
            company_name="DomainCo",
            agent_persona="Pro",
        )
        assert isinstance(tenant, Tenant)

    def test_create_tenant_stores_config(self, db):
        service = TenantService(db)
        tenant, _ = service.create_tenant(
            name="Config Corp",
            slug="config-corp",
            can_use_keys=True,
            company_name="ConfigCo",
            agent_persona="Mentor",
        )
        assert tenant is not None
        assert tenant.config_json.get("company_name") == "ConfigCo"
        assert tenant.config_json.get("agent_persona") == "Mentor"
        assert tenant.can_use_platform_keys is True

    def test_create_tenant_generates_uuid(self, db):
        service = TenantService(db)
        tenant, _ = service.create_tenant(
            name="UUID Corp",
            slug="uuid-corp",
            can_use_keys=False,
            company_name="UUIDCo",
            agent_persona="None",
        )
        assert tenant is not None
        assert tenant.id is not None
        assert isinstance(tenant.id, uuid.UUID)

    def test_create_tenant_slug_conflict_returns_error(self, db, seed_tenant):
        """Duplicate slug must return (None, error_msg) — not raise."""
        service = TenantService(db)
        tenant, error = service.create_tenant(
            name="Dupe",
            slug="test-tenant",  # already exists from seed_tenant
            can_use_keys=False,
            company_name="DupeCo",
            agent_persona="X",
        )
        assert tenant is None
        assert error is not None
        assert "Slug" in error or "slug" in error.lower() or "Error" in error

    def test_create_tenant_is_active_by_default(self, db):
        service = TenantService(db)
        tenant, _ = service.create_tenant(
            name="Active Corp",
            slug="active-corp",
            can_use_keys=False,
            company_name="ActiveCo",
            agent_persona="Friendly",
        )
        assert tenant is not None
        assert tenant.is_active is True


class TestTenantServiceUpdateTenant:
    def test_update_tenant_success(self, db, seed_tenant, tenant_id):
        service = TenantService(db)
        tenant, error = service.update_tenant(
            tenant_id=tenant_id,
            name="Updated Name",
            slug="updated-slug",
            can_use_keys=True,
            is_active=True,
        )
        assert error is None
        assert tenant is not None
        assert tenant.name == "Updated Name"
        assert tenant.slug == "updated-slug"
        assert tenant.can_use_platform_keys is True

    def test_update_tenant_accepts_string_uuid(self, db, seed_tenant, tenant_id):
        """tenant_id can be passed as a string UUID."""
        service = TenantService(db)
        tenant, error = service.update_tenant(
            tenant_id=str(tenant_id),
            name="String UUID Update",
            slug="string-uuid-update",
            can_use_keys=False,
            is_active=True,
        )
        assert error is None
        assert tenant is not None
        assert tenant.name == "String UUID Update"

    def test_update_nonexistent_tenant_returns_error(self, db):
        service = TenantService(db)
        nonexistent = uuid.uuid4()
        tenant, error = service.update_tenant(
            tenant_id=nonexistent,
            name="Ghost",
            slug="ghost-slug",
            can_use_keys=False,
            is_active=True,
        )
        assert tenant is None
        assert error is not None
        assert "no encontrado" in error.lower() or "not found" in error.lower() or "Error" in error

    def test_update_tenant_deactivate(self, db, seed_tenant, tenant_id):
        service = TenantService(db)
        tenant, error = service.update_tenant(
            tenant_id=tenant_id,
            name="Inactive Corp",
            slug="inactive-corp",
            can_use_keys=False,
            is_active=False,
        )
        assert error is None
        assert tenant is not None
        assert tenant.is_active is False

    def test_update_tenant_persists_changes(self, db, seed_tenant, tenant_id):
        """Changes must be readable back from the repository."""
        service = TenantService(db)
        service.update_tenant(
            tenant_id=tenant_id,
            name="Persisted",
            slug="persisted-slug",
            can_use_keys=False,
            is_active=True,
        )
        from luana_core_iam.infrastructure.repositories.tenant_repository import (
            TenantRepository,
        )

        repo = TenantRepository(db)
        fresh = repo.get_by_id(tenant_id)
        assert fresh is not None
        assert fresh.name == "Persisted"
        assert fresh.slug == "persisted-slug"

    def test_get_all_tenants(self, db, seed_tenant, seed_other_tenant):
        service = TenantService(db)
        all_tenants = service.get_all_tenants()
        assert len(all_tenants) >= 2
        slugs = {t.slug for t in all_tenants}
        assert "test-tenant" in slugs
        assert "other-tenant" in slugs


class TestUserService:
    def test_get_user_tenants_returns_linked_tenants(self, db, seed_user_tenant_link, user_id):
        from luana_core_iam.application.services.user_service import UserService

        service = UserService(db)
        tenants = service.get_user_tenants(user_id)
        assert len(tenants) >= 1
        assert tenants[0].slug == "test-tenant"

    def test_get_user_tenants_empty_for_unlinked_user(self, db, seed_user, user_id):
        import uuid

        from luana_core_iam.application.services.user_service import UserService

        service = UserService(db)
        tenants = service.get_user_tenants(uuid.uuid4())
        assert tenants == []

    def test_get_user_tenants_has_role(self, db, seed_user_tenant_link, user_id):
        from luana_core_iam.application.services.user_service import UserService

        service = UserService(db)
        tenants = service.get_user_tenants(user_id)
        assert tenants[0].role == "admin"
