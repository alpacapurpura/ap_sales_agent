"""ARQ cron — refresh STATIC segments linked to RUNNING campaigns.

Scope narrow (D26 architect decision):
- Only segments STATIC linked to campaigns with status=RUNNING.
- Only segments with (now - last_calculated_at) > REFRESH_THRESHOLD_MINUTES (default 60).
- Cap 50 segments per tick to avoid CPU spike.

Env: CAMPAIGNS_SEGMENT_REFRESH_INTERVAL_HOURS=1 (default; tunable).

Each snapshot is its own transaction — failure of one segment does not block others.
Audit log NOT emitted per-segment (volume noise); covered by SegmentSnapshotted outbox
event emitted by SegmentService.snapshot.

Cross-tenant SELECT is allowlisted — tenant isolation preserved inside loop
(each SegmentService.snapshot call scoped to tenant_id from the row).

Cron: minute=20 each hour (hourly at :20).

PR-5 PI-1 S2.
"""

from __future__ import annotations

import datetime as dt
import os
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from collections.abc import Callable
    from contextlib import AbstractAsyncContextManager
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from src.modules.campaigns.application.services.segment_service import SegmentService

from src.shared.domain.datetime_utils import utc_now

logger = structlog.get_logger(__name__)

_SEGMENT_REFRESH_CAP = 50
CAMPAIGNS_SEGMENT_REFRESH_INTERVAL_HOURS = "CAMPAIGNS_SEGMENT_REFRESH_INTERVAL_HOURS"


def _refresh_threshold_minutes() -> int:
    """Read refresh threshold from env. Default 60 minutes."""
    hours = float(os.environ.get(CAMPAIGNS_SEGMENT_REFRESH_INTERVAL_HOURS, "1"))
    return int(hours * 60)


async def run_segment_refresh_tick(ctx: dict) -> dict[str, int]:
    """ARQ cron entry — refresh stale STATIC segments for RUNNING campaigns.

    Args:
        ctx: ARQ context with ``db_factory`` key.

    Returns:
        Dict with ``refreshed`` (int) and ``errors`` (int).
    """
    import time

    db_factory = ctx["db_factory"]
    start = time.monotonic()
    refreshed = 0
    errors = 0

    threshold_minutes = _refresh_threshold_minutes()
    cutoff = utc_now() - dt.timedelta(minutes=threshold_minutes)

    # ── Query: stale STATIC segments linked to RUNNING campaigns ─────────────
    segments_to_refresh = await _query_stale_segments(db_factory, cutoff)

    logger.info(
        "segment_refresh_tick_start",
        candidate_count=len(segments_to_refresh),
        threshold_minutes=threshold_minutes,
    )

    # ── Refresh each segment in its own transaction ───────────────────────────
    for tenant_id, segment_id in segments_to_refresh:
        try:
            await _refresh_segment(db_factory, tenant_id, segment_id)
            refreshed += 1
        except Exception:  # noqa: BLE001
            errors += 1
            logger.warning(
                "segment_refresh_tick_segment_error",
                tenant_id=str(tenant_id),
                segment_id=str(segment_id),
                exc_info=True,
            )

    duration_ms = int((time.monotonic() - start) * 1000)
    logger.info(
        "segment_refresh_tick_complete",
        refreshed=refreshed,
        errors=errors,
        duration_ms=duration_ms,
    )
    return {"refreshed": refreshed, "errors": errors}


