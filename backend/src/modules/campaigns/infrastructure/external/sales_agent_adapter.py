"""SalesAgentAdapter — bridges CampaignTask + CampaignStep → OutboundOrchestrator.

Cross-module port: campaigns/infrastructure → sales_agent.application.
Lazy-imports OutboundOrchestrator + ChannelRouter so the campaigns module
does NOT take a top-level dependency on sales_agent (DDD: sales_agent is
the LangGraph runtime; campaigns owns the cron + DAG).

Invoked from: ``campaigns/workers/execution_task.py::_process_task`` when
``step.step_type == StepType.CALL_SUBAGENT_BRIEF``.

Compliance + RateLimit + Idempotency are applied PRE-dispatch via the
worker's existing pipeline (inherited from worker — NOT duplicated here).

Session bridge decision (PR-7 Sub-D build decision):
``sync_session_from_async`` does NOT exist in this codebase
(``src.shared.infrastructure.db`` module is absent). Pattern used:
``SessionLocal()`` from ``src.core.database`` — same pattern as admin
modules (``src/admin/modules/_shared.py:33``). A fresh sync session is
created per dispatch call and closed in a finally block regardless of
outcome. The AsyncSession from the worker is kept open for its own
transaction (task status updates); the sync session is exclusively for
the OutboundOrchestrator's ConversationPipeline reads/writes.

# [CAMPAIGNS-OUTBOUND-ADAPTER-PR7]
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from collections.abc import Generator

    from luana_core_billing.application.budget_guard import BudgetGuard
    from luana_core_campaigns.domain.campaign_step import CampaignStep
    from luana_core_campaigns.domain.campaign_task import CampaignTask
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import Session

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class SalesAgentDispatchResult:
    """Result of adapter dispatch — translates to ChannelSendResult by worker."""

    success: bool
    external_message_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None


class SalesAgentAdapter:
    """Static adapter — single async entrypoint :meth:`dispatch`."""

    @staticmethod
    @contextmanager
    def _create_sync_db() -> Generator[Session, None, None]:
        """Create a fresh sync Session for OutboundOrchestrator.

        Yields a ``Session`` and always closes it in the finally block.
        Uses ``SessionLocal`` from ``src.core.database`` — established
        pattern for sync DB access in this codebase.
        """
        from luana_core_platform.core.database import SessionLocal

        db: Session = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    @staticmethod
    async def dispatch(
        *,
        session: AsyncSession,  # noqa: ARG004 — reserved for future async reads pre-dispatch
        task: CampaignTask,
        step: CampaignStep,
        budget_guard: BudgetGuard | None = None,
    ) -> SalesAgentDispatchResult:
        """Dispatch CampaignTask via OutboundOrchestrator.

        Pre-conditions (caller-enforced — execution_task.py):
        - ``step.step_type == StepType.CALL_SUBAGENT_BRIEF``
        - Compliance, RateLimit, Idempotency already gated by worker
        - SELECT FOR UPDATE row lock held on CampaignTask

        Args:
            session: AsyncSession (worker-scoped, txn open — reserved for
                     future async pre-dispatch reads; not used by
                     OutboundOrchestrator which requires a sync Session).
            task: CampaignTask (locked).
            step: CampaignStep with step_config = {"agent_kind", "brief"}.
            budget_guard: Optional — when set, OutboundOrchestrator wraps LLM.

        Returns:
            SalesAgentDispatchResult with ``success`` + external_message_id.

        Raises:
            ValueError: step_type mismatch (caller bug).
        """
        from luana_core_campaigns.domain.enums import StepType

        if step.step_type != StepType.CALL_SUBAGENT_BRIEF:
            msg = f"SalesAgentAdapter requires CALL_SUBAGENT_BRIEF; got {step.step_type!r}"
            raise ValueError(msg)

        # Validate agent_kind BEFORE importing heavy agentic module
        agent_kind = (step.step_config or {}).get("agent_kind", "sales_agent")
        if agent_kind != "sales_agent":
            logger.warning(
                "sales_agent_adapter_unsupported_kind",
                task_id=str(task.id),
                tenant_id=str(task.tenant_id),
                campaign_id=str(task.campaign_id),
                lead_id=str(task.lead_id),
                agent_kind=agent_kind,
            )
            return SalesAgentDispatchResult(
                success=False,
                error_code="unsupported_agent_kind",
                error_message=f"agent_kind={agent_kind!r} not supported (only 'sales_agent' in S3)",
            )

        brief: str = (step.step_config or {}).get("brief") or step.label or "Iniciá la conversación outbound."
        channel_type = "telegram"  # S3 MVP — multi-canal en S4

        logger.info(
            "sales_agent_adapter_dispatch",
            task_id=str(task.id),
            tenant_id=str(task.tenant_id),
            campaign_id=str(task.campaign_id),
            lead_id=str(task.lead_id),
            channel_type=channel_type,
        )

        # Lazy imports — keep DDD boundary clean (campaigns does NOT top-level import sales_agent)
        from luana_core_campaigns.infrastructure.channels.registry import ChannelRouterRegistry
        from luana_core_sales_agent.application.orchestrator.outbound_orchestrator import (
            OutboundOrchestrator,
        )

        registry = ChannelRouterRegistry()
        channel_router = registry.get(channel_type)

        # Bridge AsyncSession → sync Session for OutboundOrchestrator.
        # See module docstring for rationale.
        with SalesAgentAdapter._create_sync_db() as sync_db:
            try:
                result = await OutboundOrchestrator.send_outbound(
                    db=sync_db,
                    tenant_id=task.tenant_id,
                    lead_id=task.lead_id,
                    campaign_id=task.campaign_id,
                    campaign_instructions=brief,
                    channel_type=channel_type,
                    channel_adapter=channel_router,  # type: ignore[arg-type]
                    budget_guard=budget_guard,
                    idempotency_key=task.idempotency_key,
                )
            except Exception as exc:  # adapter resilience — broad catch intentional
                logger.exception(
                    "sales_agent_adapter_dispatch_failed",
                    task_id=str(task.id),
                    tenant_id=str(task.tenant_id),
                    campaign_id=str(task.campaign_id),
                    lead_id=str(task.lead_id),
                )
                return SalesAgentDispatchResult(
                    success=False,
                    error_code="adapter_failure",
                    error_message=str(exc),
                )

        return SalesAgentDispatchResult(
            success=result.success,
            external_message_id=result.external_message_id,
            error_code=result.error_code,
            error_message=result.error_message,
        )


__all__ = ["SalesAgentAdapter", "SalesAgentDispatchResult"]
