"""Tests for AssetExtractionService — TDD.

Guarantees:
* Idempotent: never re-parse an already-extracted asset.
* Status transitions are explicit: pending → extracting → extracted/failed/skipped.
* Non-extractable types (image/video) short-circuit to ``skipped``.
* Persisted fields (extracted_text, extracted_summary) match parsed output.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

from src.modules.assets.domain.enums import (
    AssetScope,
    AssetStatus,
    AssetType,
    ExtractionStatus,
    StorageProvider,
)
from src.modules.assets.infrastructure.models.asset_model import AssetModel


def _make_document_asset(db, tenant_id, **overrides) -> AssetModel:
    model = AssetModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        type=AssetType.DOCUMENT.value,
        filename="brief.pdf",
        mime_type="application/pdf",
        storage_provider=StorageProvider.LOCAL.value,
        storage_path="/tmp/assets/brief.pdf",
        public_url="/static/uploads/brief.pdf",
        status=AssetStatus.PROCESSING.value,
        scope=AssetScope.EPHEMERAL.value,
        extraction_status=ExtractionStatus.PENDING.value,
    )
    for key, val in overrides.items():
        setattr(model, key, val)
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


class TestAssetExtractionService:
    def test_extracts_document_text_and_summary(self, db, seed_tenant, tenant_id) -> None:
        """A pending PDF is parsed, persisted, and marked extracted."""
        from src.modules.assets.application.asset_extraction_service import (
            AssetExtractionService,
        )

        asset = _make_document_asset(db, tenant_id)
        fake_text = "Título\n\n" + ("Contenido relevante del brief. " * 20)

        service = AssetExtractionService(db)
        with (
            patch.object(service, "_read_bytes", return_value=b"fake-pdf"),
            patch(
                "src.modules.assets.application.asset_extraction_service.FileParsingService.parse_pdf",
                return_value=fake_text,
            ),
        ):
            result = service.ensure_extracted(asset.id, tenant_id=tenant_id)

        assert result is not None
        assert result.extraction_status == ExtractionStatus.EXTRACTED.value
        assert result.extracted_text == fake_text.strip()
        assert result.extracted_summary  # non-empty
        assert len(result.extracted_summary) <= 500
        assert result.extracted_at is not None

    def test_idempotent_on_already_extracted(self, db, seed_tenant, tenant_id) -> None:
        """A second call on an extracted asset must not re-parse."""
        from src.modules.assets.application.asset_extraction_service import (
            AssetExtractionService,
        )

        asset = _make_document_asset(
            db,
            tenant_id,
            extracted_text="ya extraído",
            extracted_summary="resumen viejo",
            extraction_status=ExtractionStatus.EXTRACTED.value,
        )

        service = AssetExtractionService(db)
        with patch(
            "src.modules.assets.application.asset_extraction_service.FileParsingService.parse_pdf",
        ) as mock_parse:
            result = service.ensure_extracted(asset.id, tenant_id=tenant_id)

        mock_parse.assert_not_called()
        assert result.extracted_text == "ya extraído"

    def test_image_is_skipped(self, db, seed_tenant, tenant_id) -> None:
        """Images have no extractable text — status moves to skipped, not failed."""
        from src.modules.assets.application.asset_extraction_service import (
            AssetExtractionService,
        )

        img = _make_document_asset(
            db,
            tenant_id,
            type=AssetType.IMAGE.value,
            filename="logo.png",
            mime_type="image/png",
        )
        service = AssetExtractionService(db)
        result = service.ensure_extracted(img.id, tenant_id=tenant_id)

        assert result.extraction_status == ExtractionStatus.SKIPPED.value
        assert result.extracted_text is None

    def test_audio_uses_transcript_when_provided(self, db, seed_tenant, tenant_id) -> None:
        """Audio assets' transcript (in ai_metadata) becomes the extracted_text."""
        from src.modules.assets.application.asset_extraction_service import (
            AssetExtractionService,
        )

        audio = _make_document_asset(
            db,
            tenant_id,
            type=AssetType.AUDIO.value,
            filename="memo.webm",
            mime_type="audio/webm",
            ai_metadata={"transcript": "Hola, este es un voice memo para el copilot."},
        )
        service = AssetExtractionService(db)
        result = service.ensure_extracted(audio.id, tenant_id=tenant_id)

        assert result.extraction_status == ExtractionStatus.EXTRACTED.value
        assert "voice memo" in (result.extracted_text or "")

    def test_failure_records_error_and_marks_failed(self, db, seed_tenant, tenant_id) -> None:
        """Parser exceptions flip status to FAILED and save the message."""
        from src.modules.assets.application.asset_extraction_service import (
            AssetExtractionService,
        )

        asset = _make_document_asset(db, tenant_id)
        service = AssetExtractionService(db)

        with (
            patch.object(service, "_read_bytes", side_effect=OSError("disk broken")),
        ):
            result = service.ensure_extracted(asset.id, tenant_id=tenant_id)

        assert result.extraction_status == ExtractionStatus.FAILED.value
        assert "disk broken" in (result.extraction_error or "")

    def test_cross_tenant_returns_none(self, db, seed_tenant, tenant_id) -> None:
        """An asset from another tenant must not be extractable across boundaries."""
        from src.modules.assets.application.asset_extraction_service import (
            AssetExtractionService,
        )

        asset = _make_document_asset(db, tenant_id)
        service = AssetExtractionService(db)
        result = service.ensure_extracted(asset.id, tenant_id=uuid.uuid4())
        assert result is None
