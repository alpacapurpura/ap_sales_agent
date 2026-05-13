"""ARQ cron — promote scheduled campaigns + claim pending tasks.

Algorithm:
  Phase A — promote scheduled campaigns:
    SELECT campaigns WHERE status='scheduled' AND scheduled_at <= now() LIMIT 100.
    For each: CampaignOrchestrator.launch(tenant_id, campaign_id).
    @idempotent makes re-tick safe within TTL.

  Phase B — claim pending CampaignTasks:
    CampaignTaskRepository.claim_pending_for_worker(tenant_id=None,
    scheduled_before=now(), batch_size=100).
    For each claimed task → ARQ enqueue_job("run_campaign_execution_task", str(task.id)).

Cron offset: minute={5,15,25,35,45,55} — disjoint from analytics run_tick_scheduler
(minute=range(60)) to avoid DB connection pile-up.

job_timeout=30s hard ceiling. Each phase capped at LIMIT 100 (sufficient at 1000 tenants).

Cross-tenant SELECT in Phase A and B is documented in
test_campaigns_tenant_isolation.py allowlist (same pattern as outbox.claim_pending).

PR-5 PI-1 S2.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    import datetime as dt
    from uuid import UUID

    from luana_core_campaigns.application.services.orchestrator import CampaignOrchestrator
    from sqlalchemy.ext.asyncio import AsyncSession

from luana_core_platform.domain.datetime_utils import utc_now

logger = structlog.get_logger(__name__)

_PHASE_A_LIMIT = 100
_PHASE_B_BATCH = 100
_EXECUTION_QUEUE_NAME = "arq:campaigns_execution"
_PHASE_A_WARNING_SECONDS = 20  # warn if phase A takes >20s


async def run_campaign_scheduler_tick(ctx: dict) -> dict[str, int]:
    """ARQ cron entry — promote campaigns + claim pending tasks.

    Args:
        ctx: ARQ context with ``db_factory``, ``redis_cache`` keys.

    Returns:
        Dict with ``promoted`` (int) and ``tasks_enqueued`` (int).
    """
    db_factory = ctx["db_factory"]
    redis_cache = ctx.get("redis_cache")

    promoted = 0
    tasks_enqueued = 0
    now = utc_now()

    async with db_factory() as session:
        # ── Phase A: promote scheduled campaigns ──────────────────────────────
        promoted, phase_a_duration = await _phase_a_promote(session, now)

        if phase_a_duration > _PHASE_A_WARNING_SECONDS:
            logger.warning(
                "scheduler_tick_phase_a_slow",
                duration_seconds=phase_a_duration,
                promoted=promoted,
            )

        # ── Phase B: claim pending tasks + enqueue ────────────────────────────
        tasks_enqueued = await _phase_b_claim_and_enqueue(session, now, ctx)

    # Heartbeat (mirrors analytics scheduler heartbeat pattern)
    if redis_cache is not None:
        try:
            await redis_cache.setex("campaigns:scheduler:last_tick", 600, "1")
        except Exception:  # noqa: BLE001
            logger.warning("scheduler_tick_heartbeat_failed")

    logger.info(
        "scheduler_tick_complete",
        promoted=promoted,
        tasks_enqueued=tasks_enqueued,
    )
    return {"promoted": promoted, "tasks_enqueued": tasks_enqueued}


async def _phase_a_promote(session: AsyncSession, now: dt.datetime) -> tuple[int, float]:
    """Promote campaigns with scheduled_at <= now → launch via orchestrator.

    Returns (promoted_count, duration_seconds).
    """
    import time

    from luana_core_campaigns.infrastructure.models.campaign_model import CampaignModel
    from sqlalchemy import select

    start = time.monotonic()
    promoted = 0

    stmt = (
        select(CampaignModel)
        .where(
            CampaignModel.status == "scheduled",
            CampaignModel.scheduled_at <= now,
            CampaignModel.deleted_at.is_(None),
        )
        .limit(_PHASE_A_LIMIT)
    )
    result = await session.execute(stmt)
    rows = result.scalars().all()

    for row in rows:
        try:
            await _launch_campaign_safe(session, row.tenant_id, row.id)
            promoted += 1
        except Exception:  # noqa: BLE001
            logger.warning(
                "scheduler_tick_launch_failed",
                campaign_id=str(row.id),
                tenant_id=str(row.tenant_id),
                exc_info=True,
            )

    duration = time.monotonic() - start
    return promoted, duration


async def _launch_campaign_safe(session: AsyncSession, tenant_id: UUID, campaign_id: UUID) -> None:
    """Launch a single campaign via orchestrator. Errors logged, not propagated."""
    orchestrator = await _build_orchestrator_standalone()
    result = await orchestrator.launch(
        tenant_id=tenant_id,
        campaign_id=campaign_id,
        session=session,
    )
    logger.info(
        "scheduler_tick_campaign_launched",
        campaign_id=str(campaign_id),
        tenant_id=str(tenant_id),
        tasks_generated=result.tasks_generated,
        status=result.status,
    )


async def _build_orchestrator_standalone() -> CampaignOrchestrator:
    """Build a CampaignOrchestrator suitable for worker context (no FastAPI DI).

    PR-5 Sub-G: uses LeadQueryServiceImpl from crm.application.services
    (correct path). Workers need standalone composition root — same cross-module
    import as api/_service_factories.py, justified in KNOWN_CROSS_MODULE_IMPORTS.
    """
    from luana_core_campaigns.application.segment_filter_evaluator import (
        SegmentFilterEvaluator,
    )
    from luana_core_campaigns.application.services.audit_log_service import AuditLogService
    from luana_core_campaigns.application.services.cache import SimpleTTLCache
    from luana_core_campaigns.application.services.orchestrator import CampaignOrchestrator
    from luana_core_campaigns.application.services.segment_service import SegmentService
    from luana_core_campaigns.infrastructure.repositories.audit_log_repo_impl import (
        AuditLogRepositoryImpl,
    )
    from luana_core_campaigns.infrastructure.repositories.campaign_repository_impl import (
        CampaignRepositoryImpl,
    )
    from luana_core_campaigns.infrastructure.repositories.campaign_step_repository_impl import (
        CampaignStepRepositoryImpl,
    )
    from luana_core_campaigns.infrastructure.repositories.campaign_task_repository_impl import (
        CampaignTaskRepositoryImpl,
    )
    from luana_core_campaigns.infrastructure.repositories.segment_repository_impl import (
        SegmentRepositoryImpl,
    )
    from luana_core_campaigns.infrastructure.repositories.segment_snapshot_repository_impl import (
        SegmentSnapshotRepositoryImpl,
    )
    from luana_core_crm.application.services.lead_query_service import (
        LeadQueryServiceImpl,
    )
    from luana_core_events.outbox.application.outbox_service import OutboxService
    from luana_core_events.outbox.infrastructure.repository import (
        OutboxRepositoryImpl,
    )

    _cache = SimpleTTLCache(max_entries=256)
    outbox_svc = OutboxService(repo=OutboxRepositoryImpl())

    return CampaignOrchestrator(
        campaign_repo=CampaignRepositoryImpl(),
        step_repo=CampaignStepRepositoryImpl(),
        task_repo=CampaignTaskRepositoryImpl(),
        segment_service=SegmentService(
            repo=SegmentRepositoryImpl(),
            snapshot_repo=SegmentSnapshotRepositoryImpl(),
            lead_query_port=LeadQueryServiceImpl(),  # type: ignore[arg-type]
            filter_evaluator=SegmentFilterEvaluator(),
            outbox_service=outbox_svc,
            cache=_cache,
        ),
        outbox_service=outbox_svc,
        audit_log_service=AuditLogService(repo=AuditLogRepositoryImpl()),
        arq_pool_provider=_arq_pool_provider_fn,
    )


async def _arq_pool_provider_fn() -> object:
    """Lazy ARQ pool for worker context."""
    try:
        from arq import create_pool
        from arq.connections import RedisSettings
        from luana_core_platform.core.config import settings as app_settings

        return await create_pool(RedisSettings.from_dsn(app_settings.REDIS_URL))
    except Exception:  # noqa: BLE001
        logger.warning("scheduler_tick_arq_pool_unavailable_in_provider")
        return None


async def _phase_b_claim_and_enqueue(session: AsyncSession, now: dt.datetime, ctx: dict[str, Any]) -> int:
    """Claim pending tasks and enqueue to ARQ.

    Returns tasks_enqueued count.
    """
    from luana_core_campaigns.infrastructure.repositories.campaign_task_repository_impl import (
        CampaignTaskRepositoryImpl,
    )

    task_repo = CampaignTaskRepositoryImpl()
    tasks = await task_repo.claim_pending_for_worker(
        tenant_id=None,
        scheduled_before=now,
        batch_size=_PHASE_B_BATCH,
        session=session,
    )

    enqueued = 0
    arq_pool = ctx.get("redis")  # MockArqRedis in tests; real pool in prod
    if arq_pool is None:
        # Try to get a real ARQ pool from env
        try:
            from arq import create_pool
            from arq.connections import RedisSettings
            from luana_core_platform.core.config import settings as app_settings

            arq_pool = await create_pool(RedisSettings.from_dsn(app_settings.REDIS_URL))
        except Exception:  # noqa: BLE001
            logger.warning("scheduler_tick_arq_pool_unavailable")
            return 0

    for task in tasks:
        try:
            await arq_pool.enqueue_job(
                "run_campaign_execution_task",
                str(task.id),
                _queue_name=_EXECUTION_QUEUE_NAME,
            )
            enqueued += 1
        except Exception:  # noqa: BLE001
            logger.warning(
                "scheduler_tick_enqueue_failed",
                task_id=str(task.id),
                exc_info=True,
            )

    return enqueued
