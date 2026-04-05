"""ProductMappingPort implementation — bridges analytics and offer modules."""

import asyncio
from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.offer.infrastructure.repositories.external_product_mapping_repository import (
    ExternalProductMappingRepository,
)
from src.shared.domain.ports import ProductMappingPort


class ProductMappingPortImpl(ProductMappingPort):
    def __init__(self, db: Session):
        self.db = db
        self.repo = ExternalProductMappingRepository(db)

    async def resolve_offer_id(
        self, tenant_id: UUID, source: str, external_product_id: str
    ) -> UUID | None:
        mapping = await asyncio.to_thread(
            self.repo.get_by_external_id, tenant_id, source, external_product_id
        )
        return mapping.offer_id if mapping else None

    async def bulk_resolve(
        self, tenant_id: UUID, source: str, external_ids: list[str]
    ) -> dict[str, UUID]:
        return await asyncio.to_thread(
            self.repo.bulk_resolve, tenant_id, source, external_ids
        )
