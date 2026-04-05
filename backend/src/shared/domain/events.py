"""
Shared EventBus for cross-module domain event dispatch.

Usage:
    # Subscribe at app startup
    EventBus.subscribe("sale_completed", handle_sale_completed)

    # Publish with deferred dispatch (after DB commit)
    EventBus.publish(event, session=db)

    # Publish with immediate dispatch (no DB context)
    EventBus.publish(event, session=None)
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


@dataclass
class DomainEvent:
    """Base domain event. All cross-module events extend this."""

    event_name: str
    tenant_id: UUID
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    payload: dict[str, Any] = field(default_factory=dict)


class EventBus:
    """Simple in-process event bus with after-commit dispatch.

    Singleton pattern: _handlers is class-level, shared across the process.
    Handler exceptions are caught and logged, never propagated to the publisher.
    """

    _handlers: dict[str, list[Callable]] = {}

    @classmethod
    def subscribe(cls, event_name: str, handler: Callable) -> None:
        """Register a handler for a given event name."""
        cls._handlers.setdefault(event_name, []).append(handler)

    @classmethod
    def publish(cls, event: DomainEvent, session: Any | None = None) -> None:
        """Publish an event.

        If session is provided, dispatch is deferred until after session.commit().
        If session is None, dispatch is immediate.
        """
        if session is not None:
            from sqlalchemy import event as sa_event

            @sa_event.listens_for(session, "after_commit", once=True)
            def _on_commit(sess: Any) -> None:
                cls._dispatch(event)
        else:
            cls._dispatch(event)

    @classmethod
    def _dispatch(cls, event: DomainEvent) -> None:
        """Dispatch event to all registered handlers. Exceptions are isolated."""
        for handler in cls._handlers.get(event.event_name, []):
            try:
                handler(event)
            except Exception:
                logger.exception(
                    "Event handler %s failed for event %s",
                    getattr(handler, "__name__", handler),
                    event.event_name,
                )

    @classmethod
    def clear(cls) -> None:
        """Remove all registered handlers. Used for test isolation."""
        cls._handlers.clear()
