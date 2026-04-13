"""Channel domain module."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from src.modules.connections.domain.enums import ChannelType
from src.shared.domain.base_entity import BaseEntity


class ChannelConnection(BaseEntity):
    """Channel Connection."""

    id: UUID
    tenant_id: UUID
    channel_type: ChannelType

    # Credentials (e.g., {"bot_token": "..."})
    credentials: dict[str, Any] = Field(default_factory=dict)

    # Configuration (e.g., {"welcome_message": "...", "bot_name": "..."})
    config: dict[str, Any] = Field(default_factory=dict)

    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None
