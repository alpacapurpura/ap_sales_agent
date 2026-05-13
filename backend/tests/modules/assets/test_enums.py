"""Tests for assets module enums — value correctness and string behaviour."""

from luana_core_assets.domain.enums import (
    AssetPurpose,
    AssetScope,
    AssetStatus,
    AssetType,
    ExtractionStatus,
    StorageProvider,
)


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


class TestAssetScope:
    def test_scope_values(self):
        assert AssetScope.EPHEMERAL.value == "ephemeral"
        assert AssetScope.LIBRARY.value == "library"
        assert AssetScope.DELIVERABLE.value == "deliverable"

    def test_scope_all_members(self):
        assert {m.value for m in AssetScope} == {"ephemeral", "library", "deliverable"}


class TestAssetPurpose:
    """Closed taxonomy — adding a purpose requires migration + ADR."""

    def test_purpose_values(self):
        assert AssetPurpose.CONTEXT_EXTRACT.value == "context_extract"
        assert AssetPurpose.VISUAL_REFERENCE.value == "visual_reference"
        assert AssetPurpose.BRAND_ASSET.value == "brand_asset"
        assert AssetPurpose.OFFER_COLLATERAL.value == "offer_collateral"
        assert AssetPurpose.LEGAL_DOC.value == "legal_doc"
        assert AssetPurpose.TESTIMONIAL.value == "testimonial"
        assert AssetPurpose.KNOWLEDGE_SOURCE.value == "knowledge_source"

    def test_purpose_all_members(self):
        """Architecture guard: taxonomy is deliberately bounded."""
        assert {m.value for m in AssetPurpose} == {
            "context_extract",
            "visual_reference",
            "brand_asset",
            "offer_collateral",
            "legal_doc",
            "testimonial",
            "knowledge_source",
        }


class TestExtractionStatus:
    def test_values(self):
        assert ExtractionStatus.PENDING.value == "pending"
        assert ExtractionStatus.EXTRACTING.value == "extracting"
        assert ExtractionStatus.EXTRACTED.value == "extracted"
        assert ExtractionStatus.SKIPPED.value == "skipped"
        assert ExtractionStatus.FAILED.value == "failed"

    def test_all_members(self):
        assert {m.value for m in ExtractionStatus} == {
            "pending",
            "extracting",
            "extracted",
            "skipped",
            "failed",
        }
