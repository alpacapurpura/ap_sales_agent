"""Document processing service for interview context extraction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import structlog
from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from uuid import UUID

    from fastapi import UploadFile

    from src.shared.application.ai_action_service import AIActionService

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Pydantic model for structured LLM response
# ---------------------------------------------------------------------------


class DocumentExtractionResponse(BaseModel):
    """LLM-generated structured extraction from document text."""

    model_config = ConfigDict(from_attributes=True)

    extracted_fields: dict[str, str] = {}


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class DocumentProcessingResult:
    """Result of processing documents for an interview session."""

    delta: dict[str, str] = field(default_factory=dict)
    summary: str = ""
    source_documents: list[str] = field(default_factory=list)
    fields_extracted: int = 0
    fields_skipped: int = 0


# ---------------------------------------------------------------------------
# File parser protocol (for DI / testing)
# ---------------------------------------------------------------------------


class FileParserProtocol:
    """Protocol for file parsing. Default implementation uses FileParsingService."""

    async def parse_file(self, file: UploadFile) -> str:
        """Parse a file and return its text content."""
        from src.shared.infrastructure.files.file_parsing_service import (
            FileParsingService,
        )

        return await FileParsingService.parse_file(file)


# ---------------------------------------------------------------------------
# DocumentProcessor service
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are a structured data extractor. Given document text and an extraction "
    "template name, extract key-value pairs that match the template's expected fields. "
    "Return ONLY the fields you can confidently extract from the text. "
    "Use dot-notation keys (e.g., 'identity.brand_name', 'positioning.uvp'). "
    "Values should be concise but complete."
)


class DocumentProcessor:
    """Domain-agnostic document processing for interview context."""

    def __init__(
        self,
        ai_service: AIActionService,
        file_parser: FileParserProtocol | None = None,
    ):
        self.ai_service = ai_service
        self.file_parser = file_parser or FileParserProtocol()

    async def process_for_interview(
        self,
        *,
        files: list[UploadFile],
        extraction_template: str,
        existing_mapa: dict[str, str],
        tenant_id: UUID,
    ) -> DocumentProcessingResult:
        """Parse files, extract structured data via LLM, merge into mapa_global.

        Non-empty existing fields are NOT overwritten (skipped).
        """
        combined_text = ""
        source_docs: list[str] = []

        for file in files:
            parsed = await self.file_parser.parse_file(file)
            if parsed:
                doc_name = file.filename or "unknown"
                source_docs.append(doc_name)
                combined_text += f"\n--- {doc_name} ---\n{parsed}\n"

        if not combined_text.strip():
            return DocumentProcessingResult(
                delta={},
                summary="No se pudo extraer texto de los documentos proporcionados.",
                source_documents=source_docs,
                fields_extracted=0,
                fields_skipped=0,
            )

        logger.info(
            "document_extraction_start",
            template=extraction_template,
            doc_count=len(source_docs),
            text_length=len(combined_text),
            tenant_id=str(tenant_id),
        )

        user_prompt = (
            f"Extraction template: {extraction_template}\n\n"
            f"Document text:\n{combined_text}\n\n"
            f"Existing data (do not re-extract these if already filled):\n"
            f"{existing_mapa}"
        )

        extraction = self.ai_service.run_structured_action(
            action_name="document_extraction",
            tenant_id=tenant_id,
            system_prompt=_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=DocumentExtractionResponse,
        )

        raw_delta = extraction.extracted_fields

        # Count skipped fields (existing non-empty values)
        fields_skipped = sum(1 for k in raw_delta if existing_mapa.get(k))
        fields_extracted = len(raw_delta) - fields_skipped

        # Filter out fields that already have values
        filtered_delta = {
            k: v for k, v in raw_delta.items() if not existing_mapa.get(k)
        }

        summary_parts = [
            f"Extraídos {fields_extracted} campos de {len(source_docs)} documento(s)."
        ]
        if fields_skipped:
            summary_parts.append(
                f"{fields_skipped} campos ya tenían valor y no se sobrescribieron."
            )

        logger.info(
            "document_extraction_complete",
            fields_extracted=fields_extracted,
            fields_skipped=fields_skipped,
            source_documents=source_docs,
            tenant_id=str(tenant_id),
        )

        return DocumentProcessingResult(
            delta=filtered_delta,
            summary=" ".join(summary_parts),
            source_documents=source_docs,
            fields_extracted=fields_extracted,
            fields_skipped=fields_skipped,
        )
