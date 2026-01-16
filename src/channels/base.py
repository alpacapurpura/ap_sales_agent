from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from src.core.schema import IncomingMessage, OutgoingMessage

class BaseChannel(ABC):
    """
    Abstract base class for channel adapters.
    Enforces the Port (Interface) for all external communication channels.
    """
    
    @abstractmethod
    def normalize_payload(self, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
        """
        Convert raw webhook payload to unified IncomingMessage.
        Returns None if the payload should be ignored (e.g. status updates).
        """
        pass
        
    @abstractmethod
    async def send_message(self, message: OutgoingMessage) -> Dict[str, Any]:
        """
        Send unified OutgoingMessage to the specific channel API.
        """
        pass
