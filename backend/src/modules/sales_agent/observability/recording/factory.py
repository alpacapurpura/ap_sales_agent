"""Factory for the per-turn :class:`SalesAgentCallbackHandler`.

The orchestrator (``application/orchestrator/chat.py``) calls this once
per ``handle_*_webhook`` invocation. Returns ``None`` when the
required identity is missing — best-effort, never raise.

Responsibilities lifted out of ``ChatOrchestrator``:

1. Resolve tenant currency (``TenantBillingConfig`` or fallback ``USD``).
2. Build the three concrete repos (LLM call, trace event) bound to
   the same SA session the orchestrator already opened.
3. Build the shared :class:`PricingResolver` + :class:`FXResolver`
   (cached singletons; one lookup per process).
4. Wire all of them into a fresh :class:`SalesAgentCallbackHandler`.

Cohesión: the orchestrator does NOT know about pricing snapshots,
FX, or repos shapes. It just hands the handler to ``ainvoke(...,
config={"callbacks": [...]})``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from luana_core_observability.cost.fx_resolver import FXResolver
from luana_core_observability.persistence.pricing_snapshot_repository import (
    PricingSnapshotRepository,
)
from luana_core_observability.persistence.tenant_billing_config_repository import (
    TenantBillingConfigRepository,
)
from luana_core_observability.pricing.resolver import PricingResolver
from luana_core_sales_agent.observability.persistence.llm_call_repository import (
    SalesAgentLlmCallRepository,
)
from luana_core_sales_agent.observability.persistence.trace_event_repository import (
    SalesAgentTraceEventRepository,
)
from luana_core_sales_agent.observability.recording.callback_handler import (
    SalesAgentCallbackHandler,
)
from luana_core_sales_agent.observability.recording.turn_envelope import (
    SalesAgentObservabilityContext,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

logger = structlog.get_logger()


def build_sales_agent_callback_handler(
    *,
    db: Session,
    tenant_id: UUID,
    lead_id: UUID,
    channel_type: str,
    turn_id: UUID,
    role: str = "agent",
) -> SalesAgentCallbackHandler | None:
    """Build a turn-scoped callback handler.

    Returns ``None`` when ``tenant_id`` or ``lead_id`` is missing — the
    handler requires both for tenant isolation + per-lead audit trail.
    Failures during construction are swallowed (best-effort
    observability) and logged via ``structlog.warning``.
    """
    if tenant_id is None or lead_id is None:
        return None
    try:
        billing_repo = TenantBillingConfigRepository(db)
        llm_call_repo = SalesAgentLlmCallRepository(db)
        trace_repo = SalesAgentTraceEventRepository(db)
        # Resolver factory keeps it session-agnostic — fresh repo per call,
        # bound to the same orchestrator session.
        pricing_resolver = PricingResolver(repo_factory=lambda: PricingSnapshotRepository(db))
        # Bug #8 fix (PR-2 PI-1.1): ``FXResolver()`` no-arg crashed on
        # construct (dataclass missing required ``http_client_factory``)
        # → ``except`` block returned ``None`` → handler never wired →
        # zero observability writes for sales_agent. ``FXResolver.default()``
        # encapsulates ``httpx.Client(timeout=10)`` in shared per
        # ``tessl__graceful-degradation`` Rule 1.
        fx_resolver = FXResolver.default()
        billing_cfg = billing_repo.get(tenant_id=tenant_id)
        tenant_currency = billing_cfg.billing_currency if billing_cfg else "USD"
        return SalesAgentCallbackHandler(
            tenant_id=tenant_id,
            lead_id=lead_id,
            channel_type=channel_type,
            turn_id=turn_id,
            llm_call_repo=llm_call_repo,
            trace_repo=trace_repo,
            pricing_resolver=pricing_resolver,
            fx_resolver=fx_resolver,
            db_session=db,
            tenant_currency=tenant_currency,
            role=role,
        )
    except Exception as exc:  # noqa: BLE001 — best-effort observability
        logger.warning(
            "sales_agent_callback_handler_factory_failed",
            error=str(exc),
            tenant_id=str(tenant_id),
            lead_id=str(lead_id),
        )
        return None


def build_sales_agent_observability_context(
    *,
    db: Session,
    tenant_id: UUID,
    lead_id: UUID,
    channel_type: str,
    turn_id: UUID,
    role: str = "agent",
) -> SalesAgentObservabilityContext | None:
    """Build a turn-scoped observability context with bound callback handler.

    Bug #2 fix (PR-2 PI-1.1): the orchestrator used to wire only the
    callback handler via ``RunnableConfig(callbacks=[...])`` — that
    captured LLM/tool events but never wrote ``turn_start`` /
    ``turn_end`` rows. Wrapping ``agent_app.ainvoke`` in
    ``async with ctx.observe_turn(...)`` lands the bracket rows on
    ``sales_agent_trace_event``.

    Returns ``None`` when ``tenant_id`` or ``lead_id`` is missing —
    propagated to the orchestrator which then runs without observability
    (turn still completes, no row written; same fail-mode as the legacy
    callback factory).

    Failures during construction are swallowed (best-effort) and logged.
    """
    if tenant_id is None or lead_id is None:
        return None
    try:
        billing_repo = TenantBillingConfigRepository(db)
        llm_call_repo = SalesAgentLlmCallRepository(db)
        trace_repo = SalesAgentTraceEventRepository(db)
        pricing_resolver = PricingResolver(repo_factory=lambda: PricingSnapshotRepository(db))
        fx_resolver = FXResolver.default()
        billing_cfg = billing_repo.get(tenant_id=tenant_id)
        tenant_currency = billing_cfg.billing_currency if billing_cfg else "USD"
        return SalesAgentObservabilityContext.start(
            tenant_id=tenant_id,
            lead_id=lead_id,
            channel_type=channel_type,
            llm_call_repo=llm_call_repo,
            trace_repo=trace_repo,
            pricing_resolver=pricing_resolver,
            fx_resolver=fx_resolver,
            db_session=db,
            tenant_currency=tenant_currency,
            role=role,
            turn_id=turn_id,
        )
    except Exception as exc:  # noqa: BLE001 — best-effort observability
        logger.warning(
            "sales_agent_observability_context_factory_failed",
            error=str(exc),
            tenant_id=str(tenant_id),
            lead_id=str(lead_id),
        )
        return None


__all__ = [
    "build_sales_agent_callback_handler",
    "build_sales_agent_observability_context",
]
