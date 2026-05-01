"""SegmentRepository SQLAlchemy implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from sqlalchemy import func, select, update

if TYPE_CHECKING:
    from collections.abc import Sequence
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.campaigns.domain.repositories import SegmentRepository
from src.modules.campaigns.domain.segment import Segment
from src.modules.campaigns.domain.segment_filter import PredefinedSegmentFilter
from src.modules.campaigns.infrastructure.models.segment_model import SegmentModel

logger = structlog.get_logger()


class SegmentRepositoryImpl(SegmentRepository):
    """Async SQLAlchemy 2.0 implementation of SegmentRepository."""

    @staticmethod
    def _build_filter_dsl_json(segment: Segment) -> dict:
        """Serialize filter_dsl for JSONB storage.

        STATIC segments store lead_ids snapshot as {"_static": true, "lead_ids": [...]}.
        DYNAMIC segments store the PredefinedSegmentFilter as-is.
        """
        if segment.segment_type.value == "static" and segment.static_lead_ids is not None:
            return {
                "_static": True,
                "lead_ids": [str(lid) for lid in segment.static_lead_ids],
            }
        return segment.filter_dsl.model_dump(mode="json")

    async def append(self, segment: Segment, *, session: AsyncSession) -> None:
        """Persist a new Segment. Raises on duplicate (tenant_id, name) if not deleted."""
        row = SegmentModel(
            id=segment.id,
            tenant_id=segment.tenant_id,
            name=segment.name,
            description=segment.description,
            segment_type=segment.segment_type.value,
            filter_dsl=self._build_filter_dsl_json(segment),
            estimated_size=segment.estimated_size,
            last_calculated_at=segment.last_calculated_at,
            created_at=segment.created_at,
            updated_at=segment.updated_at,
            deleted_at=segment.deleted_at,
        )
        session.add(row)
        logger.info(
            "segment_repository_append",
            tenant_id=str(segment.tenant_id),
            segment_id=str(segment.id),
            name=segment.name,
            segment_type=segment.segment_type.value,
        )

    async def update(self, segment: Segment, *, session: AsyncSession) -> None:
        """Update an existing Segment."""
        stmt = (
            update(SegmentModel)
            .where(
                SegmentModel.id == segment.id,
                SegmentModel.tenant_id == segment.tenant_id,
            )
            .values(
                name=segment.name,
                description=segment.description,
                segment_type=segment.segment_type.value,
                filter_dsl=self._build_filter_dsl_json(segment),
                estimated_size=segment.estimated_size,
                last_calculated_at=segment.last_calculated_at,
                updated_at=segment.updated_at,
                deleted_at=segment.deleted_at,
            )
        )
        await session.execute(stmt)
        logger.info(
            "segment_repository_update",
            tenant_id=str(segment.tenant_id),
            segment_id=str(segment.id),
        )

    async def get_by_id(self, segment_id: UUID, tenant_id: UUID, *, session: AsyncSession) -> Segment | None:
        """Fetch by primary key, scoped to tenant. Excludes soft-deleted."""
        stmt = select(SegmentModel).where(
            SegmentModel.id == segment_id,
            SegmentModel.tenant_id == tenant_id,
            SegmentModel.deleted_at.is_(None),
        )
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_domain(row)

    async def get_by_name(self, name: str, tenant_id: UUID, *, session: AsyncSession) -> Segment | None:
        """Fetch by natural key (name), scoped to tenant. Excludes soft-deleted."""
        stmt = select(SegmentModel).where(
            SegmentModel.name == name,
            SegmentModel.tenant_id == tenant_id,
            SegmentModel.deleted_at.is_(None),
        )
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_domain(row)

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        *,
        session: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> Sequence[Segment]:
        """List segments for a tenant. Excludes soft-deleted."""
        stmt = (
            select(SegmentModel)
            .where(
                SegmentModel.tenant_id == tenant_id,
                SegmentModel.deleted_at.is_(None),
            )
            .order_by(SegmentModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()
        return [self._to_domain(row) for row in rows]

    async def soft_delete(self, segment_id: UUID, tenant_id: UUID, *, session: AsyncSession) -> None:
        """Set deleted_at = now(). Releases the unique name for reuse."""
        stmt = (
            update(SegmentModel)
            .where(
                SegmentModel.id == segment_id,
                SegmentModel.tenant_id == tenant_id,
                SegmentModel.deleted_at.is_(None),
            )
            .values(deleted_at=func.now())
        )
        await session.execute(stmt)
        logger.info(
            "segment_repository_soft_delete",
            tenant_id=str(tenant_id),
            segment_id=str(segment_id),
        )

    @staticmethod
    def _to_domain(row: SegmentModel) -> Segment:
        """Map JSONB filter_dsl dict to PredefinedSegmentFilter.

        STATIC segments store {"_static": true, "lead_ids": [...]} in filter_dsl.
        For these, we use an empty sentinel PredefinedSegmentFilter() for the
        typed field, and populate static_lead_ids from the JSONB payload.
        This preserves the arch invariant that filter_dsl is always a valid
        PredefinedSegmentFilter while allowing STATIC segments to carry their
        lead_ids snapshot.
        """
        raw_filter = row.filter_dsl or {}
        static_lead_ids: list | None = None

        if raw_filter.get("_static") is True:
            # STATIC segment: extract lead_ids from JSONB snapshot
            from uuid import UUID as _UUID

            raw_ids = raw_filter.get("lead_ids", [])
            static_lead_ids = [_UUID(lid) if isinstance(lid, str) else lid for lid in raw_ids]
            filter_dsl = PredefinedSegmentFilter()  # empty sentinel — never evaluated for STATIC
        else:
            filter_dsl = PredefinedSegmentFilter.model_validate(raw_filter)

        data = {
            "id": row.id,
            "tenant_id": row.tenant_id,
            "name": row.name,
            "description": row.description,
            "segment_type": row.segment_type,
            "filter_dsl": filter_dsl,
            "static_lead_ids": static_lead_ids,
            "estimated_size": row.estimated_size,
            "last_calculated_at": row.last_calculated_at,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "deleted_at": row.deleted_at,
        }
        return Segment.model_validate(data)
