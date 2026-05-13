"""Document tools — let the LLM read the content of an uploaded asset.

# [COPILOT-READ-DOCUMENT] → docs/domains/copilot/asset-lifecycle.md

Rationale:
* Eager inline injection in the orchestrator burns tokens even when the
  user didn't need the content. It also re-parses on every turn.
* A lazy tool lets the LLM decide when to look at the file. The cost of
  reading is paid once per asset (``AssetExtractionService``) and the
  tool simply serves the persisted text.

The tool works for both ``document`` (PDF/DOCX/TXT/MD) and ``audio``
assets. For audio, the extracted text is the transcript produced at
upload time.

System-prompt guidance (injected via skill loader):
    Si el usuario adjuntó un documento o audio y necesitas su contenido,
    llama ``read_document`` con el ``asset_id`` del bloque y, si corresponde,
    una ``query`` para buscar dentro. NUNCA inventes contenido de documentos
    que no has leído con la tool.
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING
from uuid import UUID

import structlog
from langchain_core.tools import tool
from luana_core_assets.application.asset_extraction_service import (
    AssetExtractionService,
)
from luana_core_assets.domain.enums import ExtractionStatus
from luana_core_assets.infrastructure.repositories.asset_repository import (
    AssetRepository,
)
from luana_core_platform.core.context import get_tenant_id
from luana_core_platform.core.database import SessionLocal

if TYPE_CHECKING:
    from luana_core_assets.domain.entity import Asset

logger = structlog.get_logger()

# Payload size caps — kept small because tool responses are re-ingested
# into the LLM context window.
FULL_TEXT_MAX_CHARS = 6_000
FRAGMENT_CHARS = 1_200
FRAGMENT_CONTEXT_BEFORE = 300
FRAGMENT_CONTEXT_AFTER = 900


def _select_fragment(text: str, query: str) -> tuple[str, bool]:
    """Return a fragment around the first match of ``query`` in ``text``.

    Falls back to the document head when no term matches. The boolean
    flag tells the caller whether a real match drove the slice.
    """
    if not text:
        return "", False
    haystack = text.lower()
    tokens = [t for t in re.split(r"\W+", query.lower()) if t]
    best_idx: int | None = None
    for token in tokens:
        idx = haystack.find(token)
        if idx != -1 and (best_idx is None or idx < best_idx):
            best_idx = idx
    if best_idx is None:
        return text[:FRAGMENT_CHARS], False
    start = max(0, best_idx - FRAGMENT_CONTEXT_BEFORE)
    end = min(len(text), best_idx + FRAGMENT_CONTEXT_AFTER)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return f"{prefix}{text[start:end]}{suffix}", True


def _build_response(
    asset: Asset,
    *,
    query: str | None,
) -> dict[str, object]:
    """Shape the tool response given an extracted asset."""
    extracted = asset.extracted_text or ""
    if not extracted:
        return {
            "asset_id": str(asset.id),
            "filename": asset.filename,
            "content": "",
            "summary": asset.extracted_summary,
            "status": asset.extraction_status,
            "note": ("El documento no tiene texto extraído. Pide al usuario re-subirlo o usar un formato soportado."),
        }

    if query:
        fragment, matched = _select_fragment(extracted, query)
        return {
            "asset_id": str(asset.id),
            "filename": asset.filename,
            "mime": asset.mime_type,
            "summary": asset.extracted_summary,
            "content": fragment,
            "fragment_matched": matched,
            "total_chars": len(extracted),
            "truncated": len(extracted) > len(fragment),
        }

    # No query: return full text capped at FULL_TEXT_MAX_CHARS.
    truncated = len(extracted) > FULL_TEXT_MAX_CHARS
    body = extracted[:FULL_TEXT_MAX_CHARS]
    if truncated:
        body = body.rsplit(" ", 1)[0] + "…"
    return {
        "asset_id": str(asset.id),
        "filename": asset.filename,
        "mime": asset.mime_type,
        "summary": asset.extracted_summary,
        "content": body,
        "total_chars": len(extracted),
        "truncated": truncated,
    }


@tool
def read_document(asset_id: str, query: str | None = None) -> str:
    """Lee el contenido de un documento o audio previamente adjuntado.

    Args:
        asset_id: UUID del asset (campo ``asset_id`` del bloque ``document`` o ``audio``).
        query: Consulta opcional. Cuando se da, la tool devuelve un fragmento relevante
               + resumen. Sin query, devuelve el texto completo (o truncado si el doc
               es grande).

    Returns:
        JSON con ``asset_id``, ``filename``, ``content``, ``summary``, ``truncated``
        y ``fragment_matched`` (cuando hay ``query``). Si algo falla, devuelve
        ``{"error": "..."}``.

    """
    tenant_id = get_tenant_id()
    if not tenant_id:
        logger.warning("read_document_no_tenant_context")
        return json.dumps({"error": "No se pudo determinar el contexto del tenant."})

    try:
        parsed_asset_id = UUID(asset_id)
    except (ValueError, TypeError):
        return json.dumps({"error": f"asset_id inválido: {asset_id}"})

    try:
        with SessionLocal() as db:
            repo = AssetRepository(db)
            asset = repo.get_by_id(parsed_asset_id, tenant_id=tenant_id)
            if asset is None:
                return json.dumps(
                    {"error": "Asset no encontrado para este tenant."},
                )

            # Ensure extracted — idempotent no-op if already done.
            if asset.extraction_status != ExtractionStatus.EXTRACTED.value:
                service = AssetExtractionService(db)
                refreshed = service.ensure_extracted(
                    parsed_asset_id,
                    tenant_id=tenant_id,
                )
                if refreshed is not None:
                    asset = refreshed

            return json.dumps(_build_response(asset, query=query), ensure_ascii=False)
    except Exception as exc:
        logger.exception("read_document_failed", asset_id=asset_id)
        return json.dumps({"error": f"Error leyendo documento: {exc!s}"})


DOCUMENT_TOOLS = [read_document]
