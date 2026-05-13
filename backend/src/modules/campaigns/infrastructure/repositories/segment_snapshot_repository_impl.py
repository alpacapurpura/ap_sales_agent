"""SegmentSnapshotRepository SQLAlchemy implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

import structlog
from sqlalchemy import select

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession

from luana_core_campaigns.domain.repositories import SegmentSnapshotRepository
from luana_core_campaigns.domain.segment import SegmentSnapshot
from luana_core_campaigns.infrastructure.models.segment_snapshot_model import SegmentSnapshotModel

logger = structlog.get_logger()


class SegmentSnapshotRepositoryImpl(SegmentSnapshotRepository):
    """Async SQLAlchemy 2.0 implementation of SegmentSnapshotRepository."""

    async def append(self, snapshot: SegmentSnapshot, *, session: AsyncSession) -> None:
        """Persist a new SegmentSnapshot."""
        row = SegmentSnapshotModel(
            id=snapshot.id,
            tenant_id=snapshot.tenant_id,
            segment_id=snapshot.segment_id,
            snapshotted_at=snapshot.snapshotted_at,
            lead_ids=[str(uid) for uid in snapshot.lead_ids],
            lead_count=snapshot.lead_count,
            created_at=snapshot.created_at,
            deleted_at=snapshot.deleted_at,
        )
        session.add(row)
        logger.info(
            "segment_snapshot_repository_append",
            tenant_id=str(snapshot.tenant_id),
            snapshot_id=str(snapshot.id),
            segment_id=str(snapshot.segment_id),
            lead_count=snapshot.lead_count,
        )

    async def get_by_id(self, snapshot_id: UUID, tenant_id: UUID, *, session: AsyncSession) -> SegmentSnapshot | None:
        """Fetch by primary key, scoped to tenant. Excludes soft-deleted."""
        stmt = select(SegmentSnapshotModel).where(
            SegmentSnapshotModel.id == snapshot_id,
            SegmentSnapshotModel.tenant_id == tenant_id,
            SegmentSnapshotModel.deleted_at.is_(None),
        )
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_domain(row)

    async def get_latest_for_segment(
        self, segment_id: UUID, tenant_id: UUID, *, session: AsyncSession
    ) -> SegmentSnapshot | None:
        """Fetch the most recent snapshot for a segment. Returns None if none exist."""
        stmt = (
            select(SegmentSnapshotModel)
            .where(
                SegmentSnapshotModel.segment_id == segment_id,
                SegmentSnapshotModel.tenant_id == tenant_id,
                SegmentSnapshotModel.deleted_at.is_(None),
            )
            .order_by(SegmentSnapshotModel.snapshotted_at.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_domain(row)

    async def list_by_segment(
        self,
        segment_id: UUID,
        tenant_id: UUID,
        *,
        session: AsyncSession,
        limit: int = 10,
    ) -> Sequence[SegmentSnapshot]:
        """List snapshots for a segment, ordered by snapshotted_at DESC."""
        stmt = (
            select(SegmentSnapshotModel)
            .where(
                SegmentSnapshotModel.segment_id == segment_id,
                SegmentSnapshotModel.tenant_id == tenant_id,
                SegmentSnapshotModel.deleted_at.is_(None),
            )
            .order_by(SegmentSnapshotModel.snapshotted_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()
        return [self._to_domain(row) for row in rows]

    @staticmethod
    def _to_domain(row: SegmentSnapshotModel) -> SegmentSnapshot:
        """Map JSONB list[str] to list[UUID] for lead_ids."""
        data = {
            "id": row.id,
            "tenant_id": row.tenant_id,
            "segment_id": row.segment_id,
            "snapshotted_at": row.snapshotted_at,
            "lead_ids": [UUID(s) for s in (row.lead_ids or [])],
            "lead_count": row.lead_count,
            "created_at": row.created_at,
            "deleted_at": row.deleted_at,
        }
        return SegmentSnapshot.model_validate(data)
