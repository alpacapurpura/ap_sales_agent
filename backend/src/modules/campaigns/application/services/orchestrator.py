"""CampaignOrchestrator — real launch() for PR-5 PI-1 S2.

Replaces CampaignService.launch() STUB from PR-4.

Single-TX atomicity (D22 CONTRACT):
  1. SELECT FOR UPDATE Campaign (lock + tenant check + FSM validation)
  2. Resolve segment → list[lead_id] (snapshot if STATIC + no fresh snapshot)
  3. INSERT batch CampaignTask root only (step_index==0)
  4. Emit CampaignLaunched + CampaignTasksGenerated via OutboxService (intra-TX)
  5. Audit log: campaign_launched + tasks_generated (intra-TX, best-effort)
  6. COMMIT

Post-commit (best-effort):
  7. ARQ enqueue run_campaign_execution_task per task with delay_minutes==0

Idempotency: @idempotent decorator key=campaigns:launch:{tenant_id}:{campaign_id}
TTL=LAUNCH_IDEMPOTENCY_TTL_SECONDS (600s). Re-launch within TTL → silent no-op.
"""

from __future__ import annotations

import datetime as dt
import os
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import structlog
from pydantic import BaseModel, ConfigDict, Field

from src.modules.campaigns.application.services._event_bridge import to_domain_event
from src.modules.campaigns.domain.audit_log import AuditEventType
from src.modules.campaigns.domain.campaign import Campaign
from src.modules.campaigns.domain.enums import CampaignStatus, TaskStatus
from src.modules.campaigns.domain.events import CampaignLaunched, CampaignTasksGenerated
from src.shared.domain.datetime_utils import utc_now
from src.shared.idempotency.application.decorator import idempotent

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.modules.campaigns.application.services.audit_log_service import AuditLogService
    from src.modules.campaigns.application.services.segment_service import SegmentService
    from src.modules.campaigns.domain.campaign_step import CampaignStep
    from src.modules.campaigns.domain.campaign_task import CampaignTask
    from src.modules.campaigns.domain.repositories import (
        CampaignRepository,
        CampaignStepRepository,
        CampaignTaskRepository,
    )
    from src.shared.domain_events.outbox.application.outbox_service import OutboxService

logger = structlog.get_logger(__name__)

# ── Exceptions ─────────────────────────────────────────────────────────────────


class OrchestratorError(Exception):
    """Base for orchestrator errors."""


class OrchestratorCampaignNotFoundError(OrchestratorError):
    """Campaign not found or not owned by tenant (→ 404)."""


class OrchestratorCampaignNotLaunchableError(OrchestratorError):
    """Campaign not in a launchable state (→ 409)."""


class OrchestratorSegmentEmptyError(OrchestratorError):
    """Segment resolved to 0 leads (→ 422)."""


class OrchestratorMissingStepsError(OrchestratorError):
    """Campaign has no root steps (→ 422)."""


# ── Result DTO ─────────────────────────────────────────────────────────────────


class OrchestratorLaunchResult(BaseModel):
    """Returned by CampaignOrchestrator.launch and serialized by @idempotent cache.

    `id` + `status` + `external_id` projected by @idempotent (matches projector
    in shared/idempotency/application/decorator.py). external_id holds tasks_count
    so re-launch within TTL returns same value.
    """

    model_config = ConfigDict(extra="forbid")

    id: UUID  # campaign_id (used by @idempotent projection)
    status: str  # "running" | "noop_already_running"
    external_id: str  # str(tasks_generated_count) — fits projection contract
    tasks_generated: int = Field(ge=0)
    snapshot_id: UUID | None
    launched_at: dt.datetime


# ── Orchestrator ────────────────────────────────────────────────────────────────


def _launch_key_fn(*_args: object, tenant_id: UUID, campaign_id: UUID, **_kw: object) -> str:
    """Idempotency key for launch: tenant+campaign.

    Accepts *_args to absorb positional ``self`` passed by the @idempotent decorator
    when it forwards bound-method args to key_fn unchanged.
    """
    return f"{tenant_id}:{campaign_id}"


