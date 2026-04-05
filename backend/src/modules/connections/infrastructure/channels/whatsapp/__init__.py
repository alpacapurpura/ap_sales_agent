from typing import Any

from src.shared.domain.messages import IncomingMessage, OutgoingMessage
from src.shared.infrastructure.channels.base import BaseChannel

from .factory import get_whatsapp_provider


class WhatsAppChannel(BaseChannel):
    """
    Facade for WhatsApp Channel.
    Delegates to the configured Evolution API Provider (V1/V2).
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.provider = get_whatsapp_provider(tenant_id)

    def normalize_payload(self, payload: dict[str, Any]) -> IncomingMessage | None:
        return self.provider.normalize_payload(payload)

    async def send_message(self, message: OutgoingMessage) -> dict[str, Any]:
        return await self.provider.send_message(message)

    async def set_typing_status(self, user_id: str) -> None:
        return await self.provider.set_typing_status(user_id)

    # Management Accessors
    # The Router can access self.provider directly or via these wrappers

    async def create_instance(self, token: str) -> dict[str, Any]:
        return await self.provider.create_instance(token)

    async def delete_instance(self) -> dict[str, Any]:
        return await self.provider.delete_instance()

    async def check_status(self) -> dict[str, Any]:
        return await self.provider.check_status()

    async def get_qr(self) -> dict[str, Any]:
        return await self.provider.get_qr()

    async def configure_webhook(self, webhook_url: str) -> dict[str, Any]:
        return await self.provider.configure_webhook(webhook_url)

    async def logout(self) -> dict[str, Any]:
        return await self.provider.logout()
