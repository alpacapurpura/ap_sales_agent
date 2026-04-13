"""Domain message value objects for cross-channel communication."""

from typing import Any

from src.shared.domain.base_entity import BaseEntity


class IncomingMessage(BaseEntity):
    """Inbound message from a user across any channel."""

    user_id: str
    text: str
    channel_type: str
    metadata: dict[str, Any] = {}


class OutgoingMessage(BaseEntity):
    """Outbound message to a user across any channel."""

    user_id: str
    text: str
    channel_type: str | None = None
    metadata: dict[str, Any] = {}
