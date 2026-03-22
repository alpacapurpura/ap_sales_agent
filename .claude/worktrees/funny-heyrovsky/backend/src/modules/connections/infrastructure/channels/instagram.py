import logging
from typing import Dict, Any, Optional
import httpx

from src.shared.infrastructure.channels.base import BaseChannel
from src.modules.connections.infrastructure.channels.meta import MetaAdapter
from src.shared.domain.messages import IncomingMessage, OutgoingMessage

logger = logging.getLogger(__name__)

class InstagramChannel(MetaAdapter, BaseChannel):
    """
    Channel adapter for Instagram via Meta Graph API.
    Inherits from MetaAdapter for OAuth/Token handling.
    Inherits from BaseChannel for unified interface.
    """
    
    def __init__(self, client_config: Dict[str, Any], credentials_data: Optional[Dict[str, Any]] = None):
        access_token = credentials_data.get("access_token") if credentials_data else None
        super().__init__(access_token=access_token)
        self.client_config = client_config or {}
        # Ensure API version is set, defaulting if not present in parent
        if not hasattr(self, 'API_VERSION'):
            self.API_VERSION = "v19.0"
        if not hasattr(self, 'BASE_URL'):
            self.BASE_URL = "https://graph.facebook.com"

    def normalize_payload(self, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
        """
        Normalize Instagram Webhook Payload.
        Docs: https://developers.facebook.com/docs/messenger-platform/instagram/features/webhook
        """
        try:
            # Handle list of entries (usually just one)
            entries = payload.get("entry", [])
            if not entries:
                return None
                
            entry = entries[0]
            messaging_list = entry.get("messaging", [])
            
            if not messaging_list:
                return None
                
            messaging = messaging_list[0]
            
            sender_id = messaging.get("sender", {}).get("id")
            
            # Check for message object
            message = messaging.get("message", {})
            text = message.get("text")
            
            if not sender_id or not text:
                # Log but return None for non-text messages (likes, deliveries, reads)
                # logger.debug("Ignored non-text or system message", extra={"payload_keys": payload.keys()})
                return None
                
            return IncomingMessage(
                user_id=sender_id,
                text=text,
                channel_type="instagram",
                metadata={
                    "message_id": message.get("mid"),
                    "recipient_id": messaging.get("recipient", {}).get("id"),
                    "timestamp": messaging.get("timestamp"),
                    "is_echo": message.get("is_echo", False)
                }
            )
        except (IndexError, AttributeError) as e:
            logger.warning(f"Failed to normalize Instagram payload: {e}")
            return None

    async def send_message(self, message: OutgoingMessage) -> Dict[str, Any]:
        """
        Send message via Instagram Graph API.
        Docs: https://developers.facebook.com/docs/messenger-platform/instagram/features/send-message
        """
        if not self.access_token:
             raise ValueError("Missing access_token for InstagramChannel")

        url = f"{self.BASE_URL}/{self.API_VERSION}/me/messages"
        
        recipient_id = message.user_id
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "recipient": {"id": recipient_id},
            "message": {"text": message.text}
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, headers=headers)
            response.raise_for_status()
            return response.json()

    async def set_typing_status(self, user_id: str) -> None:
        """
        Send 'typing_on' sender action.
        """
        if not self.access_token:
            return

        url = f"{self.BASE_URL}/{self.API_VERSION}/me/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "recipient": {"id": user_id},
            "sender_action": "typing_on"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                await client.post(url, json=data, headers=headers)
        except Exception as e:
            logger.warning(f"Failed to set typing status: {e}")
