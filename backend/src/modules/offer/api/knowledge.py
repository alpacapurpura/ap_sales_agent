"""Knowledge CRUD endpoints for the offer header Knowledge tab.

Delegates to ``OfferKnowledgeService`` wired with in-process stubs for
file storage and the RAG indexer. The real Qdrant pipeline will replace
the indexer stub without touching this router.
"""

from io import BytesIO
from typing import Annotated, BinaryIO
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.offer.api.dto.knowledge_dtos import (
    KnowledgeListResponse,
    KnowledgeSourceResponse,
    KnowledgeUrlRequest,
)
from src.modules.offer.application.ports import (
    IFileStoragePort,
    IRAGIndexerPort,
)
from src.modules.offer.application.services.offer_knowledge_service import (
    OfferKnowledgeService,
)
from src.modules.offer.domain.enums import KnowledgeSourceType
from src.modules.offer.domain.exceptions import KnowledgeSourceNotFoundError
from src.modules.offer.domain.knowledge_source import KnowledgeSource
from src.modules.offer.infrastructure.repositories.knowledge_source_repository import (
    KnowledgeSourceRepository,
)

router = APIRouter()


class _StubFileStorage(IFileStoragePort):
    """In-process file-storage stub — same pattern as assets.py."""

    def upload(
        self,
        tenant_id: UUID,
        folder: str,
        filename: str,
        content: BinaryIO,
        mime_type: str,
    ) -> tuple[str, int]:
        data = content.read() if hasattr(content, "read") else b""
        size = len(data) if isinstance(data, (bytes, bytearray)) else 0
        url = f"https://stub.local/{tenant_id}/{folder}/{uuid4().hex}-{filename}"
        return url, size

    def get_download_stream(self, file_url: str) -> BinaryIO:
        return BytesIO(b"")

    def get_signed_url(self, file_url: str, *, expires_in: int = 900) -> str:
        return file_url

    def delete(self, file_url: str) -> None:
        return None


class _StubRAGIndexer(IRAGIndexerPort):
    """Synchronous no-op indexer.

    Returns empty Qdrant point IDs and zero chunks — just enough to keep
    the service flow stable. The real indexer will replace this binding
    once the Qdrant pipeline lands.
    """

    def index_source(
        self,
        source: KnowledgeSource,
        raw_bytes: bytes | None = None,
    ) -> tuple[list[str], int]:
        return [], 0

    def reindex_source(self, source: KnowledgeSource) -> tuple[list[str], int]:
        return [], 0

    def delete_source(self, source: KnowledgeSource) -> None:
        return None


def _service(db: Session) -> OfferKnowledgeService:
    return OfferKnowledgeService(
        knowledge_repo=KnowledgeSourceRepository(db),
        file_storage=_StubFileStorage(),
        rag_indexer=_StubRAGIndexer(),
    )


def _to_response(source: KnowledgeSource) -> KnowledgeSourceResponse:
    return KnowledgeSourceResponse.model_validate(
        {
            "id": source.id,
            "offer_id": source.offer_id,
            "name": source.name,
            "type": source.type,
            "status": source.status,
            "source_url": source.source_url,
            "file_url": source.file_url,
            "mime_type": source.mime_type,
            "size_bytes": source.size_bytes,
            "indexed_chunk_count": source.indexed_chunk_count,
            "last_indexed_at": source.last_indexed_at,
            "metadata": source.metadata,
            "error_message": source.error_message,
            "created_at": source.created_at,
            "updated_at": source.updated_at,
        },
    )


@router.get("/{offer_id}/knowledge", response_model=KnowledgeListResponse)
async def list_knowledge_sources(
    offer_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    search: Annotated[str | None, Query()] = None,
    type_: Annotated[KnowledgeSourceType | None, Query(alias="type")] = None,
):
    sources = _service(db).list_sources(
        tenant_id=user.tenant_id,
        offer_id=UUID(offer_id),
        search=search,
        type_=type_,
    )
    return KnowledgeListResponse(
        items=[_to_response(s) for s in sources],
        total=len(sources),
    )


@router.post(
    "/{offer_id}/knowledge/upload",
    response_model=KnowledgeSourceResponse,
    status_code=201,
)
async def upload_knowledge_source(
    offer_id: str,
    file: Annotated[UploadFile, File()],
    type_: Annotated[KnowledgeSourceType, Form(alias="type")],
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    name: Annotated[str | None, Form()] = None,
):
    content = await file.read()
    source = _service(db).upload_source(
        tenant_id=user.tenant_id,
        offer_id=UUID(offer_id),
        file_bytes=content,
        filename=file.filename or (name or "upload"),
        type_=type_,
        name=name,
    )
    return _to_response(source)


@router.post(
    "/{offer_id}/knowledge/url",
    response_model=KnowledgeSourceResponse,
    status_code=201,
)
async def add_knowledge_url(
    offer_id: str,
    body: KnowledgeUrlRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    source = _service(db).add_url_source(
        tenant_id=user.tenant_id,
        offer_id=UUID(offer_id),
        url=str(body.url),
        type_=body.type,
        name=body.name,
    )
    return _to_response(source)


@router.delete("/{offer_id}/knowledge/{source_id}", status_code=204)
async def delete_knowledge_source(
    offer_id: str,
    source_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    try:
        _service(db).delete_source(
            tenant_id=user.tenant_id,
            offer_id=UUID(offer_id),
            source_id=UUID(source_id),
        )
    except KnowledgeSourceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/{offer_id}/knowledge/{source_id}/reindex",
    response_model=KnowledgeSourceResponse,
)
async def reindex_knowledge_source(
    offer_id: str,
    source_id: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        source = _service(db).reindex_source(
            tenant_id=user.tenant_id,
            offer_id=UUID(offer_id),
            source_id=UUID(source_id),
        )
    except KnowledgeSourceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_response(source)
