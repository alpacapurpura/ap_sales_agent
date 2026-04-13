"""Abstract base class for external communication channel adapters."""

from abc import ABC, abstractmethod
from typing import Any

from src.shared.domain.messages import IncomingMessage, OutgoingMessage


class BaseChannel(ABC):
    """Abstract port for all external communication channels.

    Enforces a unified interface for normalizing inbound payloads
    and sending outbound messages.
    """

    @abstractmethod
    def normalize_payload(self, payload: dict[str, Any]) -> IncomingMessage | None:
        """Convert raw webhook payload to unified IncomingMessage.

        Return None if the payload should be ignored (e.g. status updates).
        """

    @abstractmethod
    async def send_message(self, message: OutgoingMessage) -> dict[str, Any]:
        """Send unified OutgoingMessage to the specific channel API."""

    @abstractmethod
    async def set_typing_status(self, user_id: str) -> None:
        """Send 'typing...' status to the channel."""
