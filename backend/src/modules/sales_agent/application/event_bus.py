"""Sales-agent local in-memory EventBus for module-internal events.

This bus handles **sales_agent-internal** domain events
(``LeadQualifiedEvent``, ``ObjectionHandledEvent``, ``StageTransitionedEvent``,
``ToolLoopDetectedEvent``) that do NOT need outbox persistence.

**Shared domain events** (``PaymentReceivedEvent``, ``BookingLinkCreatedEvent``,
``LeadCapturedEvent``, etc.) are published via the shared
``EventBusAdapter`` (``src.shared.domain_events.outbox.application.event_bus_adapter``).

The distinction keeps the outbox pattern scoped to cross-boundary events
while preserving the synchronous in-process subscriber pipeline for
observability-only events.

See:
  - ``observability/domain_events/subscribers.py`` — consumer of this bus
  - ``shared/domain_events/outbox/application/event_bus_adapter.py`` — shared bus
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from collections.abc import Callable

    from src.shared.domain.events import DomainEvent

logger = structlog.get_logger()


class EventBus:
    """In-memory Event Bus for dispatching sales_agent-internal domain events.

    Subscriber map keyed by event *class* (not string) — matches the legacy
    interface expected by ``observability/domain_events/subscribers.py`` and
    its test ``test_register_subscribers_wires_all_four_handlers``.
    """

    def __init__(self) -> None:
        """Initialize instance."""
        self._subscribers: dict[type[DomainEvent], list[Callable]] = {}

    def subscribe(self, event_type: type[DomainEvent], handler: Callable) -> None:
        """Subscribe a handler for a given event type class."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.info(
            "sales_agent_event_bus_subscribed",
            handler=handler.__name__,
            event_type=event_type.__name__,
        )

    async def publish(self, event: DomainEvent) -> None:
        """Publish an event to all subscribers (async dispatch)."""
        event_type = type(event)
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    await handler(event)
                except Exception:
                    logger.exception(
                        "sales_agent_event_bus_handler_failed",
                        event_type=event_type.__name__,
                    )
        else:
            logger.debug(
                "sales_agent_event_bus_no_subscribers",
                event_type=event_type.__name__,
            )


# Module-level singleton — used by ChatOrchestrator for internal events.
event_bus = EventBus()
