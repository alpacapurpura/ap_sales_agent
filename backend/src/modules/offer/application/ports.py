"""Application ports for the offer module.

Defines abstract interfaces that external modules and infrastructure
adapters must implement to provide services to the offer bounded context.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, BinaryIO

if TYPE_CHECKING:
    from uuid import UUID

    from src.modules.offer.domain.assets import OfferAsset
    from src.modules.offer.domain.enums import (
        AssetSource,
        AssetType,
        KnowledgeSourceType,
    )
    from src.modules.offer.domain.knowledge_source import KnowledgeSource
    from src.modules.offer.domain.offer import Offer
    from src.modules.offer.domain.offer_ai_schemas import (
        PsychologyGenerationRequest,
        PsychologyGenerationResponse,
    )


class PsychologyGeneratorPort(ABC):
    @abstractmethod
    async def generate_psychology(
        self, request: PsychologyGenerationRequest, tenant_id: UUID
    ) -> PsychologyGenerationResponse: ...


class IOfferAssetRepository(ABC):
    """Repository port for offer assets. Implementations live in infra."""

    @abstractmethod
    def create(self, asset: OfferAsset) -> OfferAsset: ...

    @abstractmethod
    def get_by_id(
        self, tenant_id: UUID, offer_id: UUID, asset_id: UUID
    ) -> OfferAsset | None: ...

    @abstractmethod
    def list(
        self,
        tenant_id: UUID,
        offer_id: UUID,
        *,
        search: str | None = None,
        type: AssetType | None = None,
        source: AssetSource | None = None,
        sort: str = "created_desc",
        limit: int = 24,
        offset: int = 0,
    ) -> tuple[list[OfferAsset], int]: ...

    @abstractmethod
    def update(self, asset: OfferAsset) -> OfferAsset: ...

    @abstractmethod
    def soft_delete(self, tenant_id: UUID, offer_id: UUID, asset_id: UUID) -> bool: ...

    @abstractmethod
    def count_by_offer(self, tenant_id: UUID, offer_id: UUID) -> int: ...


class IKnowledgeSourceRepository(ABC):
    """Repository port for knowledge sources."""

    @abstractmethod
    def create(self, source: KnowledgeSource) -> KnowledgeSource: ...

    @abstractmethod
    def get_by_id(
        self, tenant_id: UUID, offer_id: UUID, source_id: UUID
    ) -> KnowledgeSource | None: ...

    @abstractmethod
    def list(
        self,
        tenant_id: UUID,
        offer_id: UUID,
        *,
        search: str | None = None,
        type: KnowledgeSourceType | None = None,
    ) -> list[KnowledgeSource]: ...

    @abstractmethod
    def update(self, source: KnowledgeSource) -> KnowledgeSource: ...

    @abstractmethod
    def soft_delete(self, tenant_id: UUID, offer_id: UUID, source_id: UUID) -> bool: ...

    @abstractmethod
    def count_by_offer(self, tenant_id: UUID, offer_id: UUID) -> int: ...

    @abstractmethod
    def count_indexed_by_offer(self, tenant_id: UUID, offer_id: UUID) -> int: ...


class IFileStoragePort(ABC):
    """Abstraction over R2/S3/local file storage."""

    @abstractmethod
    def upload(
        self,
        tenant_id: UUID,
        folder: str,
        filename: str,
        content: BinaryIO,
        mime_type: str,
    ) -> tuple[str, int]: ...  # (public_url, size_bytes)

    @abstractmethod
    def get_download_stream(self, file_url: str) -> BinaryIO: ...

    @abstractmethod
    def delete(self, file_url: str) -> None: ...


class IRAGIndexerPort(ABC):
    """Abstraction over the Qdrant pipeline used to index knowledge sources.

    The production implementation wires the existing embeddings + Qdrant
    pipeline. The default binding returns a stub that marks the source as
    indexed with a synthetic chunk count — enough for tests and to keep
    the UI contract stable until the real pipeline is built.
    """

    @abstractmethod
    def index_source(
        self, source: KnowledgeSource, raw_bytes: bytes | None = None
    ) -> tuple[list[str], int]: ...  # (qdrant_point_ids, chunk_count)

    @abstractmethod
    def reindex_source(self, source: KnowledgeSource) -> tuple[list[str], int]: ...

    @abstractmethod
    def delete_source(self, source: KnowledgeSource) -> None: ...


class IOfferCompletionService(ABC):
    @abstractmethod
    def compute(self, offer: Offer) -> float: ...


__all__ = [
    "IFileStoragePort",
    "IKnowledgeSourceRepository",
    "IOfferAssetRepository",
    "IOfferCompletionService",
    "IRAGIndexerPort",
    "PsychologyGeneratorPort",
]
