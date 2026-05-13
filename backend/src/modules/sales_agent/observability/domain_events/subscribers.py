"""Subscribers that persist sales_agent domain events to ``sales_agent_trace_event``.

Each handler:

1. Sanitises the event payload (PII redaction).
2. Opens a fresh ``SessionLocal()`` (sync) — best-effort, tightly scoped.
3. Writes one ``event_type='domain_event'`` row tagged with the
   sub-event class name (``LeadQualified`` / ``ObjectionHandled`` /
   ``StageTransitioned`` / ``ToolLoopDetected``).
4. Commits + closes; any exception is swallowed and logged via
   ``structlog.warning`` — observability must not break the turn.

Wiring lives in :func:`register_subscribers`. The orchestrator (or
worker bootstrap) calls it once at startup; subscribers stay alive
for the process lifetime.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import structlog
from luana_core_observability.recording.sanitization import sanitize_payload
from luana_core_sales_agent.domain.events import (
    LeadQualifiedEvent,
    ObjectionHandledEvent,
    StageTransitionedEvent,
    ToolLoopDetectedEvent,
)
from luana_core_sales_agent.infrastructure.db.database import SessionLocal
from luana_core_sales_agent.observability.persistence.trace_event_repository import (
    SalesAgentTraceEventRepository,
)

if TYPE_CHECKING:
    from luana_core_sales_agent.application.event_bus import EventBus

logger = structlog.get_logger()


def _persist_domain_event(
    *,
    event_name: str,
    tenant_id: object,
    lead_id: object,
    channel_type: str,
    turn_id: object,
    payload: dict[str, object],
    status: str = "ok",
) -> None:
    """Best-effort write of one ``domain_event`` row."""
    db = None
    try:
        db = SessionLocal()
        repo = SalesAgentTraceEventRepository(db)
        repo.add(
            tenant_id=tenant_id,
            turn_id=turn_id,
            span_id=uuid4(),
            event_type="domain_event",
            name=event_name,
            data=sanitize_payload(payload),
            duration_ms=None,
            status=status,
            lead_id=lead_id,
            channel_type=channel_type,
        )
        db.commit()
    except Exception as exc:  # noqa: BLE001 — best-effort
        logger.warning(
            "sales_agent_domain_event_persist_failed",
            domain_event_name=event_name,
            error=str(exc),
        )
        if db is not None:
            try:
                db.rollback()
            except Exception:  # noqa: BLE001
                logger.warning("sales_agent_domain_event_rollback_failed")
    finally:
        if db is not None:
            try:
                db.close()
            except Exception:  # noqa: BLE001
                logger.warning("sales_agent_domain_event_close_failed")


async def on_lead_qualified(event: LeadQualifiedEvent) -> None:
    """Persist a LeadQualified domain_event row."""
    _persist_domain_event(
        event_name="LeadQualified",
        tenant_id=event.tenant_id,
        lead_id=event.lead_id,
        channel_type=event.channel_type,
        turn_id=event.turn_id,
        payload={
            "lead_score": event.lead_score,
            "qualification_field_count": event.qualification_field_count,
            "buying_signal_count": event.buying_signal_count,
            "stage": event.stage,
        },
    )


async def on_objection_handled(event: ObjectionHandledEvent) -> None:
    """Persist an ObjectionHandled domain_event row."""
    _persist_domain_event(
        event_name="ObjectionHandled",
        tenant_id=event.tenant_id,
        lead_id=event.lead_id,
        channel_type=event.channel_type,
        turn_id=event.turn_id,
        payload={
            "objection_type": event.objection_type,
            "resolved": event.resolved,
            "specialist": event.specialist,
        },
    )


async def on_stage_transitioned(event: StageTransitionedEvent) -> None:
    """Persist a StageTransitioned domain_event row."""
    _persist_domain_event(
        event_name="StageTransitioned",
        tenant_id=event.tenant_id,
        lead_id=event.lead_id,
        channel_type=event.channel_type,
        turn_id=event.turn_id,
        payload={
            "from_stage": event.from_stage,
            "to_stage": event.to_stage,
            "lead_score": event.lead_score,
        },
    )


async def on_tool_loop_detected(event: ToolLoopDetectedEvent) -> None:
    """Persist a ToolLoopDetected domain_event row with status='error'."""
    _persist_domain_event(
        event_name="ToolLoopDetected",
        tenant_id=event.tenant_id,
        lead_id=event.lead_id,
        channel_type=event.channel_type,
        turn_id=event.turn_id,
        payload={
            "tool_name": event.tool_name,
            "repeat_count": event.repeat_count,
            "args_hash": event.args_hash,
        },
        status="error",
    )


def register_subscribers(event_bus: EventBus) -> None:
    """Wire all S1 sales_agent domain-event subscribers to ``event_bus``."""
    event_bus.subscribe(LeadQualifiedEvent, on_lead_qualified)
    event_bus.subscribe(ObjectionHandledEvent, on_objection_handled)
    event_bus.subscribe(StageTransitionedEvent, on_stage_transitioned)
    event_bus.subscribe(ToolLoopDetectedEvent, on_tool_loop_detected)


__all__ = [
    "on_lead_qualified",
    "on_objection_handled",
    "on_stage_transitioned",
    "on_tool_loop_detected",
    "register_subscribers",
]
