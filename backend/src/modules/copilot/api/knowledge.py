"""REST endpoints for copilot knowledge base management."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from src.modules.copilot.api.dto import IngestDocumentResponse, SearchKnowledgeResponse
from src.modules.copilot.application.services.knowledge_ingestion import (
    KnowledgeIngestionService,
)
from src.modules.copilot.infrastructure.knowledge.vector_store import (
    CopilotKnowledgeStore,
)
from src.modules.iam.api.dependencies import get_tenant_context
from src.shared.infrastructure.files.file_parsing_service import FileParsingService

router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    scope: str = "all"
    limit: int = 5


class SearchResult(BaseModel):
    content: str
    score: float
    metadata: dict


@router.post("/ingest", response_model=IngestDocumentResponse)
async def ingest_document(
    file: UploadFile = File(...),
    scope: str = Form("business"),
    source_label: str = Form("upload"),
    tenant_id: UUID | None = Depends(get_tenant_context),
):
    """Ingest a document (PDF/DOCX/TXT/MD) into the knowledge base."""
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")

    # Parse file content
    text = await FileParsingService.parse_file(file)
    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from file")

    service = KnowledgeIngestionService()
    result = service.ingest_document(
        tenant_id=str(tenant_id),
        content=text,
        source=source_label,
        scope=scope,
    )
    return result


@router.get("/search", response_model=SearchKnowledgeResponse)
async def search_knowledge(
    query: str,
    scope: str = "all",
    limit: int = 5,
    tenant_id: UUID | None = Depends(get_tenant_context),
):
    """Search the knowledge base."""
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")

    store = CopilotKnowledgeStore()
    results = store.search(query, str(tenant_id), scope, limit)

    return {
        "results": [
            {
                "content": r.get("text", ""),
                "score": r.get("score", 0),
                "metadata": r.get("meta", {}),
            }
            for r in results
        ]
    }


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    tenant_id: UUID | None = Depends(get_tenant_context),
):
    """Delete a document from the knowledge base."""
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")

    service = KnowledgeIngestionService()
    deleted = service.delete_document(str(tenant_id), document_id)

    if not deleted:
        raise HTTPException(
            status_code=404, detail="Document not found or error deleting"
        )

    return {"deleted": True}