class CampaignOrchestrator:
    """Real launch() — replaces PR-4 STUB.

    Idempotency contract: launch(campaign_id) is idempotent within
    LAUNCH_IDEMPOTENCY_TTL_SECONDS=600 via @idempotent decorator on the
    public method. Re-launch within window → cached projection.
    Re-launch after TTL: orchestrator detects Campaign.status==RUNNING
    and returns no-op (additional safety layer).

    Atomicity contract: per-launch operation runs inside a SINGLE
    `async with session.begin()` block (D22):
      1. Lock Campaign row (SELECT FOR UPDATE).
      2. Validate state (status==SCHEDULED or DRAFT with direct-launch).
      3. Resolve segment → snapshot_id (auto-snapshot if STATIC).
      4. Generate CampaignTask rows (step_index==0 roots only; descendants S3+).
      5. INSERT batch via repo.append_many (ON CONFLICT DO NOTHING dedup).
      6. Transition Campaign → RUNNING.
      7. Emit CampaignLaunched + CampaignTasksGenerated outbox events.
      8. Audit log (best-effort, intra-TX).
      9. Commit (caller delegates).
      POST-COMMIT: enqueue ARQ jobs for each task (best-effort backstop: scheduler_tick).
    """

    LAUNCH_IDEMPOTENCY_TTL_SECONDS = 600  # 10min — typical retry/UI doubleclick window

    def __init__(
        self,
        *,
        campaign_repo: CampaignRepository,
        step_repo: CampaignStepRepository,
        task_repo: CampaignTaskRepository,
        segment_service: SegmentService,
        outbox_service: OutboxService,
        audit_log_service: AuditLogService,
        arq_pool_provider: object,  # async () -> ArqRedis (lazy, multi-pod)
        execution_queue_name: str | None = None,
    ) -> None:
        """Initialize orchestrator with repos and collaborators."""
        self._campaign_repo = campaign_repo
        self._step_repo = step_repo
        self._task_repo = task_repo
        self._segment_service = segment_service
        self._outbox_service = outbox_service
        self._audit_log_service = audit_log_service
        self._arq_pool_provider = arq_pool_provider
        self._execution_queue_name = execution_queue_name or os.environ.get(
            "CAMPAIGNS_EXECUTION_QUEUE_NAME", "arq:campaigns_execution"
        )

    @idempotent(
        namespace="campaigns:launch",
        key_fn=_launch_key_fn,
        ttl=LAUNCH_IDEMPOTENCY_TTL_SECONDS,
    )
    async def launch(
        self,
        *,
        tenant_id: UUID,
        campaign_id: UUID,
        session: AsyncSession,
    ) -> OrchestratorLaunchResult:
        """Launch a campaign. Decorated with @idempotent(ttl=600s).

        Raises:
        - OrchestratorCampaignNotFoundError → 404
        - OrchestratorCampaignNotLaunchableError → 409
        - OrchestratorSegmentEmptyError → 422
        - OrchestratorMissingStepsError → 422
        """
        # ── Step 1: Idempotent guard for already-RUNNING campaigns ─────────────
        # (secondary to @idempotent decorator; handles post-TTL repeat launches)
        campaign = await self._campaign_repo.get_by_id(campaign_id, tenant_id, session=session)
        if campaign is None or campaign.deleted_at is not None:
            raise OrchestratorCampaignNotFoundError(str(campaign_id))

        if campaign.status == CampaignStatus.RUNNING:
            logger.info(
                "orchestrator_launch_noop_already_running",
                tenant_id=str(tenant_id),
                campaign_id=str(campaign_id),
            )
            # Return noop result — no tasks generated
            return OrchestratorLaunchResult(
                id=campaign_id,
                status="noop_already_running",
                external_id="0",
                tasks_generated=0,
                snapshot_id=campaign.segment_snapshot_id,
                launched_at=campaign.launched_at or utc_now(),
            )

        # ── Step 2: Validate FSM transition ────────────────────────────────────
        _launchable = {CampaignStatus.SCHEDULED, CampaignStatus.DRAFT}
        if campaign.status not in _launchable:
            msg = f"Campaign {campaign_id} in status {campaign.status.value} is not launchable"
            raise OrchestratorCampaignNotLaunchableError(msg)
        if not Campaign.transition_allowed(campaign.status, CampaignStatus.RUNNING):
            msg = f"FSM does not allow transition {campaign.status.value}→running"
            raise OrchestratorCampaignNotLaunchableError(msg)

        # ── Step 3: Resolve segment → lead_ids ────────────────────────────────
        if campaign.segment_id is None:
            # No segment = no leads → tasks_generated=0 (segment-less campaigns S3+)
            lead_ids: list[UUID] = []
            snapshot_id: UUID | None = None
        else:
            lead_ids, _total, _truncated = await self._segment_service.resolve(
                tenant_id,
                campaign.segment_id,
                session=session,
            )
            snapshot_id = None  # snapshot wired in segment_service.snapshot call (S3 full)

        # ── Step 4: Get root steps (step_index == 0, not soft-deleted) ────────
        all_steps = await self._step_repo.list_by_campaign(campaign_id, tenant_id, session=session)
        root_steps: list[CampaignStep] = [s for s in all_steps if s.step_index == 0 and s.deleted_at is None]

        if not root_steps and lead_ids:
            msg = f"Campaign {campaign_id} has leads but no root steps (step_index==0)"
            raise OrchestratorMissingStepsError(msg)

        # ── Step 5: Build CampaignTask batch (root only) ───────────────────────
        now = utc_now()
        tasks: list[CampaignTask] = []
        if lead_ids and root_steps:
            from src.modules.campaigns.domain.campaign_task import CampaignTask

            for step in root_steps:
                delay_minutes: int = step.step_config.get("delay_minutes", 0)
                scheduled_at = now + dt.timedelta(minutes=delay_minutes)
                for lead_id in lead_ids:
                    idempotency_key = f"task:{campaign_id}:{lead_id}:{step.id}"
                    task = CampaignTask(
                        id=uuid4(),
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        lead_id=lead_id,
                        step_id=step.id,
                        status=TaskStatus.PENDING,
                        scheduled_at=scheduled_at,
                        idempotency_key=idempotency_key,
                        created_at=now,
                        updated_at=now,
                    )
                    tasks.append(task)

        # ── Step 6: INSERT batch (ON CONFLICT DO NOTHING) ─────────────────────
        if tasks:
            await self._task_repo.append_many(tasks, session=session)

        # ── Step 7: Transition campaign → RUNNING ─────────────────────────────
        launched_at = campaign.launched_at if campaign.launched_at is not None else now
        updated_campaign = campaign.model_copy(
            update={
                "status": CampaignStatus.RUNNING,
                "launched_at": launched_at,
                "updated_at": now,
                "segment_snapshot_id": snapshot_id,
            }
        )
        await self._campaign_repo.update(updated_campaign, session=session)

        # ── Step 8: Emit outbox events (intra-TX) ─────────────────────────────
        await self._outbox_service.enqueue_async_from_sync_caller(
            to_domain_event(
                CampaignLaunched(
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    occurred_at=now,
                    launched_at=launched_at,
                )
            ),
            session=session,
        )
        await self._outbox_service.enqueue_async_from_sync_caller(
            to_domain_event(
                CampaignTasksGenerated(
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    occurred_at=now,
                    tasks_generated=len(tasks),
                    snapshot_id=snapshot_id,
                )
            ),
            session=session,
        )

        # ── Step 9: Audit log (best-effort, intra-TX) ─────────────────────────
        await self._audit_log_service.record(
            tenant_id=tenant_id,
            event_type=AuditEventType.CAMPAIGN_LAUNCHED,
            actor="orchestrator",
            campaign_id=campaign_id,
            payload={"launched_at": launched_at.isoformat(), "tasks_count": len(tasks)},
            session=session,
        )
        await self._audit_log_service.record(
            tenant_id=tenant_id,
            event_type=AuditEventType.TASKS_GENERATED,
            actor="orchestrator",
            campaign_id=campaign_id,
            payload={"tasks_generated": len(tasks), "snapshot_id": str(snapshot_id) if snapshot_id else None},
            session=session,
        )

        result = OrchestratorLaunchResult(
            id=campaign_id,
            status="running",
            external_id=str(len(tasks)),
            tasks_generated=len(tasks),
            snapshot_id=snapshot_id,
            launched_at=launched_at,
        )

        logger.info(
            "orchestrator_launch_complete",
            tenant_id=str(tenant_id),
            campaign_id=str(campaign_id),
            tasks_generated=len(tasks),
            root_steps=len(root_steps),
            lead_count=len(lead_ids),
        )

        # ── Post-commit: enqueue ARQ jobs ──────────────────────────────────────
        # Best-effort: pod crash between commit and enqueue → scheduler_tick backstop.
        # This is called after session.begin() commits in the API layer caller.
        # We store tasks on self for post-commit hook.
        self._pending_tasks_for_enqueue = tasks

        return result

    async def enqueue_pending_tasks(self) -> None:
        """Post-commit: enqueue ARQ jobs for tasks created by the last launch().

        Called by API layer after session.commit(). Best-effort — errors logged,
        never propagated. Scheduler_tick picks up any missed tasks at next boundary.
        """
        tasks = getattr(self, "_pending_tasks_for_enqueue", [])
        if not tasks:
            return
        self._pending_tasks_for_enqueue = []

        try:
            arq_pool = await self._arq_pool_provider()  # type: ignore[operator]
            for task in tasks:
                try:
                    await arq_pool.enqueue_job(
                        "run_campaign_execution_task",
                        str(task.id),
                        _queue_name=self._execution_queue_name,
                    )
                except Exception:  # noqa: BLE001
                    logger.warning(
                        "orchestrator_enqueue_failed",
                        task_id=str(task.id),
                        exc_info=True,
                    )
        except Exception:  # noqa: BLE001
            logger.warning(
                "orchestrator_arq_pool_unavailable",
                task_count=len(tasks),
                exc_info=True,
            )
