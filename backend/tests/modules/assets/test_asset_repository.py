"""Tests for AssetRepository — CRUD, hard delete, and tenant isolation."""

import uuid

from sqlalchemy import select

from src.modules.assets.domain.entity import Asset
from src.modules.assets.domain.enums import AssetStatus, AssetType, StorageProvider
from src.modules.assets.infrastructure.models.asset_model import AssetModel
from src.modules.assets.infrastructure.repositories.asset_repository import (
    AssetRepository,
)


def _make_asset(tenant_id: uuid.UUID, **kwargs) -> Asset:
    """Helper to build a minimal Asset domain entity."""
    defaults = {
        "id": uuid.uuid4(),
        "tenant_id": tenant_id,
        "type": AssetType.IMAGE.value,
        "filename": "test.png",
        "mime_type": "image/png",
        "storage_provider": StorageProvider.LOCAL.value,
        "storage_path": "/tmp/test.png",  # noqa: S108
        "public_url": "/static/uploads/test.png",
        "status": AssetStatus.PROCESSING.value,
    }
    defaults.update(kwargs)
    return Asset(**defaults)


class TestAssetRepositoryCreate:
    def test_create_returns_domain_entity(self, db, seed_tenant, tenant_id):
        repo = AssetRepository(db)
        asset = _make_asset(tenant_id)
        result = repo.create(asset)

        assert isinstance(result, Asset)
        assert result.id == asset.id
        assert result.tenant_id == tenant_id
        assert result.filename == "test.png"

    def test_create_persists_to_db(self, db, seed_tenant, tenant_id):
        repo = AssetRepository(db)
        asset = _make_asset(tenant_id)
        repo.create(asset)

        row = db.execute(
            select(AssetModel).where(AssetModel.id == asset.id)
        ).scalar_one_or_none()
        assert row is not None
        assert row.filename == "test.png"


class TestAssetRepositoryGetById:
    def test_get_by_id_returns_asset(self, db, sample_asset, tenant_id):
        repo = AssetRepository(db)
        result = repo.get_by_id(sample_asset.id, tenant_id)

        assert result is not None
        assert result.id == sample_asset.id

    def test_get_by_id_filters_by_tenant(
        self, db, sample_asset, seed_other_tenant, other_tenant_id
    ):
        """Must return None if the asset belongs to a different tenant."""
        repo = AssetRepository(db)
        # Should NOT find it when searching with wrong tenant_id
        # Note: currently it ignores tenant_id because the parameter doesn't exist yet,
        # so this test will fail to compile/run once we add the parameter,
        # but for now we'll write it as it SHOULD be.
        result = repo.get_by_id(sample_asset.id, tenant_id=other_tenant_id)
        assert result is None

    def test_get_by_id_nonexistent_returns_none(self, db, seed_tenant, tenant_id):
        repo = AssetRepository(db)
        result = repo.get_by_id(uuid.uuid4(), tenant_id)
        assert result is None


class TestAssetRepositoryListByTenant:
    def test_list_by_tenant_returns_own_assets(self, db, seed_tenant, tenant_id):
        repo = AssetRepository(db)
        repo.create(_make_asset(tenant_id, filename="a.png"))
        repo.create(_make_asset(tenant_id, filename="b.png"))

        results = repo.list_by_tenant(tenant_id)
        assert len(results) == 2

    def test_list_by_tenant_filters_by_type(self, db, seed_tenant, tenant_id):
        repo = AssetRepository(db)
        repo.create(
            _make_asset(tenant_id, filename="image.png", type=AssetType.IMAGE.value)
        )
        repo.create(
            _make_asset(tenant_id, filename="doc.pdf", type=AssetType.DOCUMENT.value)
        )

        images = repo.list_by_tenant(tenant_id, asset_type=AssetType.IMAGE.value)
        assert len(images) == 1
        assert images[0].filename == "image.png"

    def test_list_by_tenant_isolation(
        self, db, seed_tenant, seed_other_tenant, tenant_id, other_tenant_id
    ):
        """Assets from tenant A must not appear in tenant B's list."""
        repo = AssetRepository(db)
        repo.create(_make_asset(tenant_id))

        results_b = repo.list_by_tenant(other_tenant_id)
        assert results_b == []


class TestAssetRepositoryDelete:
    def test_delete_returns_true_on_success(self, db, sample_asset):
        repo = AssetRepository(db)
        result = repo.delete(sample_asset.id)
        assert result is True

    def test_delete_soft_sets_deleted_at(self, db, sample_asset):
        """Soft delete: the DB row must have deleted_at set after deletion."""
        repo = AssetRepository(db)
        repo.delete(sample_asset.id)

        row = db.execute(
            select(AssetModel).where(AssetModel.id == sample_asset.id)
        ).scalar_one_or_none()
        assert row is not None
        assert row.deleted_at is not None

    def test_delete_nonexistent_returns_false(self, db, seed_tenant):
        repo = AssetRepository(db)
        result = repo.delete(uuid.uuid4())
        assert result is False
