"""ARQ worker — process a single CampaignTask by id.

Dequeued by SchedulerSettings.cron or enqueued directly by CampaignOrchestrator
post-commit. One ARQ job per CampaignTask.

Algorithm:
1. Open AsyncSession; SELECT FOR UPDATE the task row (exclusivity vs parallel retry).
2. If status != 'pending'/'scheduled' → noop (race / already processed).
3. Resolve channel via ChannelRouterRegistry.get(step.channel_priority[0]).
4. router.send(...) wrapped inside TelegramChannelRouter's own CircuitBreaker.
5. Map result / error → action:
   - success=True            → mark_sent + audit task_sent
   - CircuitBreakerOpenError → mark_failed error_code='circuit_open'; NO ARQ retry
   - ChannelTenantRateExceeded → reschedule task pending+5m; no CB hit; no ARQ retry
   - ChannelComplianceBlocked  → mark_skipped; no CB hit; no ARQ retry
   - ChannelFatalError         → mark_failed; no CB hit; no ARQ retry
   - ChannelRateLimitedError / ChannelRetryableError → re-raise → ARQ exp backoff
   - generic Exception         → re-raise → ARQ exp backoff
6. Commit. Audit log writes are best-effort (never abort main tx).

Retries (ARQ max_tries=5): exponential backoff 60s x 2^attempt capped 1h.

PR-5 PI-1 S2 — tessl__graceful-degradation: every external call has timeout;
circuit breaker is the fallback pattern.
"""

from __future__ import annotations

import datetime as dt
from uuid import UUID

import structlog

from src.modules.campaigns.domain.audit_log import AuditEventType
from src.modules.campaigns.domain.enums import StepType, TaskStatus
from src.modules.campaigns.infrastructure.channels.errors import (
    ChannelComplianceBlocked,
    ChannelFatalError,
    ChannelRateLimitedError,
    ChannelRetryableError,
    ChannelTenantRateExceeded,
)
from src.modules.campaigns.infrastructure.channels.registry import ChannelRouterRegistry
from src.modules.campaigns.infrastructure.resilience.errors import CircuitBreakerOpenError

logger = structlog.get_logger(__name__)

_DEFAULT_RESCHEDULE_DELAY_MINUTES = 5


async def run_campaign_execution_task(ctx: dict, campaign_task_id: str) -> dict[str, str]:
    """ARQ entry — process a single CampaignTask.

    Args:
        ctx: ARQ context with ``db_factory`` and ``redis_cache`` keys.
        campaign_task_id: UUID string of the CampaignTask to process.

    Returns:
        Dict with ``id``, ``status``, and ``external_id`` keys.
    """
    task_uuid = UUID(campaign_task_id)
    db_factory = ctx["db_factory"]

    async with db_factory() as session:
        return await _process_task(session, task_uuid, ctx)


def _task_row_to_domain(row: object) -> object:
    """Convert a CampaignTaskModel ORM row to a CampaignTask domain entity.

    Used by the CALL_SUBAGENT_BRIEF dispatch branch to pass a typed domain
    object to SalesAgentAdapter without importing models into the domain layer.

    Args:
        row: A ``CampaignTaskModel`` instance (already loaded from DB).

    Returns:
        ``CampaignTask`` domain entity built from the ORM row.
    """
    from src.modules.campaigns.domain.campaign_task import CampaignTask

    return CampaignTask.model_validate(row, from_attributes=True)


