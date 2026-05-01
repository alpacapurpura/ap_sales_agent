"""Factories for per-turn sales-agent observability.

Two factories live here, both best-effort (return ``None`` instead of
raising):

* :func:`build_sales_agent_callback_handler` — the lower-level handler
  the legacy orchestrator paths still construct directly. Kept for
  back-compat and unit-test convenience; **prefer the envelope factory
  in new code**.
* :func:`build_sales_agent_observability_context` — the *envelope* used
  by the orchestrators. Returns a :class:`SalesAgentObservabilityContext`
  whose :meth:`observe_turn` brackets the turn with a real
  ``turn_start`` / ``turn_end`` row + an explicit ``commit`` on the
  trace-event session. **Without this envelope** the callback handler's
  ``session.add(...)`` calls pile up uncommitted in the orchestrator
  session and get discarded when ``SessionLocal()`` closes — which is
  exactly Bug #2 (see ``IMPL-LOG-agentic.md``).

Responsibilities lifted out of ``ChatOrchestrator`` /
``OutboundOrchestrator``:

1. Resolve tenant currency (``TenantBillingConfig`` or fallback ``USD``).
2. Build the concrete repos (LLM call, trace event) bound to the same
   SA session the orchestrator already opened.
3. Build the shared :class:`PricingResolver` + :class:`FXResolver`
   (cached singletons; one lookup per process).
4. Wire all of them into a fresh :class:`SalesAgentObservabilityContext`.

Cohesión: the orchestrators do NOT know about pricing snapshots, FX, or
repos shapes. They just call ``await ctx.observe_turn(...)``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from src.modules.sales_agent.observability.persistence.llm_call_repository import (
    SalesAgentLlmCallRepository,
)
from src.modules.sales_agent.observability.persistence.trace_event_repository import (
    SalesAgentTraceEventRepository,
)
from src.modules.sales_agent.observability.recording.callback_handler import (
    SalesAgentCallbackHandler,
)
from src.modules.sales_agent.observability.recording.turn_envelope import (
    SalesAgentObservabilityContext,
)
from src.shared.agent_observability.cost.fx_resolver import FXResolver
from src.shared.agent_observability.persistence.pricing_snapshot_repository import (
    PricingSnapshotRepository,
)
from src.shared.agent_observability.persistence.tenant_billing_config_repository import (
    TenantBillingConfigRepository,
)
from src.shared.agent_observability.pricing.resolver import PricingResolver

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

logger = structlog.get_logger()


def _resolve_tenant_currency(db: Session, tenant_id: UUID) -> str:
    """Best-effort tenant-currency lookup; falls back to ``"USD"``.

    Note: ``billing_cfg.billing_currency`` returns ``Column[str] | str``
    depending on access path (SA model attribute vs unloaded
    descriptor). We cast to ``str`` to keep the public contract narrow
    and silence mypy.
    """
    try:
        billing_cfg = TenantBillingConfigRepository(db).get(tenant_id=tenant_id)
        return str(billing_cfg.billing_currency) if billing_cfg else "USD"
    except Exception as exc:  # noqa: BLE001 — best-effort observability
        logger.warning(
            "sales_agent_tenant_currency_lookup_failed",
            error=str(exc),
            tenant_id=str(tenant_id),
        )
        return "USD"


def build_sales_agent_callback_handler(
    *,
    db: Session,
    tenant_id: UUID,
    lead_id: UUID,
    channel_type: str,
    turn_id: UUID,
    role: str = "agent",
) -> SalesAgentCallbackHandler | None:
    """Build a turn-scoped callback handler (low-level).

    Returns ``None`` when ``tenant_id`` or ``lead_id`` is missing — the
    handler requires both for tenant isolation + per-lead audit trail.
    Failures during construction are swallowed (best-effort
    observability) and logged via ``structlog.warning``.

    Prefer :func:`build_sales_agent_observability_context` — it wraps
    the same handler in the turn envelope that actually commits rows
    (see module docstring).
    """
    if tenant_id is None or lead_id is None:
        return None
    try:
        llm_call_repo = SalesAgentLlmCallRepository(db)
        trace_repo = SalesAgentTraceEventRepository(db)
        # Resolver factory keeps it session-agnostic — fresh repo per call,
        # bound to the same orchestrator session.
        pricing_resolver = PricingResolver(repo_factory=lambda: PricingSnapshotRepository(db))
        fx_resolver = FXResolver()
        tenant_currency = _resolve_tenant_currency(db, tenant_id)
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
    role: str = "agent",
    turn_id: UUID | None = None,
) -> SalesAgentObservabilityContext | None:
    """Build a turn-scoped observability **envelope**.

    The envelope is what the orchestrators must use — it brackets the
    turn with a real ``turn_start`` / ``turn_end`` row plus an explicit
    ``session.commit()`` on the trace-event session, picking up every
    row the bound :class:`SalesAgentCallbackHandler` queued during
    ``ainvoke``.

    Returns ``None`` when ``tenant_id`` or ``lead_id`` is missing —
    callers must short-circuit to a raw ``ainvoke`` (no observability)
    in that case.
    """
    if tenant_id is None or lead_id is None:
        return None
    try:
        llm_call_repo = SalesAgentLlmCallRepository(db)
        trace_repo = SalesAgentTraceEventRepository(db)
        pricing_resolver = PricingResolver(repo_factory=lambda: PricingSnapshotRepository(db))
        fx_resolver = FXResolver()
        tenant_currency = _resolve_tenant_currency(db, tenant_id)
        return SalesAgentObservabilityContext.start(
            tenant_id=tenant_id,
            lead_id=lead_id,
            channel_type=channel_type,
            llm_call_repo=llm_call_repo,
            trace_repo=trace_repo,
            pricing_resolver=pricing_resolver,
            fx_resolver=fx_resolver,
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
