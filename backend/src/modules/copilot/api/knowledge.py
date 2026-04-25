"""Legacy tenant knowledge ingest endpoints — retired in F10.

Pre-F10 the copilot exposed ``POST /api/v1/copilot/ingest`` so any tenant
could push their own documents into ``copilot_knowledge`` (per-tenant
filter). The corpus is now globally curated by Nicolify staff into
``nicolify_marketing_kb`` (tenant-agnostic) and ingestion happens through
the Streamlit admin only.

Every endpoint below returns **HTTP 410 Gone** with a clear migration
message. We keep the routes (instead of deleting them outright) so any
forgotten frontend caller surfaces a loud error instead of a silent 404.

[COPILOT-MARKETING-KB-F10]
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter()


class GoneResponse(BaseModel):
    """Standard response model for retired endpoints."""

    detail: str
    migration_hint: str


_GONE_DETAIL = (
    "El ingest de documentos por tenant fue retirado. "
    "La base de conocimiento de marketing es ahora curada por Nicolify "
    "(colección 'nicolify_marketing_kb') y se administra desde el panel interno."
)
_GONE_MIGRATION_HINT = (
    "Si necesitas que tu equipo cargue material propio, escríbenos: "
    "publicamos un proceso de revisión + ingesta supervisada en el roadmap."
)


def _gone() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_410_GONE,
        detail={"detail": _GONE_DETAIL, "migration_hint": _GONE_MIGRATION_HINT},
    )


@router.post("/ingest", status_code=status.HTTP_410_GONE)
async def ingest_document() -> GoneResponse:  # pragma: no cover - exception path
    """Retired in F10. See ``GoneResponse.migration_hint``."""
    raise _gone()


@router.get("/search", status_code=status.HTTP_410_GONE)
async def search_knowledge() -> GoneResponse:  # pragma: no cover - exception path
    """Retired in F10. Use the ``knowledge_search`` tool from the copilot chat."""
    raise _gone()


@router.delete("/{document_id}", status_code=status.HTTP_410_GONE)
async def delete_document(document_id: str) -> GoneResponse:
    """Retired in F10. Curated corpus is managed via the Streamlit admin."""
    _ = document_id  # parameter retained for URL parity, unused
    raise _gone()
