from typing import Callable, Type, List, Dict
from src.shared.domain.events import DomainEvent
import logging

logger = logging.getLogger(__name__)

class EventBus:
    """
    In-memory Event Bus for dispatching domain events.
    """
    def __init__(self):
        self._subscribers: Dict[Type[DomainEvent], List[Callable]] = {}

    def subscribe(self, event_type: Type[DomainEvent], handler: Callable):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.info(f"Subscribed handler {handler.__name__} to event {event_type.__name__}")

    async def publish(self, event: DomainEvent):
        event_type = type(event)
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Error handling event {event_type.__name__}: {str(e)}")
                    # We might want to re-raise or handle errors differently depending on strategy
        else:
            logger.debug(f"No subscribers for event {event_type.__name__}")

# Global instance
event_bus = EventBus()
