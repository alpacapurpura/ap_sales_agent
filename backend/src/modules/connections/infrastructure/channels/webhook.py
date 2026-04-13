from typing import Any

import structlog

from src.shared.domain.messages import OutgoingMessage

logger = structlog.get_logger()


class WebhookAdapter:
    """
    Adapter for generic Webhook/API integration.
    Collects responses in-memory to return them in the HTTP response.
    """

    def __init__(self) -> None:
        self.responses: list[str] = []

    async def send_message(self, message: OutgoingMessage) -> None:
        """
        Stores the message content.
        """
        logger.info(
            "webhook_adapter_collecting_message",
            user_id=message.user_id,
            text=message.text,
        )
        self.responses.append(message.text)

    async def set_typing_status(self, user_id: str) -> None:
        """
        No-op for API, or could potentially send an intermediate event if we supported streaming.
        For now, just log.
        """
        logger.debug("webhook_adapter_typing", user_id=user_id)

    def normalize_payload(self, payload: Any) -> None:  # noqa: ANN401 — webhook payload structure varies
        """
        Not used in the synchronous flow, but kept for interface consistency.
        """
