"""Domain-event subscribers — copilot publishes, observability records.

Phase 1 ships the wiring; the publishers (``copilot_card_emitted``,
``copilot_routing_decided``, ``copilot_turn_started``,
``copilot_turn_ended``) land in Phase 2 when chat.py and the tools
adopt the event bus instead of calling the recorder directly.

``register_subscribers`` is opt-in: the module entry-point in Phase 2
will call it from the FastAPI app startup hook (and, for workers, from
``WorkerSettings.on_startup`` if any worker emits these events).
Idempotent — re-registering doesn't duplicate handlers.
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING
from uuid import UUID

import structlog

from src.modules.copilot.observability.recording.sanitization import sanitize_payload, truncate
from src.shared.domain.events import DomainEvent, EventBus

if TYPE_CHECKING:
    from collections.abc import Callable

    from src.modules.copilot.observability.persistence.trace_event_repository import (
        TraceEventRepository,
    )

logger = structlog.get_logger()


# Event-name catalogue. Publishers in Phase 2 use these literals so
# subscribers and producers can't drift apart.
EVENT_CARD_EMITTED = "copilot_card_emitted"
EVENT_ROUTING_DECIDED = "copilot_routing_decided"
EVENT_TURN_STARTED = "copilot_turn_started"
EVENT_TURN_ENDED = "copilot_turn_ended"


def register_subscribers(*, repo_factory: Callable[[], TraceEventRepository]) -> None:
    """Wire the observability handlers onto the shared ``EventBus``.

    ``repo_factory`` returns a fresh ``TraceEventRepository`` (i.e. opens
    its own ``Session``) — handlers must not share a session with the
    publisher's transaction since the bus dispatches after-commit.
    Calling this function twice is a no-op for already-registered
    handlers.
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
                event=event.event_name,
                row_id=getattr(row, "id", None),
            )
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning(
                "obs_domain_subscriber_failed",
                event=event.event_name,
                error=str(exc),
            )

    def on_card_emitted(event: DomainEvent) -> None:
        _persist(event, event_type="card_emitted", name_key="card_kind")

    def on_routing_decided(event: DomainEvent) -> None:
        _persist(event, event_type="routing_decided", name_key="tier")

    def on_turn_started(event: DomainEvent) -> None:
        _persist(event, event_type="turn_start", name_key="route")

    def on_turn_ended(event: DomainEvent) -> None:
        _persist(event, event_type="turn_end", name_key="route")

    _subscribe_once(EVENT_CARD_EMITTED, on_card_emitted)
    _subscribe_once(EVENT_ROUTING_DECIDED, on_routing_decided)
    _subscribe_once(EVENT_TURN_STARTED, on_turn_started)
    _subscribe_once(EVENT_TURN_ENDED, on_turn_ended)


def _subscribe_once(event_name: str, handler: Callable[[DomainEvent], None]) -> None:
    """Subscribe ``handler`` only if a same-named handler isn't already there.

    Mirrors the pattern in ``shared/application/brand_summary_event_handlers.py``
    so re-imports / hot-reloads don't stack duplicate handlers.
    """
    existing = EventBus._handlers.get(event_name, [])
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


__all__ = [
    "EVENT_CARD_EMITTED",
    "EVENT_ROUTING_DECIDED",
    "EVENT_TURN_ENDED",
    "EVENT_TURN_STARTED",
    "register_subscribers",
]