async def _query_stale_segments(
    db_factory: Callable[[], AbstractAsyncContextManager[AsyncSession]],
    cutoff: dt.datetime,
) -> list[tuple]:
    """Cross-tenant query: STATIC segments in RUNNING campaigns needing refresh.

    Cross-tenant SELECT allowlisted — same pattern as claim_pending_for_worker.
    Returns list of (tenant_id, segment_id) tuples.
    """
    from sqlalchemy import and_, select
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.modules.campaigns.infrastructure.models.campaign_model import CampaignModel
    from src.modules.campaigns.infrastructure.models.segment_model import SegmentModel

    async with db_factory() as session:
        if not isinstance(session, AsyncSession):
            msg = f"Expected AsyncSession, got {type(session)}"
            raise TypeError(msg)

        # JOIN segment ↔ campaign ON campaign.segment_id = segment.id
        # WHERE segment.segment_type='static'
        #   AND campaign.status='running'
        #   AND campaign.deleted_at IS NULL
        #   AND segment.deleted_at IS NULL
        #   AND (segment.last_calculated_at IS NULL OR segment.last_calculated_at < cutoff)
        stmt = (
            select(SegmentModel.tenant_id, SegmentModel.id)
            .join(CampaignModel, CampaignModel.segment_id == SegmentModel.id)
            .where(
                SegmentModel.segment_type == "static",
                SegmentModel.deleted_at.is_(None),
                CampaignModel.status == "running",
                CampaignModel.deleted_at.is_(None),
                and_((SegmentModel.last_calculated_at.is_(None)) | (SegmentModel.last_calculated_at < cutoff)),
            )
            .limit(_SEGMENT_REFRESH_CAP)
            .distinct()
        )
        result = await session.execute(stmt)
        rows = result.all()
        return [(row[0], row[1]) for row in rows]


async def _refresh_segment(
    db_factory: Callable[[], AbstractAsyncContextManager[AsyncSession]],
    tenant_id: UUID,
    segment_id: UUID,
) -> None:
    """Refresh a single segment in its own transaction.

    Calls SegmentService.snapshot which emits SegmentSnapshotted outbox event.
    """
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    if not isinstance(tenant_id, UUID):
        msg = f"Expected UUID for tenant_id, got {type(tenant_id)}"
        raise TypeError(msg)
    if not isinstance(segment_id, UUID):
        msg = f"Expected UUID for segment_id, got {type(segment_id)}"
        raise TypeError(msg)

    async with db_factory() as session:
        if not isinstance(session, AsyncSession):
            msg = f"Expected AsyncSession, got {type(session)}"
            raise TypeError(msg)

        segment_svc = _build_segment_service_standalone()
        await segment_svc.snapshot(tenant_id, segment_id, session=session)
        await session.commit()

        logger.info(
            "segment_refresh_tick_segment_refreshed",
            tenant_id=str(tenant_id),
            segment_id=str(segment_id),
        )


def _build_segment_service_standalone() -> SegmentService:
    """Build a SegmentService suitable for worker context (no FastAPI DI).

    PR-5 Sub-G: uses LeadQueryServiceImpl from crm.application.services
    (correct path). Workers need standalone composition root — same cross-module
    import as api/_service_factories.py, justified in KNOWN_CROSS_MODULE_IMPORTS.
    """
    from src.modules.campaigns.application.segment_filter_evaluator import SegmentFilterEvaluator
    from src.modules.campaigns.application.services.cache import SimpleTTLCache
    from src.modules.campaigns.application.services.segment_service import SegmentService
    from src.modules.campaigns.infrastructure.repositories.segment_repository_impl import (
        SegmentRepositoryImpl,
    )
    from src.modules.campaigns.infrastructure.repositories.segment_snapshot_repository_impl import (
        SegmentSnapshotRepositoryImpl,
    )
    from src.modules.crm.application.services.lead_query_service import LeadQueryServiceImpl
    from src.shared.domain_events.outbox.application.outbox_service import OutboxService
    from src.shared.domain_events.outbox.infrastructure.repository import OutboxRepositoryImpl

    return SegmentService(
        repo=SegmentRepositoryImpl(),
        snapshot_repo=SegmentSnapshotRepositoryImpl(),
        lead_query_port=LeadQueryServiceImpl(),  # type: ignore[arg-type]
        filter_evaluator=SegmentFilterEvaluator(),
        outbox_service=OutboxService(repo=OutboxRepositoryImpl()),
        cache=SimpleTTLCache(max_entries=256),
    )
