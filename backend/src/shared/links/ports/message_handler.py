"""MessageHandlerPort — cross-module port for incoming message handling.

``connections`` endpoints use this port to route incoming channel messages
(Meta, Telegram, WhatsApp, generic webhook) to the sales agent without
importing the orchestrator directly.

Canonical implementation: ``sales_agent.application.orchestrator.chat.ChatOrchestrator``
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import BackgroundTasks
    from luana_core_platform.domain.messages import IncomingMessage
    from luana_core_platform.infrastructure.channels.base import BaseChannel
    from sqlalchemy.orm import Session


class MessageHandlerPort(ABC):
    """Port for routing incoming channel messages to the sales agent."""

    @abstractmethod
    async def process_chat_flow(
        self,
        channel_adapter: BaseChannel,
        incoming: IncomingMessage,
        tenant_id: str | None = None,
    ) -> None:
        """Process a fully normalized incoming message through the agent flow."""
        ...

    @abstractmethod
    async def handle_telegram_webhook(
        self,
        payload: dict,
        background_tasks: BackgroundTasks,
        tenant_id: str | None = None,
        db: Session | None = None,
    ) -> None:
        """Handle a raw Telegram webhook payload."""
        ...

    @abstractmethod
    async def handle_incoming_webhook(
        self,
        channel_adapter: BaseChannel,
        payload: dict,
        background_tasks: BackgroundTasks | None,
        tenant_id: str | None = None,
    ) -> None:
        """Handle a raw webhook payload via a channel adapter (normalize + buffer + debounce)."""
        ...
