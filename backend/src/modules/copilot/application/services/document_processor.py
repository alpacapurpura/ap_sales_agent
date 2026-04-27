"""Document processing service for interview context extraction.

The pipeline:

1. Caller passes the raw document text plus a ``domain``
   (``brand`` | ``offer`` | ``buyer_persona``).
2. ``ExtractionDomainConfig`` from the registry tells us which Jinja2
   template to render and how strict the response shape is.
3. ``build_field_paths_hint(domain)`` derives the editable surface from the
   shared catalog, so the LLM never has to guess which paths exist.
4. The rendered template + hint are sent to ``AIActionService`` under a
   per-domain ``action_name`` (clean telemetry).
5. The LLM response is parsed into ``DocumentExtractionResponse`` whose
   ``extracted_fields`` accepts strings, lists or nested dicts —
   buyer_persona stores ``pain_points`` as ``list[dict]`` and the schema
   used to be ``dict[str, str]`` only, which is exactly what produced the
   ``Extra data: line N column M`` failures observed in production.
6. Persisters validate the actual shape on persist; this service does not.

# [COPILOT-DOC-EXTRACTION-PIPELINE]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import structlog
from pydantic import BaseModel, ConfigDict

from src.core.enums import ModelRole
from src.modules.copilot.domain.extraction_domain_registry import (
    get_extraction_config,
)
from src.modules.copilot.domain.field_paths_hint import build_field_paths_hint
from src.shared.application.ai_action_service import (
    AIActionPolicy,
    AIModelPolicy,
)
from src.shared.infrastructure.files.file_parsing_service import (
    FileParsingService,
)
from src.shared.infrastructure.prompts.base import prompt_loader

if TYPE_CHECKING:
    from uuid import UUID

    from fastapi import UploadFile

    from src.shared.application.ai_action_service import AIActionService

logger = structlog.get_logger()


# ---------------------------------------------------------------------------
# Pydantic model for structured LLM response
# ---------------------------------------------------------------------------


class DocumentExtractionResponse(BaseModel):
    """LLM-generated structured extraction from document text.

    ``extracted_fields`` accepts heterogeneous values because BuyerPersona
    stores ``pain_points``/``desires``/``objections``/``preferred_channels``
    as arrays of objects, while brand/offer fields are mostly scalars. The
    persister layer is the authoritative validator of per-path shape.
    """

    model_config = ConfigDict(from_attributes=True, extra="ignore")

    extracted_fields: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class DocumentProcessingResult:
    """Result of processing documents for an interview session."""

    delta: dict[str, Any] = field(default_factory=dict)
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
        return await FileParsingService.parse_file(file)


# ---------------------------------------------------------------------------
# DocumentProcessor service
# ---------------------------------------------------------------------------

# Minimal role framing — concrete instructions live in each domain template
# so the prompt stays in sync with the editable catalog. Spanish neutro.
_SYSTEM_PROMPT = (
    "Eres un extractor de datos estructurados para Nicolify. "
    "Sigues las reglas del prompt del usuario al pie de la letra y devuelves "
    "JSON válido sin texto adicional. Si un campo no aparece en el catálogo "
    "que recibes, lo omites en lugar de inventarlo."
)


class DocumentProcessor:
    """Domain-aware document processing for the copilot extract pipeline."""

    def __init__(
        self,
        ai_service: AIActionService,
        file_parser: FileParserProtocol | None = None,
    ) -> None:
        """Initialize with AI service and optional file parser."""
        self.ai_service = ai_service
        self.file_parser = file_parser or FileParserProtocol()

    async def process_files(
        self,
        *,
        files: list[UploadFile],
        domain: str,
        existing_mapa: dict[str, Any],
        tenant_id: UUID,
    ) -> DocumentProcessingResult:
        """Parse uploaded files, extract structured data via LLM, merge into mapa.

        Non-empty existing fields are NOT overwritten (skipped). Thin wrapper
        over ``extract_from_text``: parses the files first, then delegates.
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

        return self.extract_from_text(
            text=combined_text,
            source_documents=source_docs,
            domain=domain,
            existing_mapa=existing_mapa,
            tenant_id=tenant_id,
        )

    def extract_from_text(
        self,
        *,
        text: str,
        source_documents: list[str],
        domain: str,
        existing_mapa: dict[str, Any],
        tenant_id: UUID,
    ) -> DocumentProcessingResult:
        """Run the LLM extraction against already-parsed document text.

        ``domain`` drives template selection, prompt hint, and the per-domain
        ``action_name`` used for tracing.

        Used by the copilot ``extract_document_to_fields`` tool which reads
        pre-extracted text from ``assets.extracted_text`` — no re-parsing on
        every turn.
        """
        combined_text = text.strip()
        if not combined_text:
            return DocumentProcessingResult(
                delta={},
                summary="Documento sin texto extraíble.",
                source_documents=list(source_documents),
                fields_extracted=0,
                fields_skipped=0,
            )

        config = get_extraction_config(domain)
        if config is None:
            logger.warning("document_extraction_unsupported_domain", domain=domain)
            return DocumentProcessingResult(
                delta={},
                summary=f"Dominio '{domain}' no soportado para extracción de documentos.",
                source_documents=list(source_documents),
                fields_extracted=0,
                fields_skipped=0,
            )

        field_paths_hint = build_field_paths_hint(domain)
        existing_repr = _format_existing_for_prompt(existing_mapa)

        try:
            user_prompt = prompt_loader.render(
                config.template_name,
                document_text=combined_text,
                existing_data=existing_repr,
                field_paths_hint=field_paths_hint,
            )
        except Exception:
            # Template missing or render error: bubble up as a clean failure
            # so the tool layer turns it into an actionable card instead of
            # crashing the conversation.
            logger.exception(
                "document_extraction_template_render_failed",
                template=config.template_name,
                domain=domain,
            )
            raise

        action_name = f"{domain}_doc_extraction"
        logger.info(
            "document_extraction_start",
            action_name=action_name,
            template=config.template_name,
            doc_count=len(source_documents),
            text_length=len(combined_text),
            tenant_id=str(tenant_id),
        )

        # Document extraction is structured-JSON parsing — the schema
        # (``DocumentExtractionResponse``) does the heavy lifting, no
        # chain-of-thought required. Routing to the FAST role avoids the
        # reasoning-budget trap (conv ``1ec7e82d``, 2026-04-27, where
        # the default REASONING role on DeepSeek-V4 burned the full
        # ``max_tokens`` cap on internal CoT and emitted empty content)
        # AND saves ~10x cost / ~5x latency. OpenAI Help Center
        # explicitly recommends non-reasoning models for "extractive QA
        # and simple RAG" — this is exactly that.
        extraction = self.ai_service.run_structured_action(
            action_name=action_name,
            tenant_id=tenant_id,
            system_prompt=_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=DocumentExtractionResponse,
            policy=AIActionPolicy(
                model=AIModelPolicy(
                    model_type=ModelRole.FAST,
                    temperature=0,
                    max_output_tokens=2000,
                ),
            ),
        )

        raw_delta = extraction.extracted_fields or {}

        # Skip fields that already have a non-empty value in the existing mapa.
        fields_skipped = sum(1 for k in raw_delta if _has_value(existing_mapa.get(k)))
        filtered_delta = {k: v for k, v in raw_delta.items() if not _has_value(existing_mapa.get(k))}
        fields_extracted = len(filtered_delta)

        summary_parts = [
            f"Extraídos {fields_extracted} campos de {len(source_documents)} documento(s).",
        ]
        if fields_skipped:
            summary_parts.append(
                f"{fields_skipped} campos ya tenían valor y no se sobrescribieron.",
            )

        logger.info(
            "document_extraction_complete",
            action_name=action_name,
            fields_extracted=fields_extracted,
            fields_skipped=fields_skipped,
            source_documents=source_documents,
            tenant_id=str(tenant_id),
        )

        return DocumentProcessingResult(
            delta=filtered_delta,
            summary=" ".join(summary_parts),
            source_documents=list(source_documents),
            fields_extracted=fields_extracted,
            fields_skipped=fields_skipped,
        )


def _has_value(value: Any) -> bool:  # noqa: ANN401 — accepts heterogeneous mapa values
    """True iff the existing-mapa entry should block an overwrite."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list | dict | tuple | set):
        return len(value) > 0
    return True


def _format_existing_for_prompt(existing_mapa: dict[str, Any]) -> str:
    """Render the existing mapa as a compact string for the prompt context."""
    if not existing_mapa:
        return ""
    parts = [f"- {key}: {value!r}" for key, value in existing_mapa.items() if _has_value(value)]
    return "\n".join(parts)
