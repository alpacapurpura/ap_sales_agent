import logging
from collections.abc import Callable

from src.shared.domain.events import DomainEvent

logger = logging.getLogger(__name__)


class EventBus:
    """
    In-memory Event Bus for dispatching domain events.
    """

    def __init__(self):
        self._subscribers: dict[type[DomainEvent], list[Callable]] = {}

    def subscribe(self, event_type: type[DomainEvent], handler: Callable):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.info(
            "Subscribed handler %s to event %s",
            handler.__name__,
            event_type.__name__,
        )

    async def publish(self, event: DomainEvent):
        event_type = type(event)
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    await handler(event)
                except Exception:
                    logger.exception("Error handling event %s", event_type.__name__)
                    # We might want to re-raise or handle errors differently depending on strategy
        else:
            logger.debug("No subscribers for event %s", event_type.__name__)


# Global instance
event_bus = EventBus()
