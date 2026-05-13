"""ProductMappingPort implementation — bridges analytics and offer modules."""

import asyncio
from uuid import UUID

from luana_core_offer_studio.infrastructure.repositories.external_product_mapping_repository import (
    ExternalProductMappingRepository,
)
from luana_core_platform.domain.ports import ProductMappingPort
from sqlalchemy.orm import Session


class ProductMappingPortImpl(ProductMappingPort):
    """Product Mapping Port Impl."""

    def __init__(self, db: Session) -> None:
        """Initialize instance."""
        self.db = db
        self.repo = ExternalProductMappingRepository(db)

    async def resolve_offer_id(
        self,
        tenant_id: UUID,
        source: str,
        external_product_id: str,
    ) -> UUID | None:
        """Resolve offer id."""
        mapping = await asyncio.to_thread(
            self.repo.get_by_external_id,
            tenant_id,
            source,
            external_product_id,
        )
        return mapping.offer_id if mapping else None

    async def bulk_resolve(
        self,
        tenant_id: UUID,
        source: str,
        external_ids: list[str],
    ) -> dict[str, UUID]:
        """Bulk resolve."""
        return await asyncio.to_thread(
            self.repo.bulk_resolve,
            tenant_id,
            source,
            external_ids,
        )
