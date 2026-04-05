from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from src.modules.sales_agent.domain.enums import MessageSender
from src.shared.domain.base_entity import BaseEntity


class Message(BaseEntity):
    id: UUID
    lead_id: UUID | None = None
    tenant_id: UUID | None = None

    sender_type: MessageSender
    content: str
    channel: str | None = None  # whatsapp / telegram
    external_id: str | None = None  # Message ID from channel

    metadata_info: dict[str, Any] = Field(default_factory=dict)

    created_at: datetime | None = None
