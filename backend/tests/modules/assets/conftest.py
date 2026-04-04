"""Fixtures for assets module tests."""
import uuid
import pytest

from tests.factories import TenantFactory
from src.modules.assets.infrastructure.models.asset_model import AssetModel  # noqa: F401 — ensures table is registered
from src.modules.assets.domain.enums import AssetType, AssetStatus, StorageProvider

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
    """Insert TenantModel row so FK constraint on assets.tenant_id is satisfied."""
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
    """Insert a second TenantModel row for isolation tests."""
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
def sample_asset(db, seed_tenant, tenant_id):
    """Persist an AssetModel row and return it."""
    asset = AssetModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        type=AssetType.IMAGE.value,
        filename="logo.png",
        mime_type="image/png",
        storage_provider=StorageProvider.LOCAL.value,
        storage_path="/tmp/assets/logo.png",
        public_url="/static/uploads/logo.png",
        status=AssetStatus.COMPLETED.value,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset
