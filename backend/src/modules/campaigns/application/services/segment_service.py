"""SegmentService — CRUD + lazy resolve + estimate_size + opt-in snapshot.

Production-grade: resolve() compiles SegmentFilter → SQL WHERE clauses
(NEVER loads leads in Python). estimate_size cached 5min.
"""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import structlog

from src.modules.campaigns.application.services._event_bridge import to_domain_event
from src.modules.campaigns.domain.events import SegmentCreated, SegmentSnapshotted
from src.modules.campaigns.domain.segment import Segment, SegmentSnapshot
from src.modules.campaigns.domain.segment_filter import PredefinedSegmentFilter
from src.shared.domain.datetime_utils import utc_now

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.modules.campaigns.application.dtos.pagination import PaginatedResponse
    from src.modules.campaigns.application.dtos.segment_dtos import (
        SegmentCreate,
        SegmentResponse,
        SegmentUpdate,
    )
    from src.modules.campaigns.application.ports.lead_query_port import LeadQueryPort
    from src.modules.campaigns.application.segment_filter_evaluator import (
        SegmentFilterEvaluator,
    )
    from src.modules.campaigns.application.services.cache import CacheBackend
    from src.modules.campaigns.domain.repositories import (
        SegmentRepository,
        SegmentSnapshotRepository,
    )
    from src.shared.domain_events.outbox.application.outbox_service import OutboxService

logger = structlog.get_logger(__name__)


class SegmentNotFoundError(Exception):
    """Raised when segment not found or not owned by tenant (→ 404)."""


class SegmentDuplicateNameError(Exception):
    """Raised when segment name already exists for tenant (→ 409)."""


class SegmentService:
    """CRUD + lazy resolve + estimate_size + opt-in snapshot.

    resolve() uses SQL-side filtering via SegmentFilterEvaluator.
    NEVER loads leads in Python (scalable to 1000+ tenants × 10K leads).
    """

    ESTIMATE_CACHE_TTL = 300  # 5 min

    def __init__(
        self,
        *,
        repo: SegmentRepository,
        snapshot_repo: SegmentSnapshotRepository,
        lead_query_port: LeadQueryPort,
        filter_evaluator: SegmentFilterEvaluator,
        outbox_service: OutboxService,
        cache: CacheBackend,
    ) -> None:
        """Initialize service with repos and collaborators."""
        self._repo = repo
        self._snapshot_repo = snapshot_repo
        self._lead_query_port = lead_query_port
        self._filter_evaluator = filter_evaluator
        self._outbox_service = outbox_service
        self._cache = cache

    async def create(
        self,
        tenant_id: UUID,
        dto: SegmentCreate,
        *,
        session: AsyncSession,
    ) -> Segment:
        """Create segment. Raises SegmentDuplicateNameError on duplicate name."""
        now = utc_now()
        segment = Segment(
            id=uuid4(),
            tenant_id=tenant_id,
            name=dto.name,
            description=dto.description,
            segment_type=dto.segment_type,
            filter_dsl=dto.filter_dsl,
            created_at=now,
            updated_at=now,
        )
        try:
            await self._repo.append(segment, session=session)
        except Exception as exc:
            exc_str = str(exc).lower()
            if "unique" in exc_str or "duplicate" in exc_str or "uq_segment" in exc_str:
                msg = f"segmento con nombre '{dto.name}' ya existe"
                raise SegmentDuplicateNameError(msg) from exc
            raise
        await self._outbox_service.enqueue_async_from_sync_caller(
            to_domain_event(
                SegmentCreated(
                    tenant_id=tenant_id,
                    segment_id=segment.id,
                    occurred_at=now,
                )
            ),
            session=session,
        )
        # Invalidate estimate cache for tenant (new segment, no estimate yet)
        await self._cache.invalidate_pattern(f"segments:estimate:{tenant_id}:*")
        logger.info(
            "segment_service_create",
            tenant_id=str(tenant_id),
            segment_id=str(segment.id),
            name=segment.name,
        )
        return segment

    async def get(
        self,
        tenant_id: UUID,
        segment_id: UUID,
        *,
        session: AsyncSession,
    ) -> Segment:
        """Get segment. Raises SegmentNotFoundError if not found."""
        seg = await self._repo.get_by_id(segment_id, tenant_id, session=session)
        if seg is None or seg.deleted_at is not None:
            raise SegmentNotFoundError(str(segment_id))
        return seg

    async def list(
        self,
        tenant_id: UUID,
        *,
        session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
    ) -> PaginatedResponse[SegmentResponse]:
        """Paginated list of segments for tenant."""
        from src.modules.campaigns.application.dtos.pagination import PaginatedResponse
        from src.modules.campaigns.application.dtos.segment_dtos import SegmentResponse

        if not (1 <= limit <= 100):
            from src.modules.campaigns.application.services.campaign_service import (
                CampaignServiceError,
            )

            msg = "limit fuera de rango [1, 100]"
            raise CampaignServiceError(msg)
        items = await self._repo.list_by_tenant(tenant_id, session=session, limit=limit, offset=offset)
        # For total count we do a separate query (list_by_tenant doesn't return count)
        total_items = await self._repo.list_by_tenant(tenant_id, session=session, limit=10000, offset=0)
        total = len(total_items)
        return PaginatedResponse(
            items=[SegmentResponse.model_validate(s) for s in items],
            total_count=total,
            limit=limit,
            offset=offset,
            has_more=(offset + len(items)) < total,
        )

    async def update(
        self,
        tenant_id: UUID,
        segment_id: UUID,
        dto: SegmentUpdate,
        *,
        session: AsyncSession,
    ) -> Segment:
        """Update segment. Invalidates estimate_size cache."""
        seg = await self.get(tenant_id, segment_id, session=session)
        now = utc_now()
        updated = seg.model_copy(
            update={
                **dto.model_dump(exclude_unset=True, exclude_none=False),
                "updated_at": now,
                "estimated_size": None,  # invalidate on filter change
                "last_calculated_at": None,
            }
        )
        await self._repo.update(updated, session=session)
        # Invalidate estimate cache
        await self._cache.invalidate(f"segments:estimate:{tenant_id}:{segment_id}")
        logger.info(
            "segment_service_update",
            tenant_id=str(tenant_id),
            segment_id=str(segment_id),
        )
        return updated

    async def delete(
        self,
        tenant_id: UUID,
        segment_id: UUID,
        *,
        session: AsyncSession,
    ) -> None:
        """Soft delete segment."""
        seg = await self.get(tenant_id, segment_id, session=session)
        await self._repo.soft_delete(seg.id, tenant_id, session=session)
        await self._cache.invalidate(f"segments:estimate:{tenant_id}:{segment_id}")
        logger.info(
            "segment_service_delete",
            tenant_id=str(tenant_id),
            segment_id=str(segment_id),
        )

    async def resolve(
        self,
        tenant_id: UUID,
        segment_id: UUID,
        *,
        at: dt.datetime | None = None,
        limit: int = 10_000,
        session: AsyncSession,
    ) -> tuple[list[UUID], int, bool]:
        """SQL-side filtering. NEVER loads leads in Python.

        Returns:
            (lead_ids, lead_count, truncated)
            truncated=True if total exceeds limit.
        """
        seg = await self.get(tenant_id, segment_id, session=session)
        # 1. Compile filter_dsl → SQL predicate (pure function)
        filter_dsl = seg.filter_dsl
        if isinstance(filter_dsl, PredefinedSegmentFilter):
            predicate = self._filter_evaluator.to_sql_predicate(filter_dsl, tenant_id=tenant_id, at=at)
        else:
            # Fallback: empty filter → no results
            from sqlalchemy import false

            predicate = false()

        # 2. SQL-side query (no Python loop over leads)
        lead_ids, total = await self._lead_query_port.list_lead_ids_matching(
            tenant_id=tenant_id,
            predicate=predicate,
            limit=limit,
            session=session,
        )
        truncated = total > limit
        logger.info(
            "segment_service_resolve",
            tenant_id=str(tenant_id),
            segment_id=str(segment_id),
            lead_count=total,
            returned=len(lead_ids),
            truncated=truncated,
        )
        return lead_ids, total, truncated

    async def estimate_size(
        self,
        tenant_id: UUID,
        segment_id: UUID,
        *,
        session: AsyncSession,
    ) -> tuple[int, dt.datetime, bool]:
        """Cached count. Returns (estimated_size, cached_at, cache_hit)."""
        cache_key = f"segments:estimate:{tenant_id}:{segment_id}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return cached["size"], cached["at"], True

        seg = await self.get(tenant_id, segment_id, session=session)
        filter_dsl = seg.filter_dsl
        if isinstance(filter_dsl, PredefinedSegmentFilter):
            predicate = self._filter_evaluator.to_sql_predicate(filter_dsl, tenant_id=tenant_id)
        else:
            from sqlalchemy import false

            predicate = false()

        size = await self._lead_query_port.count_leads_matching(
            tenant_id=tenant_id,
            predicate=predicate,
            session=session,
        )
        now = utc_now()
        await self._cache.set(cache_key, {"size": size, "at": now}, ttl=self.ESTIMATE_CACHE_TTL)
        # Persist hint on segment (best-effort)
        try:
            await self._repo.update(
                seg.model_copy(update={"estimated_size": size, "last_calculated_at": now, "updated_at": now}),
                session=session,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "segment_estimate_size_persist_failed",
                tenant_id=str(tenant_id),
                segment_id=str(segment_id),
                error=str(exc),
            )
        return size, now, False

    async def snapshot(
        self,
        tenant_id: UUID,
        segment_id: UUID,
        *,
        session: AsyncSession,
        max_lead_ids: int = 100_000,
    ) -> SegmentSnapshot:
        """Materialize segment. Emits SegmentSnapshotted event."""
        lead_ids, total, truncated = await self.resolve(
            tenant_id,
            segment_id,
            limit=max_lead_ids,
            session=session,
        )
        if truncated:
            logger.warning(
                "segment_snapshot_truncated",
                tenant_id=str(tenant_id),
                segment_id=str(segment_id),
                total=total,
                cap=max_lead_ids,
            )
        now = utc_now()
        snap = SegmentSnapshot(
            id=uuid4(),
            tenant_id=tenant_id,
            segment_id=segment_id,
            snapshotted_at=now,
            lead_ids=lead_ids,
            lead_count=len(lead_ids),
            created_at=now,
        )
        await self._snapshot_repo.append(snap, session=session)
        await self._outbox_service.enqueue_async_from_sync_caller(
            to_domain_event(
                SegmentSnapshotted(
                    tenant_id=tenant_id,
                    segment_id=segment_id,
                    snapshot_id=snap.id,
                    lead_count=snap.lead_count,
                    occurred_at=now,
                )
            ),
            session=session,
        )
        logger.info(
            "segment_service_snapshot",
            tenant_id=str(tenant_id),
            segment_id=str(segment_id),
            snapshot_id=str(snap.id),
            lead_count=snap.lead_count,
        )
        return snap
