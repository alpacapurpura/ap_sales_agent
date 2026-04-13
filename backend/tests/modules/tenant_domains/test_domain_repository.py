"""Tests for DomainRepositoryImpl — CRUD, soft delete, tenant isolation, hostname uniqueness."""

import uuid

import pytest

from src.modules.tenant_domains.domain.domain_entity import (
    DomainStatus,
    DomainType,
    TenantDomain,
)
from src.modules.tenant_domains.infrastructure.domain_repository_impl import (
    DomainRepositoryImpl,
)


def _make_domain(
    tenant_id: uuid.UUID,
    hostname: str = "shop.example.com",
) -> TenantDomain:
    return TenantDomain(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        hostname=hostname,
        domain_type=DomainType.CUSTOM,
        status=DomainStatus.PENDING_VERIFICATION,
    )


class TestDomainRepositoryCreate:
    def test_create_returns_domain_entity(self, db, tenant_id):
        repo = DomainRepositoryImpl(db)
        domain = _make_domain(tenant_id)
        saved = repo.create(domain)

        assert saved.id == domain.id
        assert saved.tenant_id == tenant_id
        assert saved.hostname == "shop.example.com"
        assert saved.domain_type is DomainType.CUSTOM
        assert saved.status is DomainStatus.PENDING_VERIFICATION

    def test_create_platform_domain(self, db, tenant_id):
        repo = DomainRepositoryImpl(db)
        domain = TenantDomain(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            hostname="myshop.nicolify.com",
            domain_type=DomainType.PLATFORM,
            status=DomainStatus.ACTIVE,
        )
        saved = repo.create(domain)

        assert saved.domain_type is DomainType.PLATFORM
        assert saved.status is DomainStatus.ACTIVE


class TestDomainRepositoryGetById:
    def test_get_by_id_returns_correct_domain(self, db, tenant_id):
        repo = DomainRepositoryImpl(db)
        domain = _make_domain(tenant_id)
        saved = repo.create(domain)

        result = repo.get_by_id(saved.id, tenant_id)
        assert result is not None
        assert result.id == saved.id

    def test_get_by_id_wrong_tenant_returns_none(self, db, tenant_id, other_tenant_id):
        """Tenant isolation: tenant B cannot access tenant A's domain."""
        repo = DomainRepositoryImpl(db)
        saved = repo.create(_make_domain(tenant_id))

        result = repo.get_by_id(saved.id, other_tenant_id)
        assert result is None

    def test_get_by_id_nonexistent_returns_none(self, db, tenant_id):
        repo = DomainRepositoryImpl(db)
        result = repo.get_by_id(uuid.uuid4(), tenant_id)
        assert result is None

    def test_get_by_id_soft_deleted_returns_none(self, db, tenant_id):
        """Soft-deleted domains must not be returned."""
        repo = DomainRepositoryImpl(db)
        saved = repo.create(_make_domain(tenant_id))
        repo.soft_delete(saved.id, tenant_id)

        result = repo.get_by_id(saved.id, tenant_id)
        assert result is None


class TestDomainRepositoryGetByHostname:
    def test_get_by_hostname_returns_domain(self, db, tenant_id):
        repo = DomainRepositoryImpl(db)
        domain = _make_domain(tenant_id, hostname="unique.example.com")
        repo.create(domain)

        result = repo.get_by_hostname("unique.example.com")
        assert result is not None
        assert result.hostname == "unique.example.com"

    def test_get_by_hostname_nonexistent_returns_none(self, db):
        repo = DomainRepositoryImpl(db)
        result = repo.get_by_hostname("notexist.example.com")
        assert result is None

    def test_get_by_hostname_soft_deleted_returns_none(self, db, tenant_id):
        repo = DomainRepositoryImpl(db)
        saved = repo.create(_make_domain(tenant_id, hostname="deleted.example.com"))
        repo.soft_delete(saved.id, tenant_id)

        result = repo.get_by_hostname("deleted.example.com")
        assert result is None


class TestDomainRepositoryListByTenant:
    def test_list_returns_tenant_domains_only(self, db, tenant_id, other_tenant_id):
        """Tenant A's domains are not visible to tenant B query."""
        repo = DomainRepositoryImpl(db)
        repo.create(_make_domain(tenant_id, hostname="a1.example.com"))
        repo.create(_make_domain(tenant_id, hostname="a2.example.com"))
        repo.create(_make_domain(other_tenant_id, hostname="b1.example.com"))

        tenant_a_domains = repo.list_by_tenant(tenant_id)
        tenant_b_domains = repo.list_by_tenant(other_tenant_id)

        assert len(tenant_a_domains) == 2
        assert len(tenant_b_domains) == 1
        hostnames_a = {d.hostname for d in tenant_a_domains}
        assert hostnames_a == {"a1.example.com", "a2.example.com"}

    def test_list_excludes_soft_deleted(self, db, tenant_id):
        repo = DomainRepositoryImpl(db)
        saved = repo.create(_make_domain(tenant_id, hostname="will-delete.example.com"))
        repo.create(_make_domain(tenant_id, hostname="keep.example.com"))
        repo.soft_delete(saved.id, tenant_id)

        results = repo.list_by_tenant(tenant_id)
        hostnames = {d.hostname for d in results}
        assert "will-delete.example.com" not in hostnames
        assert "keep.example.com" in hostnames

    def test_list_empty_returns_empty_list(self, db, tenant_id):
        repo = DomainRepositoryImpl(db)
        results = repo.list_by_tenant(tenant_id)
        assert results == []


class TestDomainRepositoryUpdate:
    def test_update_status(self, db, tenant_id):
        repo = DomainRepositoryImpl(db)
        saved = repo.create(_make_domain(tenant_id))
        saved.status = DomainStatus.ACTIVE
        saved.ssl_status = "active"

        updated = repo.update(saved)
        assert updated.status is DomainStatus.ACTIVE
        assert updated.ssl_status == "active"

    def test_update_nonexistent_raises(self, db, tenant_id):
        repo = DomainRepositoryImpl(db)
        ghost = _make_domain(tenant_id)  # never persisted
        with pytest.raises(ValueError, match="not found"):
            repo.update(ghost)


class TestDomainRepositorySoftDelete:
    def test_soft_delete_hides_domain(self, db, tenant_id):
        repo = DomainRepositoryImpl(db)
        saved = repo.create(_make_domain(tenant_id))

        repo.soft_delete(saved.id, tenant_id)

        result = repo.get_by_id(saved.id, tenant_id)
        assert result is None

    def test_soft_delete_wrong_tenant_is_noop(self, db, tenant_id, other_tenant_id):
        """Soft-deleting with the wrong tenant_id must not affect the original domain."""
        repo = DomainRepositoryImpl(db)
        saved = repo.create(_make_domain(tenant_id))

        repo.soft_delete(saved.id, other_tenant_id)  # wrong tenant — should be no-op

        result = repo.get_by_id(saved.id, tenant_id)
        assert result is not None  # domain is still there

    def test_soft_delete_nonexistent_is_noop(self, db, tenant_id):
        """Deleting a non-existent domain raises no error."""
        repo = DomainRepositoryImpl(db)
        repo.soft_delete(uuid.uuid4(), tenant_id)  # should not raise
