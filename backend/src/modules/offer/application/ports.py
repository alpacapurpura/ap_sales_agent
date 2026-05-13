"""Application ports for the offer module.

Defines abstract interfaces that external modules and infrastructure
adapters must implement to provide services to the offer bounded context.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, BinaryIO

# Re-exported here so offer-internal code has a single import origin
# while the actual contract lives in shared/links (DDD-clean). See
# ``shared/links/ports/edition_landing_clone.py``.
from luana_core_platform.links.ports.edition_landing_clone import (
    IEditionLandingClonePort,
    LandingRef,
)

if TYPE_CHECKING:
    from uuid import UUID

    from luana_core_offer_studio.domain.assets import OfferAsset
    from luana_core_offer_studio.domain.enums import (
        AssetSource,
        AssetType,
        KnowledgeSourceType,
    )
    from luana_core_offer_studio.domain.knowledge_source import KnowledgeSource
    from luana_core_offer_studio.domain.offer import Offer
    from luana_core_offer_studio.domain.offer_ai_schemas import (
        PsychologyGenerationRequest,
        PsychologyGenerationResponse,
    )


class PsychologyGeneratorPort(ABC):
    """Psychology Generator Port."""

    @abstractmethod
    async def generate_psychology(
        self,
        request: PsychologyGenerationRequest,
        tenant_id: UUID,
    ) -> PsychologyGenerationResponse:
        """Generate psychology."""
        ...


class IOfferAssetRepository(ABC):
    """Repository port for offer assets. Implementations live in infra."""

    @abstractmethod
    def create(self, asset: OfferAsset) -> OfferAsset:
        """Create."""
        ...

    @abstractmethod
    def get_by_id(
        self,
        tenant_id: UUID,
        offer_id: UUID,
        asset_id: UUID,
    ) -> OfferAsset | None:
        """Retrieve by id."""
        ...

    @abstractmethod
    def list(
        self,
        tenant_id: UUID,
        offer_id: UUID,
        *,
        search: str | None = None,
        type_: AssetType | None = None,
        source: AssetSource | None = None,
        edition_id: UUID | None = None,
        sort: str = "created_desc",
        limit: int = 24,
        offset: int = 0,
    ) -> tuple[list[OfferAsset], int]:
        """List assets.

        ``edition_id`` semantics:

        - ``None`` → legacy/offer-wide listing, returns every live asset
          regardless of edition scoping.
        - set → edition-scoped listing: assets bound to that edition OR
          flagged ``shared_across_editions = TRUE``.
        """
        ...

    @abstractmethod
    def update(self, asset: OfferAsset) -> OfferAsset:
        """Update."""
        ...

    @abstractmethod
    def soft_delete(self, tenant_id: UUID, offer_id: UUID, asset_id: UUID) -> bool:
        """Soft delete."""
        ...

    @abstractmethod
    def count_by_offer(self, tenant_id: UUID, offer_id: UUID) -> int:
        """Count by offer."""
        ...


class IKnowledgeSourceRepository(ABC):
    """Repository port for knowledge sources."""

    @abstractmethod
    def create(self, source: KnowledgeSource) -> KnowledgeSource:
        """Create."""
        ...

    @abstractmethod
    def get_by_id(
        self,
        tenant_id: UUID,
        offer_id: UUID,
        source_id: UUID,
    ) -> KnowledgeSource | None:
        """Retrieve by id."""
        ...

    @abstractmethod
    def list(
        self,
        tenant_id: UUID,
        offer_id: UUID,
        *,
        search: str | None = None,
        type_: KnowledgeSourceType | None = None,
    ) -> list[KnowledgeSource]:
        """List."""
        ...

    @abstractmethod
    def update(self, source: KnowledgeSource) -> KnowledgeSource:
        """Update."""
        ...

    @abstractmethod
    def soft_delete(self, tenant_id: UUID, offer_id: UUID, source_id: UUID) -> bool:
        """Soft delete."""
        ...

    @abstractmethod
    def count_by_offer(self, tenant_id: UUID, offer_id: UUID) -> int:
        """Count by offer."""
        ...

    @abstractmethod
    def count_indexed_by_offer(self, tenant_id: UUID, offer_id: UUID) -> int:
        """Count indexed by offer."""
        ...


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
    ) -> tuple[str, int]:  # (public_url, size_bytes)
        """Upload."""
        ...

    @abstractmethod
    def get_download_stream(self, file_url: str) -> BinaryIO:
        """Retrieve download stream."""
        ...

    @abstractmethod
    def get_signed_url(self, file_url: str, *, expires_in: int = 900) -> str:
        """Retrieve signed url."""
        ...

    @abstractmethod
    def delete(self, file_url: str) -> None:
        """Delete."""
        ...


class ILandingGenerationRepository(ABC):
    """Narrow cross-module port for the landing generation flow.

    Exposes just the subset of landing-module persistence that the offer
    module needs to drive landing generation/publish/unpublish from the
    offer header. Implemented by the landing module and wired via FastAPI
    ``Depends`` at the API layer.
    """

    @abstractmethod
    def get_by_offer_id(self, tenant_id: UUID, offer_id: UUID) -> object | None:
        """Retrieve by offer id."""
        ...

    @abstractmethod
    def upsert_for_generation(
        self,
        *,
        tenant_id: UUID,
        offer_id: UUID,
        snapshot_version: str,
        job_id: UUID,
        job_status: str,
    ) -> object:
        """Upsert for generation."""
        ...

    @abstractmethod
    def save(self, landing: object) -> object:
        """Save."""
        ...


class IRAGIndexerPort(ABC):
    """Abstraction over the Qdrant pipeline used to index knowledge sources.

    The production implementation wires the existing embeddings + Qdrant
    pipeline. The default binding returns a stub that marks the source as
    indexed with a synthetic chunk count — enough for tests and to keep
    the UI contract stable until the real pipeline is built.
    """

    @abstractmethod
    def index_source(
        self,
        source: KnowledgeSource,
        raw_bytes: bytes | None = None,
    ) -> tuple[list[str], int]:  # (qdrant_point_ids, chunk_count)
        """Index source."""
        ...

    @abstractmethod
    def reindex_source(self, source: KnowledgeSource) -> tuple[list[str], int]:
        """Reindex source."""
        ...

    @abstractmethod
    def delete_source(self, source: KnowledgeSource) -> None:
        """Delete source."""
        ...


class IOfferCompletionService(ABC):
    """Service for ioffer completion operations."""

    @abstractmethod
    def compute(self, offer: Offer) -> float:
        """Compute."""
        ...


__all__ = [
    "IEditionLandingClonePort",
    "IFileStoragePort",
    "IKnowledgeSourceRepository",
    "ILandingGenerationRepository",
    "IOfferAssetRepository",
    "IOfferCompletionService",
    "IRAGIndexerPort",
    "LandingRef",
    "PsychologyGeneratorPort",
]
