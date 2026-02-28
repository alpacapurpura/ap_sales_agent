from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from src.shared.domain.messages import IncomingMessage, OutgoingMessage

class WhatsAppProvider(ABC):
    """
    Abstract Strategy for WhatsApp Evolution API Providers.
    """
    
    def __init__(self, tenant_id: str, base_url: str, api_key: str):
        self.tenant_id = tenant_id
        self.base_url = base_url
        self.headers = {
            "apikey": api_key,
            "Content-Type": "application/json"
        }

    @abstractmethod
    def normalize_payload(self, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
        """Normalize webhook payload to internal schema."""
        pass

    @abstractmethod
    async def send_message(self, message: OutgoingMessage) -> Dict[str, Any]:
        """Send a text message."""
        pass

    @abstractmethod
    async def set_typing_status(self, user_id: str) -> None:
        """Send typing presence."""
        pass
    
    # Management Methods (used by Router)
    @abstractmethod
    async def create_instance(self, token: str) -> Dict[str, Any]:
        """Create a new instance."""
        pass
        
    @abstractmethod
    async def delete_instance(self) -> Dict[str, Any]:
        """Delete the instance."""
        pass
        
    @abstractmethod
    async def check_status(self) -> Dict[str, Any]:
        """Check connection status."""
        pass
        
    @abstractmethod
    async def get_qr(self) -> Dict[str, Any]:
        """Get QR code."""
        pass
        
    @abstractmethod
    async def configure_webhook(self, webhook_url: str) -> Dict[str, Any]:
        """Configure webhook."""
        pass
        
    @abstractmethod
    async def logout(self) -> Dict[str, Any]:
        """Logout instance."""
        pass
