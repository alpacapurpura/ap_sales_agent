from abc import ABC, abstractmethod
from typing import Any

from src.shared.domain.messages import IncomingMessage, OutgoingMessage


class BaseChannel(ABC):
    """
    Abstract base class for channel adapters.
    Enforces the Port (Interface) for all external communication channels.
    """

    @abstractmethod
    def normalize_payload(self, payload: dict[str, Any]) -> IncomingMessage | None:
        """
        Convert raw webhook payload to unified IncomingMessage.
        Returns None if the payload should be ignored (e.g. status updates).
        """

    @abstractmethod
    async def send_message(self, message: OutgoingMessage) -> dict[str, Any]:
        """
        Send unified OutgoingMessage to the specific channel API.
        """

    @abstractmethod
    async def set_typing_status(self, user_id: str) -> None:
        """
        Send 'typing...' status to the channel.
        """
