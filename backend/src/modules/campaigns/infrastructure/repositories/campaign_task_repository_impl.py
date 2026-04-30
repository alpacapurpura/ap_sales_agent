"""CampaignTaskRepository SQLAlchemy implementation.

Performance-critical for 1000+ tenants:
- claim_pending_for_worker uses FOR UPDATE SKIP LOCKED (same pattern as outbox)
- append_many uses INSERT ... ON CONFLICT DO NOTHING for bulk idempotent insert
- Partial index ix_campaign_task_worker_queue declared in migration 111
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

if TYPE_CHECKING:
    import datetime as dt
    from collections.abc import Sequence
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.campaigns.domain.campaign_task import CampaignTask
from src.modules.campaigns.domain.enums import TaskStatus
from src.modules.campaigns.domain.repositories import CampaignTaskRepository
from src.modules.campaigns.infrastructure.models.campaign_task_model import CampaignTaskModel

logger = structlog.get_logger()


class CampaignTaskRepositoryImpl(CampaignTaskRepository):
    """Async SQLAlchemy 2.0 implementation of CampaignTaskRepository."""

    async def append(self, task: CampaignTask, *, session: AsyncSession) -> None:
        """Persist a single CampaignTask."""
        row = self._to_model(task)
        session.add(row)
        logger.info(
            "campaign_task_repository_append",
            tenant_id=str(task.tenant_id),
            task_id=str(task.id),
            campaign_id=str(task.campaign_id),
            lead_id=str(task.lead_id),
            status=task.status.value,
        )

    async def append_many(self, tasks: Sequence[CampaignTask], *, session: AsyncSession) -> None:
        """Bulk insert tasks with idempotency dedup.

        INSERT ... ON CONFLICT (tenant_id, idempotency_key) DO NOTHING.
        Service layer PR-4 / S2 orchestrator uses this when launching
        a campaign over a snapshot of N leads.
        """
        if not tasks:
            return
        rows = [
            {
                "id": task.id,
                "tenant_id": task.tenant_id,
                "campaign_id": task.campaign_id,
                "lead_id": task.lead_id,
                "step_id": task.step_id,
                "status": task.status.value,
                "scheduled_at": task.scheduled_at,
                "dispatched_at": task.dispatched_at,
                "sent_at": task.sent_at,
                "executed_at": task.executed_at,
                "channel_used": task.channel_used,
                "external_message_id": task.external_message_id,
                "attempt_count": task.attempt_count,
                "last_error": task.last_error,
                "compliance_check": task.compliance_check,
                "outbox_event_id": task.outbox_event_id,
                "idempotency_key": task.idempotency_key,
                "created_at": task.created_at,
                "updated_at": task.updated_at,
                "deleted_at": task.deleted_at,
            }
            for task in tasks
        ]
        stmt = pg_insert(CampaignTaskModel).values(rows)
        stmt = stmt.on_conflict_do_nothing(
            constraint="uq_campaign_task_tenant_idem",
        )
        await session.execute(stmt)
        logger.info(
            "campaign_task_repository_append_many",
            task_count=len(tasks),
            campaign_id=str(tasks[0].campaign_id) if tasks else "n/a",
        )

    async def get_by_id(self, task_id: UUID, tenant_id: UUID, *, session: AsyncSession) -> CampaignTask | None:
        """Fetch by primary key, scoped to tenant. Excludes soft-deleted."""
        stmt = select(CampaignTaskModel).where(
            CampaignTaskModel.id == task_id,
            CampaignTaskModel.tenant_id == tenant_id,
            CampaignTaskModel.deleted_at.is_(None),
        )
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return CampaignTask.model_validate(row)

    async def claim_pending_for_worker(
        self,
        *,
        tenant_id: UUID | None,
        scheduled_before: dt.datetime,
        batch_size: int = 50,
        session: AsyncSession,
    ) -> Sequence[CampaignTask]:
        """Claim pending/scheduled tasks for worker execution.

        Cross-tenant capable when tenant_id=None (documented arch exception).
        Uses FOR UPDATE SKIP LOCKED for high-throughput worker queue at 1000+ tenants.
        """
        pending_statuses = [TaskStatus.PENDING.value, TaskStatus.SCHEDULED.value]
        stmt = (
            select(CampaignTaskModel)
            .where(
                CampaignTaskModel.status.in_(pending_statuses),
                CampaignTaskModel.scheduled_at <= scheduled_before,
                CampaignTaskModel.deleted_at.is_(None),
            )
            .order_by(CampaignTaskModel.scheduled_at.asc())
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )
        if tenant_id is not None:
            stmt = stmt.where(CampaignTaskModel.tenant_id == tenant_id)

        result = await session.execute(stmt)
        rows = result.scalars().all()

        if rows:
            row_ids = [row.id for row in rows]
            update_stmt = (
                update(CampaignTaskModel)
                .where(CampaignTaskModel.id.in_(row_ids))
                .values(
                    status=TaskStatus.DISPATCHED.value,
                    dispatched_at=func.now(),
                    updated_at=func.now(),
                )
            )
            await session.execute(update_stmt)
            logger.info(
                "campaign_task_repository_claim_pending",
                claimed_count=len(rows),
                tenant_id=str(tenant_id) if tenant_id else "all",
            )

        return [CampaignTask.model_validate(row) for row in rows]

    async def mark_dispatched(
        self,
        task_id: UUID,
        tenant_id: UUID,
        *,
        outbox_event_id: UUID | None,
        session: AsyncSession,
    ) -> None:
        """Transition task to DISPATCHED status with optional outbox link."""
        stmt = (
            update(CampaignTaskModel)
            .where(
                CampaignTaskModel.id == task_id,
                CampaignTaskModel.tenant_id == tenant_id,
            )
            .values(
                status=TaskStatus.DISPATCHED.value,
                dispatched_at=func.now(),
                outbox_event_id=outbox_event_id,
                updated_at=func.now(),
            )
        )
        await session.execute(stmt)
        logger.info(
            "campaign_task_repository_mark_dispatched",
            tenant_id=str(tenant_id),
            task_id=str(task_id),
        )

    async def mark_sent(
        self,
        task_id: UUID,
        tenant_id: UUID,
        *,
        external_message_id: str | None,
        channel_used: str,
        session: AsyncSession,
    ) -> None:
        """Transition task to SENT status with channel resolution data."""
        stmt = (
            update(CampaignTaskModel)
            .where(
                CampaignTaskModel.id == task_id,
                CampaignTaskModel.tenant_id == tenant_id,
            )
            .values(
                status=TaskStatus.SENT.value,
                sent_at=func.now(),
                executed_at=func.now(),
                external_message_id=external_message_id,
                channel_used=channel_used,
                updated_at=func.now(),
            )
        )
        await session.execute(stmt)
        logger.info(
            "campaign_task_repository_mark_sent",
            tenant_id=str(tenant_id),
            task_id=str(task_id),
            channel_used=channel_used,
        )

    async def mark_failed(
        self,
        task_id: UUID,
        tenant_id: UUID,
        *,
        error_code: str,
        error_message: str,
        session: AsyncSession,
    ) -> None:
        """Transition task to FAILED status with error details."""
        stmt = (
            update(CampaignTaskModel)
            .where(
                CampaignTaskModel.id == task_id,
                CampaignTaskModel.tenant_id == tenant_id,
            )
            .values(
                status=TaskStatus.FAILED.value,
                executed_at=func.now(),
                last_error=f"[{error_code}] {error_message}"[:2000],
                attempt_count=CampaignTaskModel.attempt_count + 1,
                updated_at=func.now(),
            )
        )
        await session.execute(stmt)
        logger.info(
            "campaign_task_repository_mark_failed",
            tenant_id=str(tenant_id),
            task_id=str(task_id),
            error_code=error_code,
        )

    async def mark_skipped(
        self,
        task_id: UUID,
        tenant_id: UUID,
        *,
        reason: str,
        compliance_check: dict | None,
        session: AsyncSession,
    ) -> None:
        """Transition task to SKIPPED status (compliance/rate/budget gate refused)."""
        stmt = (
            update(CampaignTaskModel)
            .where(
                CampaignTaskModel.id == task_id,
                CampaignTaskModel.tenant_id == tenant_id,
            )
            .values(
                status=TaskStatus.SKIPPED.value,
                executed_at=func.now(),
                last_error=reason[:2000],
                compliance_check=compliance_check,
                updated_at=func.now(),
            )
        )
        await session.execute(stmt)
        logger.info(
            "campaign_task_repository_mark_skipped",
            tenant_id=str(tenant_id),
            task_id=str(task_id),
            reason=reason,
        )

    async def count_by_campaign_status(
        self,
        campaign_id: UUID,
        tenant_id: UUID,
        *,
        session: AsyncSession,
    ) -> dict[TaskStatus, int]:
        """Count tasks per status for a campaign. For GET /campaigns/{id}/stats (S3)."""
        stmt = (
            select(CampaignTaskModel.status, func.count(CampaignTaskModel.id))
            .where(
                CampaignTaskModel.campaign_id == campaign_id,
                CampaignTaskModel.tenant_id == tenant_id,
                CampaignTaskModel.deleted_at.is_(None),
            )
            .group_by(CampaignTaskModel.status)
        )
        result = await session.execute(stmt)
        rows = result.all()
        return {TaskStatus(status_val): count for status_val, count in rows}

    @staticmethod
    def _to_model(task: CampaignTask) -> CampaignTaskModel:
        """Convert domain entity to SQLAlchemy model."""
        return CampaignTaskModel(
            id=task.id,
            tenant_id=task.tenant_id,
            campaign_id=task.campaign_id,
            lead_id=task.lead_id,
            step_id=task.step_id,
            status=task.status.value,
            scheduled_at=task.scheduled_at,
            dispatched_at=task.dispatched_at,
            sent_at=task.sent_at,
            executed_at=task.executed_at,
            channel_used=task.channel_used,
            external_message_id=task.external_message_id,
            attempt_count=task.attempt_count,
            last_error=task.last_error,
            compliance_check=task.compliance_check,
            outbox_event_id=task.outbox_event_id,
            idempotency_key=task.idempotency_key,
            created_at=task.created_at,
            updated_at=task.updated_at,
            deleted_at=task.deleted_at,
        )
