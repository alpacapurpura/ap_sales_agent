"""Repository for offer_knowledge_sources CRUD operations.

Implements `IKnowledgeSourceRepository` from `offer.application.ports`.
All queries filter by `tenant_id` (multitenant isolation) and exclude
soft-deleted rows (`deleted_at IS NULL`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, or_, select

from src.modules.offer.application.ports import IKnowledgeSourceRepository
from src.modules.offer.domain.enums import (
    KnowledgeSourceStatus,
    KnowledgeSourceType,
)
from src.modules.offer.domain.knowledge_source import KnowledgeSource
from src.modules.offer.infrastructure.models.knowledge_source_model import (
    KnowledgeSourceModel,
)
from src.shared.domain.datetime_utils import utc_now

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session


class KnowledgeSourceRepository(IKnowledgeSourceRepository):
    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------ mapping

    @staticmethod
    def _to_domain(model: KnowledgeSourceModel) -> KnowledgeSource:
        return KnowledgeSource(
            id=model.id,
            tenant_id=model.tenant_id,
            offer_id=model.offer_id,
            name=model.name,
            type=KnowledgeSourceType(model.type),
            status=KnowledgeSourceStatus(model.status),
            source_url=model.source_url,
            file_url=model.file_url,
            mime_type=model.mime_type,
            size_bytes=model.size_bytes,
            indexed_chunk_count=int(model.indexed_chunk_count or 0),
            last_indexed_at=model.last_indexed_at,
            qdrant_collection=model.qdrant_collection,
            qdrant_point_ids=list(model.qdrant_point_ids or []),
            metadata=dict(model.metadata_json or {}),
            error_message=model.error_message,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )

    @staticmethod
    def _apply_domain_to_model(
        model: KnowledgeSourceModel, source: KnowledgeSource
    ) -> None:
        model.tenant_id = source.tenant_id
        model.offer_id = source.offer_id
        model.name = source.name
        model.type = source.type.value
        model.status = source.status.value
        model.source_url = source.source_url
        model.file_url = source.file_url
        model.mime_type = source.mime_type
        model.size_bytes = source.size_bytes
        model.indexed_chunk_count = source.indexed_chunk_count
        model.last_indexed_at = source.last_indexed_at
        model.qdrant_collection = source.qdrant_collection
        model.qdrant_point_ids = list(source.qdrant_point_ids or [])
        model.metadata_json = dict(source.metadata or {})
        model.error_message = source.error_message

    # ------------------------------------------------------------------ CRUD

    def create(self, source: KnowledgeSource) -> KnowledgeSource:
        model = KnowledgeSourceModel(id=source.id)
        self._apply_domain_to_model(model, source)
        self.db.add(model)
        self.db.flush()
        self.db.refresh(model)
        return self._to_domain(model)

    def get_by_id(
        self, tenant_id: UUID, offer_id: UUID, source_id: UUID
    ) -> KnowledgeSource | None:
        stmt = select(KnowledgeSourceModel).where(
            KnowledgeSourceModel.id == source_id,
            KnowledgeSourceModel.tenant_id == tenant_id,
            KnowledgeSourceModel.offer_id == offer_id,
            KnowledgeSourceModel.deleted_at.is_(None),
        )
        model = self.db.execute(stmt).scalar_one_or_none()
        return self._to_domain(model) if model else None

    def list(
        self,
        tenant_id: UUID,
        offer_id: UUID,
        *,
        search: str | None = None,
        type: KnowledgeSourceType | None = None,
    ) -> list[KnowledgeSource]:
        filters = [
            KnowledgeSourceModel.tenant_id == tenant_id,
            KnowledgeSourceModel.offer_id == offer_id,
            KnowledgeSourceModel.deleted_at.is_(None),
        ]
        if search:
            like = f"%{search}%"
            filters.append(
                or_(
                    KnowledgeSourceModel.name.ilike(like),
                    KnowledgeSourceModel.source_url.ilike(like),
                )
            )
        if type is not None:
            filters.append(KnowledgeSourceModel.type == type.value)

        stmt = (
            select(KnowledgeSourceModel)
            .where(*filters)
            .order_by(KnowledgeSourceModel.created_at.desc())
        )
        rows = self.db.execute(stmt).scalars().all()
        return [self._to_domain(r) for r in rows]

    def update(self, source: KnowledgeSource) -> KnowledgeSource:
        stmt = select(KnowledgeSourceModel).where(
            KnowledgeSourceModel.id == source.id,
            KnowledgeSourceModel.tenant_id == source.tenant_id,
            KnowledgeSourceModel.deleted_at.is_(None),
        )
        model = self.db.execute(stmt).scalar_one_or_none()
        if model is None:
            msg = f"KnowledgeSource {source.id} not found for update"
            raise ValueError(msg)
        self._apply_domain_to_model(model, source)
        self.db.flush()
        self.db.refresh(model)
        return self._to_domain(model)

    def soft_delete(self, tenant_id: UUID, offer_id: UUID, source_id: UUID) -> bool:
        stmt = select(KnowledgeSourceModel).where(
            KnowledgeSourceModel.id == source_id,
            KnowledgeSourceModel.tenant_id == tenant_id,
            KnowledgeSourceModel.offer_id == offer_id,
            KnowledgeSourceModel.deleted_at.is_(None),
        )
        model = self.db.execute(stmt).scalar_one_or_none()
        if model is None:
            return False
        model.deleted_at = utc_now()
        self.db.flush()
        return True

    def count_by_offer(self, tenant_id: UUID, offer_id: UUID) -> int:
        stmt = select(func.count(KnowledgeSourceModel.id)).where(
            KnowledgeSourceModel.tenant_id == tenant_id,
            KnowledgeSourceModel.offer_id == offer_id,
            KnowledgeSourceModel.deleted_at.is_(None),
        )
        return int(self.db.execute(stmt).scalar() or 0)

    def count_indexed_by_offer(self, tenant_id: UUID, offer_id: UUID) -> int:
        stmt = select(func.count(KnowledgeSourceModel.id)).where(
            KnowledgeSourceModel.tenant_id == tenant_id,
            KnowledgeSourceModel.offer_id == offer_id,
            KnowledgeSourceModel.deleted_at.is_(None),
            KnowledgeSourceModel.status == KnowledgeSourceStatus.INDEXED.value,
        )
        return int(self.db.execute(stmt).scalar() or 0)
