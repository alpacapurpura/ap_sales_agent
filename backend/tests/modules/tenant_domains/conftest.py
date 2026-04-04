import uuid
import pytest

from tests.factories import TenantFactory
from src.modules.tenant_domains.infrastructure.models.tenant_domain_model import TenantDomainModel  # noqa: F401

TENANT_A = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")
TENANT_B = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")


@pytest.fixture
def tenant_id():
    return TENANT_A


@pytest.fixture
def other_tenant_id():
    return TENANT_B


@pytest.fixture
def seed_tenant(db, tenant_id):
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
    tenant = TenantFactory.build(
        id=other_tenant_id,
        name="Other Tenant",
        slug="other-tenant",
        config_json={},
    )
    db.add(tenant)
    db.commit()
    return tenant


@pytest.fixture
def sample_domain_model(db, tenant_id):
    """Insert a TenantDomainModel row directly (bypasses service)."""
    model = TenantDomainModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        hostname="shop.example.com",
        domain_type="custom",
        status="pending_verification",
        is_primary=False,
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return model
