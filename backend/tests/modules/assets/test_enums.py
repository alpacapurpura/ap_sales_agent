"""Tests for assets module enums — value correctness and string behaviour."""

from src.modules.assets.domain.enums import AssetStatus, AssetType, StorageProvider


class TestAssetType:
    def test_asset_type_values(self):
        assert AssetType.IMAGE.value == "IMAGE"
        assert AssetType.VIDEO.value == "VIDEO"
        assert AssetType.AUDIO.value == "AUDIO"
        assert AssetType.DOCUMENT.value == "DOCUMENT"

    def test_asset_type_is_str_enum(self):
        """AssetType members should behave as plain strings via equality."""
        assert AssetType.IMAGE == "IMAGE"
        assert AssetType.VIDEO.value == "VIDEO"

    def test_asset_type_all_members(self):
        members = {m.value for m in AssetType}
        assert members == {"IMAGE", "VIDEO", "AUDIO", "DOCUMENT"}


class TestAssetStatus:
    def test_asset_status_values(self):
        assert AssetStatus.PROCESSING.value == "processing"
        assert AssetStatus.COMPLETED.value == "completed"
        assert AssetStatus.FAILED.value == "failed"

    def test_asset_status_is_str_enum(self):
        assert AssetStatus.COMPLETED == "completed"


class TestStorageProvider:
    def test_storage_provider_values(self):
        assert StorageProvider.LOCAL.value == "LOCAL"
        assert StorageProvider.S3.value == "S3"
        assert StorageProvider.R2.value == "R2"

    def test_storage_provider_all_members(self):
        members = {m.value for m in StorageProvider}
        assert members == {"LOCAL", "S3", "R2"}
