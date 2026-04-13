"""Interface channel adapter."""

from abc import ABC, abstractmethod
from typing import Any

from src.shared.domain.messages import IncomingMessage, OutgoingMessage


class WhatsAppProvider(ABC):
    """Abstract Strategy for WhatsApp Evolution API Providers."""

    def __init__(self, tenant_id: str, base_url: str, api_key: str) -> None:
        """Initialize instance."""
        self.tenant_id = tenant_id
        self.base_url = base_url
        self.headers = {"apikey": api_key, "Content-Type": "application/json"}

    @abstractmethod
    def normalize_payload(self, payload: dict[str, Any]) -> IncomingMessage | None:
        """Normalize webhook payload to internal schema."""

    @abstractmethod
    async def send_message(self, message: OutgoingMessage) -> dict[str, Any]:
        """Send a text message."""

    @abstractmethod
    async def set_typing_status(self, user_id: str) -> None:
        """Send typing presence."""

    # Management Methods (used by Router)
    @abstractmethod
    async def create_instance(self, token: str) -> dict[str, Any]:
        """Create a new instance."""

    @abstractmethod
    async def delete_instance(self) -> dict[str, Any]:
        """Delete the instance."""

    @abstractmethod
    async def check_status(self) -> dict[str, Any]:
        """Check connection status."""

    @abstractmethod
    async def get_qr(self) -> dict[str, Any]:
        """Get QR code."""

    @abstractmethod
    async def configure_webhook(self, webhook_url: str) -> dict[str, Any]:
        """Configure webhook."""

    @abstractmethod
    async def logout(self) -> dict[str, Any]:
        """Logout instance."""
