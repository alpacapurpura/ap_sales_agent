"""Tests for AssetsService — upload, list, and delete with mocked storage."""

import io
import uuid
from unittest.mock import MagicMock, patch

from luana_core_assets.application.assets_service import AssetsService
from luana_core_assets.domain.entity import Asset
from luana_core_assets.domain.enums import AssetStatus, AssetType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_service(db, storage_mock):
    """Construct AssetsService with the real repo but a mock storage strategy."""
    with patch(
        "luana_core_assets.application.assets_service.get_storage_strategy",
        return_value=storage_mock,
    ):
        svc = AssetsService(db)
    return svc


def _make_storage_mock(
    storage_path="/tmp/fake/logo.png",
    public_url="/static/uploads/fake/logo.png",
):
    mock = MagicMock()
    mock.save.return_value = (storage_path, public_url)
    mock.delete.return_value = True
    return mock


# ---------------------------------------------------------------------------
# upload_asset
# ---------------------------------------------------------------------------


class TestUploadAsset:
    def test_upload_creates_asset_record(self, db, seed_tenant, tenant_id):
        storage = _make_storage_mock()
        svc = _make_service(db, storage)

        file_obj = io.BytesIO(b"fake image data")
        asset = svc.upload_asset(
            tenant_id=tenant_id,
            file_obj=file_obj,
            filename="logo.png",
            mime_type="image/png",
        )

        assert isinstance(asset, Asset)
        assert asset.tenant_id == tenant_id
        assert asset.filename == "logo.png"
        assert asset.type == AssetType.IMAGE.value

    def test_upload_calls_storage_save(self, db, seed_tenant, tenant_id):
        storage = _make_storage_mock()
        svc = _make_service(db, storage)

        file_obj = io.BytesIO(b"data")
        svc.upload_asset(
            tenant_id=tenant_id,
            file_obj=file_obj,
            filename="vid.mp4",
            mime_type="video/mp4",
        )

        assert storage.save.called

    def test_upload_detects_mime_from_filename_when_none_given(
        self,
        db,
        seed_tenant,
        tenant_id,
    ):
        storage = _make_storage_mock()
        svc = _make_service(db, storage)

        file_obj = io.BytesIO(b"data")
        asset = svc.upload_asset(
            tenant_id=tenant_id,
            file_obj=file_obj,
            filename="photo.jpeg",
        )

        assert asset.type == AssetType.IMAGE.value

    def test_upload_stores_user_description(self, db, seed_tenant, tenant_id):
        storage = _make_storage_mock()
        svc = _make_service(db, storage)

        file_obj = io.BytesIO(b"data")
        asset = svc.upload_asset(
            tenant_id=tenant_id,
            file_obj=file_obj,
            filename="doc.pdf",
            mime_type="application/pdf",
            description="My important PDF",
        )

        assert asset.user_description == "My important PDF"

    def test_upload_initial_status_is_processing(self, db, seed_tenant, tenant_id):
        storage = _make_storage_mock()
        svc = _make_service(db, storage)

        file_obj = io.BytesIO(b"data")
        asset = svc.upload_asset(
            tenant_id=tenant_id,
            file_obj=file_obj,
            filename="img.png",
            mime_type="image/png",
        )

        assert asset.status == AssetStatus.PROCESSING.value


# ---------------------------------------------------------------------------
# list_assets
# ---------------------------------------------------------------------------


class TestListAssets:
    def test_list_assets_returns_own_assets(self, db, seed_tenant, tenant_id):
        storage = _make_storage_mock()
        svc = _make_service(db, storage)

        svc.upload_asset(
            tenant_id=tenant_id,
            file_obj=io.BytesIO(b"a"),
            filename="a.png",
            mime_type="image/png",
        )
        svc.upload_asset(
            tenant_id=tenant_id,
            file_obj=io.BytesIO(b"b"),
            filename="b.png",
            mime_type="image/png",
        )

        results = svc.list_assets(tenant_id)
        assert len(results) == 2

    def test_list_assets_tenant_isolation(
        self,
        db,
        seed_tenant,
        seed_other_tenant,
        tenant_id,
        other_tenant_id,
    ):
        storage = _make_storage_mock()
        svc = _make_service(db, storage)

        svc.upload_asset(
            tenant_id=tenant_id,
            file_obj=io.BytesIO(b"a"),
            filename="a.png",
            mime_type="image/png",
        )

        results_b = svc.list_assets(other_tenant_id)
        assert results_b == []

    def test_list_assets_filters_by_type(self, db, seed_tenant, tenant_id):
        storage = _make_storage_mock()
        svc = _make_service(db, storage)

        svc.upload_asset(
            tenant_id=tenant_id,
            file_obj=io.BytesIO(b"i"),
            filename="img.png",
            mime_type="image/png",
        )
        svc.upload_asset(
            tenant_id=tenant_id,
            file_obj=io.BytesIO(b"d"),
            filename="doc.pdf",
            mime_type="application/pdf",
        )

        images = svc.list_assets(tenant_id, asset_type=AssetType.IMAGE.value)
        assert len(images) == 1
        assert images[0].filename == "img.png"


# ---------------------------------------------------------------------------
# delete_asset
# ---------------------------------------------------------------------------


class TestDeleteAsset:
    def test_delete_asset_removes_record(self, db, seed_tenant, tenant_id):
        storage = _make_storage_mock()
        svc = _make_service(db, storage)

        asset = svc.upload_asset(
            tenant_id=tenant_id,
            file_obj=io.BytesIO(b"x"),
            filename="x.png",
            mime_type="image/png",
        )
        result = svc.delete_asset(tenant_id=tenant_id, asset_id=asset.id)

        assert result is True
        remaining = svc.list_assets(tenant_id)
        assert all(a.id != asset.id for a in remaining)

    def test_delete_asset_calls_storage_delete(self, db, seed_tenant, tenant_id):
        storage = _make_storage_mock()
        svc = _make_service(db, storage)

        asset = svc.upload_asset(
            tenant_id=tenant_id,
            file_obj=io.BytesIO(b"x"),
            filename="x.png",
            mime_type="image/png",
        )
        svc.delete_asset(tenant_id=tenant_id, asset_id=asset.id)

        assert storage.delete.called

    def test_delete_asset_wrong_tenant_returns_false(
        self,
        db,
        seed_tenant,
        seed_other_tenant,
        tenant_id,
        other_tenant_id,
    ):
        """Tenant B must not be able to delete tenant A's asset."""
        storage = _make_storage_mock()
        svc = _make_service(db, storage)

        asset = svc.upload_asset(
            tenant_id=tenant_id,
            file_obj=io.BytesIO(b"x"),
            filename="x.png",
            mime_type="image/png",
        )
        result = svc.delete_asset(tenant_id=other_tenant_id, asset_id=asset.id)

        assert result is False

    def test_delete_asset_nonexistent_returns_false(self, db, seed_tenant, tenant_id):
        storage = _make_storage_mock()
        svc = _make_service(db, storage)

        result = svc.delete_asset(tenant_id=tenant_id, asset_id=uuid.uuid4())
        assert result is False
