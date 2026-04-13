"""Offer knowledge-source service.

Drives the Knowledge tab — uploads / URL registrations / reindex / delete
against the Qdrant-backed RAG pipeline via ``IRAGIndexerPort``.

Indexing is asynchronous from the user's perspective: rows are created in
``PROCESSING`` status and flipped to ``INDEXED`` once the indexer finishes.
The default ``IRAGIndexerPort`` binding is a stub that returns immediately;
a real worker will replace it without any changes here.
"""

from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING

import structlog

from src.modules.offer.domain.enums import (
    KnowledgeSourceStatus,
    KnowledgeSourceType,
)
from src.modules.offer.domain.events import (
    KnowledgeSourceCreated,
    KnowledgeSourceDeleted,
)
from src.modules.offer.domain.exceptions import KnowledgeSourceNotFoundError
from src.modules.offer.domain.knowledge_source import KnowledgeSource
from src.shared.domain.datetime_utils import utc_now

if TYPE_CHECKING:
    from uuid import UUID

    from src.modules.offer.application.ports import (
        IFileStoragePort,
        IKnowledgeSourceRepository,
        IRAGIndexerPort,
    )


logger = structlog.get_logger(__name__)


_DEFAULT_MIME_BY_TYPE: dict[KnowledgeSourceType, str] = {
    KnowledgeSourceType.PDF: "application/pdf",
    KnowledgeSourceType.DOCX: ("application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    KnowledgeSourceType.TXT: "text/plain",
    KnowledgeSourceType.MARKDOWN: "text/markdown",
    KnowledgeSourceType.VIDEO: "video/mp4",
}


class OfferKnowledgeService:
    """Service for offer knowledge operations."""

    def __init__(
        self,
        *,
        knowledge_repo: IKnowledgeSourceRepository,
        file_storage: IFileStoragePort,
        rag_indexer: IRAGIndexerPort,
        event_bus: object | None = None,
    ) -> None:
        """Initialize service with dependencies."""
        self._repo = knowledge_repo
        self._storage = file_storage
        self._indexer = rag_indexer
        self._events = event_bus

    # --------------------------------------------------------------- list
    def list_sources(
        self,
        *,
        tenant_id: UUID,
        offer_id: UUID,
        search: str | None = None,
        type_: KnowledgeSourceType | None = None,
    ) -> list[KnowledgeSource]:
        """List sources."""
        return self._repo.list(tenant_id, offer_id, search=search, type_=type_)

    # ---------------------------------------------------------------- get
    def get_source(
        self,
        *,
        tenant_id: UUID,
        offer_id: UUID,
        source_id: UUID,
    ) -> KnowledgeSource:
        """Retrieve source."""
        source = self._repo.get_by_id(tenant_id, offer_id, source_id)
        if source is None:
            raise KnowledgeSourceNotFoundError(source_id)
        return source

    # -------------------------------------------------------------- upload
    def upload_source(
        self,
        *,
        tenant_id: UUID,
        offer_id: UUID,
        file_bytes: bytes,
        filename: str,
        type_: KnowledgeSourceType,
        mime_type: str | None = None,
        name: str | None = None,
    ) -> KnowledgeSource:
        """Upload source."""
        mime = mime_type or _DEFAULT_MIME_BY_TYPE.get(type_, "application/octet-stream")
        folder = f"offers/{offer_id}/knowledge"
        file_url, size_bytes = self._storage.upload(
            tenant_id=tenant_id,
            folder=folder,
            filename=filename,
            content=BytesIO(file_bytes),
            mime_type=mime,
        )
        source = KnowledgeSource(
            tenant_id=tenant_id,
            offer_id=offer_id,
            name=name or filename,
            type=type_,
            status=KnowledgeSourceStatus.PROCESSING,
            file_url=file_url,
            mime_type=mime,
            size_bytes=size_bytes,
        )
        created = self._repo.create(source)
        self._emit_created(created)
        try:
            self._indexer.index_source(created, raw_bytes=file_bytes)
        except Exception:  # noqa: BLE001 — knowledge store resilience
            logger.warning(
                "offer_knowledge_index_failed",
                source_id=str(created.id),
                offer_id=str(offer_id),
            )
        logger.info(
            "offer_knowledge_uploaded",
            source_id=str(created.id),
            offer_id=str(offer_id),
            tenant_id=str(tenant_id),
        )
        return created

    # --------------------------------------------------------------- url
    def add_url_source(
        self,
        *,
        tenant_id: UUID,
        offer_id: UUID,
        url: str,
        type_: KnowledgeSourceType,
        name: str | None = None,
    ) -> KnowledgeSource:
        """Add url source."""
        source = KnowledgeSource(
            tenant_id=tenant_id,
            offer_id=offer_id,
            name=name or url,
            type=type_,
            status=KnowledgeSourceStatus.PROCESSING,
            source_url=url,
        )
        created = self._repo.create(source)
        self._emit_created(created)
        try:
            self._indexer.index_source(created)
        except Exception:  # noqa: BLE001 — knowledge store resilience
            logger.warning(
                "offer_knowledge_index_failed",
                source_id=str(created.id),
                offer_id=str(offer_id),
            )
        logger.info(
            "offer_knowledge_url_added",
            source_id=str(created.id),
            offer_id=str(offer_id),
            tenant_id=str(tenant_id),
        )
        return created

    # --------------------------------------------------------------- delete
    def delete_source(
        self,
        *,
        tenant_id: UUID,
        offer_id: UUID,
        source_id: UUID,
    ) -> None:
        """Delete source."""
        source = self._repo.get_by_id(tenant_id, offer_id, source_id)
        if source is None:
            raise KnowledgeSourceNotFoundError(source_id)
        try:
            self._indexer.delete_source(source)
        except Exception:  # noqa: BLE001 — knowledge store resilience
            logger.warning(
                "offer_knowledge_indexer_delete_failed",
                source_id=str(source_id),
            )
        if not self._repo.soft_delete(tenant_id, offer_id, source_id):
            raise KnowledgeSourceNotFoundError(source_id)
        self._emit_deleted(tenant_id=tenant_id, offer_id=offer_id, source_id=source_id)
        logger.info(
            "offer_knowledge_deleted",
            source_id=str(source_id),
            offer_id=str(offer_id),
            tenant_id=str(tenant_id),
        )

    # ------------------------------------------------------------- reindex
    def reindex_source(
        self,
        *,
        tenant_id: UUID,
        offer_id: UUID,
        source_id: UUID,
    ) -> KnowledgeSource:
        """Reindex source."""
        source = self._repo.get_by_id(tenant_id, offer_id, source_id)
        if source is None:
            raise KnowledgeSourceNotFoundError(source_id)
        source.status = KnowledgeSourceStatus.PROCESSING
        source.error_message = None
        updated = self._repo.update(source)
        try:
            self._indexer.reindex_source(updated)
        except Exception:  # noqa: BLE001 — knowledge store resilience
            logger.warning(
                "offer_knowledge_reindex_failed",
                source_id=str(source_id),
            )
        logger.info(
            "offer_knowledge_reindex_queued",
            source_id=str(source_id),
            offer_id=str(offer_id),
        )
        return updated

    # -------------------------------------------------------------- events
    def _emit_created(self, source: KnowledgeSource) -> None:
        if self._events is None:
            return
        event = KnowledgeSourceCreated(
            tenant_id=source.tenant_id,
            occurred_at=utc_now(),
            offer_id=source.offer_id,
            source_id=source.id,
            type=source.type.value,
        )
        try:
            self._events.publish(event)
        except Exception:  # noqa: BLE001 — knowledge store resilience
            logger.warning(
                "offer_knowledge_event_publish_failed",
                source_id=str(source.id),
            )

    def _emit_deleted(
        self,
        *,
        tenant_id: UUID,
        offer_id: UUID,
        source_id: UUID,
    ) -> None:
        if self._events is None:
            return
        event = KnowledgeSourceDeleted(
            tenant_id=tenant_id,
            occurred_at=utc_now(),
            offer_id=offer_id,
            source_id=source_id,
        )
        try:
            self._events.publish(event)
        except Exception:  # noqa: BLE001 — knowledge store resilience
            logger.warning(
                "offer_knowledge_event_publish_failed",
                source_id=str(source_id),
            )


__all__ = ["OfferKnowledgeService"]
