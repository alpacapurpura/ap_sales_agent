import pytest
import uuid

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
def sample_tenant(tenant_id: uuid.UUID):
    """Build a TenantModel (not persisted) for use in unit-level tests."""
    return TenantFactory.build(
        id=tenant_id,
        name="Test Tenant",
        slug="test-tenant",
        config_json={"company_name": "TestCo", "agent_persona": "Friendly"},
    )


@pytest.fixture
def seed_tenant(db, tenant_id: uuid.UUID):
    """Persist a TenantModel for TENANT_A to the in-memory SQLite DB."""
    tenant = TenantFactory.build(
        id=tenant_id,
        name="Test Tenant",
        slug="test-tenant",
        config_json={"company_name": "TestCo", "agent_persona": "Friendly"},
    )
    db.add(tenant)
    db.commit()
    return tenant


@pytest.fixture
def seed_other_tenant(db, other_tenant_id: uuid.UUID):
    """Persist a TenantModel for TENANT_B (isolation testing)."""
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
def seed_user(db, user_id: uuid.UUID):
    """Persist a UserModel for USER_A to the in-memory SQLite DB."""
    from src.modules.iam.infrastructure.models.user_model import UserModel

    user = UserModel(
        id=user_id,
        full_name="Alice Test",
        email="alice@example.com",
        clerk_id="clerk_alice_001",
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def seed_user_tenant_link(db, seed_user, seed_tenant, user_id: uuid.UUID, tenant_id: uuid.UUID):
    """Link USER_A to TENANT_A via UserTenantModel."""
    from src.modules.iam.infrastructure.models.user_tenant_model import UserTenantModel

    link = UserTenantModel(
        user_id=user_id,
        tenant_id=tenant_id,
        role="admin",
        is_active=True,
    )
    db.add(link)
    db.commit()
    return link
