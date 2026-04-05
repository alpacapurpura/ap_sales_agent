from typing import Any

from src.shared.domain.base_entity import BaseEntity


class IncomingMessage(BaseEntity):
    user_id: str
    text: str
    channel_type: str
    metadata: dict[str, Any] = {}


class OutgoingMessage(BaseEntity):
    user_id: str
    text: str
    channel_type: str | None = None
    metadata: dict[str, Any] = {}
