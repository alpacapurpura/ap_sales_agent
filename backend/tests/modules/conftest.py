"""Shared fixtures for all module tests.

Centralises tenant/user identity fixtures that were duplicated across 7+ module
conftest files.  Module-specific conftest files can override any fixture here
(pytest resolves the closest fixture first).
"""

import uuid

import pytest

from tests.factories import TenantFactory

TENANT_A = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")
TENANT_B = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")
USER_A = uuid.UUID("cccc0000-0000-0000-0000-000000000001")


@pytest.fixture
def tenant_id() -> uuid.UUID:
    return TENANT_A


@pytest.fixture
def other_tenant_id() -> uuid.UUID:
    return TENANT_B


@pytest.fixture
def user_id() -> uuid.UUID:
    return USER_A


@pytest.fixture
def seed_tenant(db, tenant_id):
    """Persist a TenantModel row so FK constraints are satisfied."""
    tenant = TenantFactory.build(
        id=tenant_id,
        name="Test Tenant",
        slug="test-tenant",
        config_json={},
    )
    db.add(tenant)
    db.commit()
    return tenant


@pytest.fixture
def seed_other_tenant(db, other_tenant_id):
    """Persist a second TenantModel row for tenant isolation tests."""
    tenant = TenantFactory.build(
        id=other_tenant_id,
        name="Other Tenant",
        slug="other-tenant",
        config_json={},
    )
    db.add(tenant)
    db.commit()
    return tenant
