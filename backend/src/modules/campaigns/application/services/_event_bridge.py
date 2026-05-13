"""Event bridge: campaigns Pydantic events → OutboxService-compatible DomainEvent.

Campaign events are Pydantic BaseModels (for type-safe serialization).
OutboxService.enqueue_async_from_sync_caller expects DomainEvent (dataclass with
event_name + tenant_id + occurred_at + payload).

This module provides a thin adapter that wraps campaign Pydantic events.
_PydanticEventAdapter inherits from DomainEvent so OutboxService type-checks pass
without any type: ignore (S1 cross-PR contract — PR-3 events are Pydantic, PR-1
OutboxService expects DomainEvent dataclass; adapter bridges both without modifying
shared/ OutboxService or the campaign domain events).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from luana_core_platform.domain.events import DomainEvent


@dataclass
class _PydanticEventAdapter(DomainEvent):
    """Adapter making a campaign Pydantic event compatible with OutboxEntry.from_event.

    Inherits DomainEvent so OutboxService.enqueue_async_from_sync_caller type-checks.
    OutboxEntry.from_event accesses: event.tenant_id, event.event_name, event.payload.
    Campaign events have: event.tenant_id, event.EVENT_NAME (class attr), event.model_dump().
    """


def to_domain_event(pydantic_event: Any) -> _PydanticEventAdapter:
    """Convert a campaign Pydantic event to an OutboxService-compatible shape.

    Reads EVENT_NAME class attribute and model_dump() for payload.
    """
    event_name: str = pydantic_event.EVENT_NAME  # class-level Literal
    tenant_id: UUID = pydantic_event.tenant_id
    occurred_at: dt.datetime = pydantic_event.occurred_at

    # Payload = full model dump minus tenant_id and occurred_at (already on envelope)
    payload = pydantic_event.model_dump(mode="json")
    payload.pop("EVENT_NAME", None)

    return _PydanticEventAdapter(
        tenant_id=tenant_id,
        event_name=event_name,
        occurred_at=occurred_at,
        payload=payload,
    )
