"""Domain-event subscribers — copilot publishes, observability records.

Phase 2 wires this for two of the four event names:

* ``copilot_card_emitted`` — turns into a ``card_emitted`` row.
* ``copilot_routing_decided`` — turns into a ``routing_decided`` row.

``copilot_turn_started`` / ``copilot_turn_ended`` are written **directly**
by :class:`turn_envelope.ObservabilityContext.observe_turn` because the
turn lifecycle owns the aggregation query against ``copilot_llm_call``
and we don't want a second writer racing for the same row.

``register_subscribers`` is opt-in and idempotent — re-registering
doesn't duplicate handlers.
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING
from uuid import UUID

import structlog

from src.modules.copilot.domain.events import (
    EVENT_CARD_EMITTED,
    EVENT_ROUTING_DECIDED,
)
from src.shared.agent_observability.recording.sanitization import sanitize_payload, truncate
from src.shared.domain.events import DomainEvent  # noqa: TC001 — used in runtime handler signatures
from src.shared.domain_events.outbox.application.event_bus_adapter import (
    adapter_bus as EventBus,  # noqa: N812
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from src.modules.copilot.observability.persistence.trace_event_repository import (
        TraceEventRepository,
    )

logger = structlog.get_logger()


def register_subscribers(*, repo_factory: Callable[[], TraceEventRepository]) -> None:
    """Wire the observability handlers onto the shared ``EventBus``.

    ``repo_factory`` returns a fresh ``TraceEventRepository`` (i.e. opens
    its own ``Session``). Handlers commit through that session so the
    write is independent from any orchestrator transaction. Calling this
    function twice is a no-op for already-registered handlers.
    """

    def _persist(event: DomainEvent, *, event_type: str, name_key: str) -> None:
        try:
            repo = repo_factory()
            session = getattr(repo, "db", None)
            payload = event.payload or {}
            tenant_id = event.tenant_id
            turn_id = _coerce_uuid(payload.get("turn_id"))
            conversation_id = _coerce_uuid(payload.get("conversation_id"))
            user_id = _coerce_uuid(payload.get("user_id"))
            name = payload.get(name_key)
            row = repo.add(
                tenant_id=tenant_id,
                user_id=user_id,
                conversation_id=conversation_id,
                turn_id=turn_id or tenant_id,  # fallback so the column stays NOT NULL
                span_id=_coerce_uuid(payload.get("span_id")) or _new_uuid(),
                event_type=event_type,
                name=truncate(str(name)) if name else event_type,
                data=sanitize_payload(_drop_uuid_keys(payload)),
                status="ok",
            )
            if session is not None:
                with contextlib.suppress(Exception):
                    session.commit()
            logger.debug(
                "obs_domain_subscriber_persisted",
                event_name=event.event_name,
                row_id=getattr(row, "id", None),
            )
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning(
                "obs_domain_subscriber_failed",
                event_name=event.event_name,
                error=str(exc),
            )

    def on_card_emitted(event: DomainEvent) -> None:
        _persist(event, event_type="card_emitted", name_key="card_kind")

    def on_routing_decided(event: DomainEvent) -> None:
        _persist(event, event_type="routing_decided", name_key="tier")

    _subscribe_once(EVENT_CARD_EMITTED, on_card_emitted)
    _subscribe_once(EVENT_ROUTING_DECIDED, on_routing_decided)


def _subscribe_once(event_name: str, handler: Callable[[DomainEvent], None]) -> None:
    """Subscribe ``handler`` only if a same-named handler isn't already there.

    Mirrors the pattern in ``shared/application/brand_summary_event_handlers.py``
    so re-imports / hot-reloads don't stack duplicate handlers.

    ``EventBus`` here is the adapter_bus whose ``subscribe`` delegates to the
    legacy in-memory bus.  The dedup check must therefore query
    ``LegacyEventBus._handlers`` (class attribute on the legacy bus class).
    """
    from src.shared.domain.events import EventBus as _LegacyEventBus

    existing = _LegacyEventBus._handlers.get(event_name, [])
    target_name = getattr(handler, "__name__", str(handler))
    for h in existing:
        if getattr(h, "__name__", str(h)) == target_name:
            return
    EventBus.subscribe(event_name, handler)


def _coerce_uuid(value: object) -> UUID | None:
    """Best-effort UUID parse — domain events serialise UUIDs as strings."""
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def _new_uuid() -> UUID:
    from uuid import uuid4

    return uuid4()


def _drop_uuid_keys(payload: dict[str, object]) -> dict[str, object]:
    """Strip the IDs we already lifted into columns so ``data`` stays small."""
    drop = {"turn_id", "conversation_id", "user_id", "span_id"}
    return {k: v for k, v in payload.items() if k not in drop}


__all__ = ["register_subscribers"]
