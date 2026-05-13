"""Analytics domain events."""

from datetime import datetime
from typing import Any
from uuid import UUID

from luana_core_platform.domain.base_entity import BaseEntity
from pydantic import Field


class JourneyEvent(BaseEntity):
    """Represent journey event data."""

    id: UUID
    profile_id: UUID
    tenant_id: UUID | None = None

    event_name: str  # "page_view", "email_opened", "checkout_completed"
    event_type: str  # "track", "page", "screen"

    properties: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)

    occurred_at: datetime | None = None
