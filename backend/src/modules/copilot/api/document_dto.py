"""DTOs for document processing API endpoints."""

from pydantic import BaseModel, ConfigDict


class DocumentProcessingResponse(BaseModel):
    """Response for POST /{session_id}/documents endpoint."""

    model_config = ConfigDict(from_attributes=True)

    delta: dict[str, str]
    summary: str
    source_documents: list[str]
    fields_extracted: int
    fields_skipped: int
