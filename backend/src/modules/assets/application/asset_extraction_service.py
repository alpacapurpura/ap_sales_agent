"""Text extraction pipeline for assets.

Converts binary uploads (PDF/DOCX/TXT/MD) and audio transcripts into
``extracted_text`` + ``extracted_summary`` persisted on the asset row.
Runs exactly once per asset (idempotent) and reports progress via the
``extraction_status`` column.

Downstream consumers (copilot ``read_document`` tool, RAG indexing,
sales_agent attachments) key off this state instead of re-parsing bytes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from src.modules.assets.domain.enums import AssetType, ExtractionStatus
from src.modules.assets.infrastructure.repositories.asset_repository import (
    AssetRepository,
)
from src.modules.assets.infrastructure.storage import get_storage_strategy
from src.shared.domain.datetime_utils import utc_now
from src.shared.infrastructure.files.file_parsing_service import FileParsingService

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

    from src.modules.assets.domain.entity import Asset

logger = structlog.get_logger()

# Upper bound for persisted text — protects DB from pathological uploads.
MAX_EXTRACTED_CHARS = 200_000

# Summary length target (DB column caps at 500).
SUMMARY_MAX_CHARS = 480

_DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class AssetExtractionService:
    """Populate ``extracted_text`` / ``extracted_summary`` for an asset."""

    def __init__(self, db: Session) -> None:
        """Initialize."""
        self.db = db
        self.repo = AssetRepository(db)
        self.storage = get_storage_strategy()

    # ── Public API ────────────────────────────────────────────────────────

    def ensure_extracted(self, asset_id: UUID, *, tenant_id: UUID) -> Asset | None:
        """Extract text+summary for ``asset_id`` once; no-op if already done.

        Returns the updated asset, or ``None`` if not found under ``tenant_id``.
        Never raises on parser errors — they are caught and recorded in
        ``extraction_status`` / ``extraction_error``.
        """
        asset = self.repo.get_by_id(asset_id, tenant_id)
        if asset is None:
            return None

        # Idempotent short-circuit.
        if (
            asset.extraction_status
            in (
                ExtractionStatus.EXTRACTED.value,
                ExtractionStatus.SKIPPED.value,
                ExtractionStatus.FAILED.value,
            )
            and asset.extracted_at is not None
        ):
            return asset

        # Non-extractable types short-circuit to SKIPPED — not an error state.
        if asset.type in (AssetType.IMAGE.value, AssetType.VIDEO.value):
            return self.repo.update_partial(
                asset_id,
                tenant_id,
                extraction_status=ExtractionStatus.SKIPPED.value,
                extracted_at=utc_now(),
            )

        # Mark as in-flight so concurrent callers see state progress.
        self.repo.update_partial(
            asset_id,
            tenant_id,
            extraction_status=ExtractionStatus.EXTRACTING.value,
        )
        self.db.commit()

        try:
            text = self._extract_text(asset)
        except Exception as exc:
            logger.exception(
                "asset_extraction_failed",
                asset_id=str(asset_id),
                tenant_id=str(tenant_id),
            )
            updated = self.repo.update_partial(
                asset_id,
                tenant_id,
                extraction_status=ExtractionStatus.FAILED.value,
                extraction_error=str(exc)[:500],
                extracted_at=utc_now(),
            )
            self.db.commit()
            return updated

        trimmed = (text or "").strip()[:MAX_EXTRACTED_CHARS]
        summary = self._summarize(trimmed, asset.filename)

        updated = self.repo.update_partial(
            asset_id,
            tenant_id,
            extracted_text=trimmed or None,
            extracted_summary=summary,
            extraction_status=ExtractionStatus.EXTRACTED.value,
            extraction_error=None,
            extracted_at=utc_now(),
        )
        self.db.commit()
        return updated

    # ── Helpers ───────────────────────────────────────────────────────────

    def _extract_text(self, asset: Asset) -> str:
        """Route to the right parser based on asset type + mime."""
        if asset.type == AssetType.AUDIO.value:
            transcript = (asset.ai_metadata or {}).get("transcript")
            return str(transcript or "").strip()

        if asset.type != AssetType.DOCUMENT.value:
            return ""

        raw = self._read_bytes(asset)
        return self._parse_document_bytes(
            raw,
            mime=(asset.mime_type or "").lower(),
            filename=asset.filename or "",
        )

    def _read_bytes(self, asset: Asset) -> bytes:
        """Isolated for test mocking; delegates to the active storage backend."""
        return self.storage.get_file_bytes(asset.storage_path)  # type: ignore[arg-type]

    @staticmethod
    def _parse_document_bytes(raw: bytes, *, mime: str, filename: str) -> str:
        """Dispatch to FileParsingService based on mime / extension."""
        lowered = filename.lower()
        if mime == "application/pdf" or lowered.endswith(".pdf"):
            return (FileParsingService.parse_pdf(raw) or "").strip()
        if mime == _DOCX_MIME or lowered.endswith(".docx"):
            return (FileParsingService.parse_docx(raw) or "").strip()
        if lowered.endswith((".txt", ".md")) or mime.startswith("text/"):
            try:
                return raw.decode("utf-8").strip()
            except UnicodeDecodeError:
                return raw.decode("latin-1", errors="replace").strip()
        return ""

    @staticmethod
    def _summarize(text: str, _filename: str | None = None) -> str | None:
        """Cheap heuristic summary — first non-empty sentences up to the cap.

        Deliberately no LLM call here: extraction should be cheap and
        deterministic. A separate worker can enrich the summary with an
        LLM later without changing the contract.
        """
        if not text:
            return None
        compact = " ".join(text.split())
        if len(compact) <= SUMMARY_MAX_CHARS:
            return compact
        truncated = compact[:SUMMARY_MAX_CHARS].rsplit(" ", 1)[0]
        return f"{truncated}…"
