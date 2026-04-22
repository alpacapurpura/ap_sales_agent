"""Abstract base class for external communication channel adapters."""

from abc import ABC, abstractmethod
from typing import Any

from src.shared.domain.messages import IncomingMessage, OutgoingMessage


class BaseChannel(ABC):
    """Abstract port for all external communication channels.

    Enforces a unified interface for normalizing inbound payloads
    and sending outbound messages, including rich multimodal blocks.

    Rich channels override send_rich_message to consume OutgoingMessage.blocks.
    Text-only channels inherit the default fallback (text only via send_message).
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

    async def send_rich_message(self, message: OutgoingMessage) -> dict[str, Any]:
        """Send a rich multimodal message. Override for native block support.

        # [COPILOT-CHANNEL-RENDERER] → docs/domains/copilot/channel-adapters.md

        Default implementation sends ``message.text`` via send_message, dropping
        blocks gracefully. This is safe because OutgoingMessage invariant (§4.0
        of CONTRACT-MULTIMODAL) guarantees ``text`` is the flattened plain-text
        equivalent of ``blocks``.

        Rich channels (WhatsApp, Telegram) override this method and iterate
        ``message.blocks``, dispatching each block to the channel-native API.
        See docs/domains/copilot/channel-adapters.md for the checklist.
        """
        return await self.send_message(message)
