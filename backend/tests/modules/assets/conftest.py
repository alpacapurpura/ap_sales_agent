"""Fixtures for assets module tests."""

import uuid

import pytest

from luana_core_assets.domain.enums import AssetStatus, AssetType, StorageProvider
from luana_core_assets.infrastructure.models.asset_model import AssetModel


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