async def _process_task(session: object, task_id: UUID, ctx: dict | None = None) -> dict[str, str]:  # noqa: C901, PLR0911, PLR0912, PLR0915
    """Inner logic scoped to a single AsyncSession.

    Args:
        session: Open AsyncSession for this worker execution.
        task_id: UUID of the CampaignTask to process.
        ctx: Optional ARQ context dict — used to pass ``budget_guard`` to
             SalesAgentAdapter for CALL_SUBAGENT_BRIEF steps.
    """
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.modules.campaigns.application.services.audit_log_service import AuditLogService
    from src.modules.campaigns.infrastructure.models.campaign_task_model import CampaignTaskModel
    from src.modules.campaigns.infrastructure.repositories.audit_log_repo_impl import (
        AuditLogRepositoryImpl,
    )
    from src.modules.campaigns.infrastructure.repositories.campaign_step_repository_impl import (
        CampaignStepRepositoryImpl,
    )
    from src.modules.campaigns.infrastructure.repositories.campaign_task_repository_impl import (
        CampaignTaskRepositoryImpl,
    )

    assert isinstance(session, AsyncSession)  # noqa: S101

    task_repo = CampaignTaskRepositoryImpl()
    step_repo = CampaignStepRepositoryImpl()
    audit_svc = AuditLogService(repo=AuditLogRepositoryImpl())

    # ── Step 1: SELECT FOR UPDATE ──────────────────────────────────────────────
    async with session.begin():
        stmt = select(CampaignTaskModel).where(CampaignTaskModel.id == task_id).with_for_update()
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()

        if row is None:
            logger.warning("execution_task_not_found", task_id=str(task_id))
            return {"id": str(task_id), "status": "not_found", "external_id": ""}

        tenant_id: UUID = row.tenant_id
        campaign_id: UUID = row.campaign_id

        # ── Step 2: Skip if already processed ─────────────────────────────────
        if row.status not in (TaskStatus.PENDING.value, TaskStatus.SCHEDULED.value):
            logger.info(
                "execution_task_noop",
                task_id=str(task_id),
                status=row.status,
                tenant_id=str(tenant_id),
            )
            return {
                "id": str(task_id),
                "status": row.status,
                "external_id": row.external_message_id or "",
            }

        # ── Step 3: Resolve channel ────────────────────────────────────────────
        channel = "telegram"
        content: dict = {}
        step = None
        if row.step_id is not None:
            step = await step_repo.get_by_id(row.step_id, tenant_id, session=session)
            if step is not None:
                # step_config.channel_override is per-step channel (SEND_MESSAGE contract)
                channel_override = step.step_config.get("channel_override") if step.step_config else None
                if channel_override:
                    channel = channel_override
                if step.step_config:
                    content = dict(step.step_config)

        # ── PR-7 Sub-D: CALL_SUBAGENT_BRIEF branch (before channel router) ─────
        # Dispatches via SalesAgentAdapter → OutboundOrchestrator → LangGraph.
        # Channel send + LLM are owned by the orchestrator. Worker only marks
        # task status and writes audit log.
        if step is not None and step.step_type == StepType.CALL_SUBAGENT_BRIEF:
            from src.modules.campaigns.infrastructure.external.sales_agent_adapter import (
                SalesAgentAdapter,
            )

            budget_guard = (ctx or {}).get("budget_guard")
            sa_result = await SalesAgentAdapter.dispatch(
                session=session,
                task=_task_row_to_domain(row),
                step=step,
                budget_guard=budget_guard,
            )

            if sa_result.success:
                await task_repo.mark_sent(
                    task_id,
                    tenant_id,
                    external_message_id=sa_result.external_message_id,
                    channel_used="telegram",
                    session=session,
                )
                await _audit(
                    audit_svc,
                    session,
                    tenant_id=tenant_id,
                    event_type=AuditEventType.TASK_SENT,
                    actor="execution_worker",
                    campaign_id=campaign_id,
                    campaign_task_id=task_id,
                    payload={
                        "external_message_id": sa_result.external_message_id or "",
                        "channel": "telegram",
                        "via": "sales_agent_adapter",
                    },
                )
                logger.info(
                    "campaign_execution_task_sent_via_sales_agent",
                    tenant_id=str(tenant_id),
                    task_id=str(task_id),
                    campaign_id=str(campaign_id),
                    external_message_id=sa_result.external_message_id or "",
                )
                return {
                    "id": str(task_id),
                    "status": "sent",
                    "external_id": sa_result.external_message_id or "",
                }

            await task_repo.mark_failed(
                task_id,
                tenant_id,
                error_code=sa_result.error_code or "sales_agent_dispatch_failed",
                error_message=sa_result.error_message or "",
                session=session,
            )
            await _audit(
                audit_svc,
                session,
                tenant_id=tenant_id,
                event_type=AuditEventType.TASK_FAILED,
                actor="execution_worker",
                campaign_id=campaign_id,
                campaign_task_id=task_id,
                payload={
                    "error_code": sa_result.error_code or "sales_agent_dispatch_failed",
                    "error_message": sa_result.error_message or "",
                    "via": "sales_agent_adapter",
                },
            )
            logger.warning(
                "campaign_execution_task_sales_agent_failed",
                tenant_id=str(tenant_id),
                task_id=str(task_id),
                campaign_id=str(campaign_id),
                error_code=sa_result.error_code,
            )
            return {"id": str(task_id), "status": "failed", "external_id": ""}

        registry = ChannelRouterRegistry()
        if not registry.has(channel):
            logger.warning(
                "execution_task_channel_not_registered",
                task_id=str(task_id),
                channel=channel,
            )
            await task_repo.mark_failed(
                task_id,
                tenant_id,
                error_code="unregistered_channel",
                error_message=f"Channel '{channel}' not registered in registry",
                session=session,
            )
            await _audit(
                audit_svc,
                session,
                tenant_id=tenant_id,
                event_type=AuditEventType.TASK_FAILED,
                actor="execution_worker",
                campaign_id=campaign_id,
                campaign_task_id=task_id,
                payload={"error_code": "unregistered_channel", "channel": channel},
            )
            return {"id": str(task_id), "status": "failed", "external_id": ""}

        router = registry.get(channel)
        idempotency_key = f"telegram-send:{task_id}"

        # ── Step 4: Audit dispatched (best-effort) ─────────────────────────────
        await _audit(
            audit_svc,
            session,
            tenant_id=tenant_id,
            event_type=AuditEventType.TASK_DISPATCHED,
            actor="execution_worker",
            campaign_id=campaign_id,
            campaign_task_id=task_id,
            payload={"channel": channel, "idempotency_key": idempotency_key},
        )

        logger.info(
            "campaign_execution_task_dispatch",
            tenant_id=str(tenant_id),
            task_id=str(task_id),
            campaign_id=str(campaign_id),
            channel=channel,
        )

        # ── Step 5: Send ───────────────────────────────────────────────────────
        start = dt.datetime.now(tz=dt.timezone.utc)
        try:
            send_result = await router.send(
                tenant_id,
                row.lead_id,
                channel,
                content,
                idempotency_key=idempotency_key,
            )
        except CircuitBreakerOpenError as exc:
            # CB open → mark failed, NO ARQ retry
            logger.warning(
                "campaign_execution_task_circuit_open",
                task_id=str(task_id),
                tenant_id=str(tenant_id),
                channel=channel,
                retry_after=exc.retry_after_seconds,
            )
            await task_repo.mark_failed(
                task_id,
                tenant_id,
                error_code="circuit_open",
                error_message=str(exc),
                session=session,
            )
            await _audit(
                audit_svc,
                session,
                tenant_id=tenant_id,
                event_type=AuditEventType.TASK_FAILED,
                actor="execution_worker",
                campaign_id=campaign_id,
                campaign_task_id=task_id,
                payload={"error_code": "circuit_open", "error_message": str(exc)},
            )
            return {"id": str(task_id), "status": "failed", "external_id": ""}

        except ChannelTenantRateExceeded:
            # Tenant rate exceeded → mark failed (task gets rescheduled by scheduler_tick)
            # No CB hit, no ARQ retry
            await task_repo.mark_failed(
                task_id,
                tenant_id,
                error_code="tenant_rate_exceeded",
                error_message="Tenant outbound rate exceeded",
                session=session,
            )
            await _audit(
                audit_svc,
                session,
                tenant_id=tenant_id,
                event_type=AuditEventType.RATE_LIMITED,
                actor="execution_worker",
                campaign_id=campaign_id,
                campaign_task_id=task_id,
                payload={"error_code": "tenant_rate_exceeded"},
            )
            logger.info(
                "campaign_execution_task_rate_limited",
                task_id=str(task_id),
                tenant_id=str(tenant_id),
            )
            return {"id": str(task_id), "status": "pending", "external_id": ""}

        except ChannelComplianceBlocked as exc:
            # Compliance blocked → skip, no retry, no CB hit
            await task_repo.mark_skipped(
                task_id,
                tenant_id,
                reason=str(exc),
                compliance_check={"error_code": exc.error_code},
                session=session,
            )
            await _audit(
                audit_svc,
                session,
                tenant_id=tenant_id,
                event_type=AuditEventType.COMPLIANCE_BLOCKED,
                actor="execution_worker",
                campaign_id=campaign_id,
                campaign_task_id=task_id,
                payload={"reason": str(exc)},
            )
            logger.info(
                "campaign_execution_task_compliance_blocked",
                task_id=str(task_id),
                tenant_id=str(tenant_id),
            )
            return {"id": str(task_id), "status": "skipped", "external_id": ""}

        except ChannelFatalError as exc:
            # Fatal (4xx non-429) → mark failed, no retry
            await task_repo.mark_failed(
                task_id,
                tenant_id,
                error_code=getattr(exc, "error_code", "fatal"),
                error_message=str(exc),
                session=session,
            )
            await _audit(
                audit_svc,
                session,
                tenant_id=tenant_id,
                event_type=AuditEventType.TASK_FAILED,
                actor="execution_worker",
                campaign_id=campaign_id,
                campaign_task_id=task_id,
                payload={"error_code": getattr(exc, "error_code", "fatal"), "error_message": str(exc)},
            )
            return {"id": str(task_id), "status": "failed", "external_id": ""}

        except (ChannelRateLimitedError, ChannelRetryableError):
            # Transient / rate-limited → re-raise so ARQ applies exp backoff; CB counts
            logger.warning(
                "campaign_execution_task_retryable_error",
                task_id=str(task_id),
                tenant_id=str(tenant_id),
                exc_info=True,
            )
            raise  # ARQ retry

        # ── Step 6: Success ────────────────────────────────────────────────────
        duration_ms = int((dt.datetime.now(tz=dt.timezone.utc) - start).total_seconds() * 1000)
        external_id = str(send_result.external_message_id) if send_result.external_message_id else ""

        await task_repo.mark_sent(
            task_id,
            tenant_id,
            external_message_id=send_result.external_message_id,
            channel_used=channel,
            session=session,
        )
        await _audit(
            audit_svc,
            session,
            tenant_id=tenant_id,
            event_type=AuditEventType.TASK_SENT,
            actor="execution_worker",
            campaign_id=campaign_id,
            campaign_task_id=task_id,
            payload={
                "external_message_id": external_id,
                "channel": channel,
                "duration_ms": duration_ms,
            },
        )

        logger.info(
            "campaign_execution_task_sent",
            tenant_id=str(tenant_id),
            task_id=str(task_id),
            external_message_id=external_id,
            duration_ms=duration_ms,
        )
        return {"id": str(task_id), "status": "sent", "external_id": external_id}


async def _audit(
    audit_svc: object,
    session: object,
    *,
    tenant_id: UUID,
    event_type: AuditEventType,
    actor: str,
    campaign_id: UUID | None = None,
    campaign_task_id: UUID | None = None,
    payload: dict | None = None,
) -> None:
    """Write audit row. Never raises (AuditLogService.record contract)."""
    try:
        from sqlalchemy.ext.asyncio import AsyncSession

        from src.modules.campaigns.application.services.audit_log_service import AuditLogService

        assert isinstance(audit_svc, AuditLogService)  # noqa: S101
        assert isinstance(session, AsyncSession)  # noqa: S101
        await audit_svc.record(
            tenant_id=tenant_id,
            event_type=event_type,
            actor=actor,
            campaign_id=campaign_id,
            campaign_task_id=campaign_task_id,
            payload=payload,
            session=session,
        )
    except Exception:  # noqa: BLE001
        logger.warning("execution_task_audit_write_error", exc_info=True)
