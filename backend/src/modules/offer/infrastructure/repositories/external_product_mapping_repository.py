"""Repository for external product → offer mappings."""

from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.modules.offer.infrastructure.models.external_product_mapping_model import (
    ExternalProductMappingModel,
)


class ExternalProductMappingRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_external_id(
        self, tenant_id: UUID, source: str, external_id: str
    ) -> Optional[ExternalProductMappingModel]:
        stmt = select(ExternalProductMappingModel).where(
            ExternalProductMappingModel.tenant_id == tenant_id,
            ExternalProductMappingModel.source == source,
            ExternalProductMappingModel.external_id == external_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_offer_id(
        self, tenant_id: UUID, offer_id: UUID
    ) -> List[ExternalProductMappingModel]:
        stmt = select(ExternalProductMappingModel).where(
            ExternalProductMappingModel.tenant_id == tenant_id,
            ExternalProductMappingModel.offer_id == offer_id,
        )
        return list(self.db.execute(stmt).scalars().all())

    def list_by_source(
        self, tenant_id: UUID, source: str
    ) -> List[ExternalProductMappingModel]:
        stmt = select(ExternalProductMappingModel).where(
            ExternalProductMappingModel.tenant_id == tenant_id,
            ExternalProductMappingModel.source == source,
        )
        return list(self.db.execute(stmt).scalars().all())

    def create_mapping(
        self,
        tenant_id: UUID,
        offer_id: UUID,
        source: str,
        external_id: str,
        external_name: Optional[str] = None,
        metadata_info: Optional[dict] = None,
    ) -> ExternalProductMappingModel:
        mapping = ExternalProductMappingModel(
            tenant_id=tenant_id,
            offer_id=offer_id,
            source=source,
            external_id=external_id,
            external_name=external_name,
            metadata_info=metadata_info or {},
        )
        self.db.add(mapping)
        self.db.flush()
        return mapping

    def delete_mapping(self, mapping_id: UUID, tenant_id: UUID) -> bool:
        stmt = delete(ExternalProductMappingModel).where(
            ExternalProductMappingModel.id == mapping_id,
            ExternalProductMappingModel.tenant_id == tenant_id,
        )
        result = self.db.execute(stmt)
        return result.rowcount > 0

    def bulk_resolve(
        self, tenant_id: UUID, source: str, external_ids: List[str]
    ) -> Dict[str, UUID]:
        """Batch lookup: returns {external_id: offer_id} for found mappings."""
        if not external_ids:
            return {}
        stmt = select(
            ExternalProductMappingModel.external_id,
            ExternalProductMappingModel.offer_id,
        ).where(
            ExternalProductMappingModel.tenant_id == tenant_id,
            ExternalProductMappingModel.source == source,
            ExternalProductMappingModel.external_id.in_(external_ids),
        )
        rows = self.db.execute(stmt).all()
        return {ext_id: offer_id for ext_id, offer_id in rows}
