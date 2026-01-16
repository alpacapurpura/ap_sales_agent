import httpx
from typing import Dict, Any, Optional
from src.core.schema import IncomingMessage, OutgoingMessage
from src.channels.base import BaseChannel
from src.config import settings
import logging

logger = logging.getLogger(__name__)

class WhatsAppChannel(BaseChannel):
    """
    Adapter for WhatsApp Business API (Cloud API).
    """
    
    def normalize_payload(self, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
        """
        Extracts message from WhatsApp Cloud API webhook.
        Structure: entry[0].changes[0].value.messages[0]
        """
        try:
            entry = payload.get("entry", [])
            if not entry:
                return None
                
            changes = entry[0].get("changes", [])
            if not changes:
                return None
                
            value = changes[0].get("value", {})
            if "messages" not in value:
                # Status updates (sent, delivered, read) come here too
                return None
                
            messages = value.get("messages", [])
            if not messages:
                return None
                
            message = messages[0]
            
            if message.get("type") != "text":
                # Handle only text for now
                return None
                
            user_id = message.get("from") # Phone number
            text_body = message.get("text", {}).get("body", "")
            
            # Metadata
            contacts = value.get("contacts", [])
            profile_name = ""
            if contacts:
                profile_name = contacts[0].get("profile", {}).get("name", "")
                
            metadata = {
                "name": profile_name,
                "wa_id": message.get("id"),
                "source": "whatsapp"
            }
            
            return IncomingMessage(
                user_id=user_id,
                text=text_body,
                channel_type="whatsapp",
                metadata=metadata
            )
            
        except (IndexError, KeyError, AttributeError) as e:
            logger.debug(f"Skipping non-message WhatsApp payload: {e}")
            return None

    async def send_message(self, message: OutgoingMessage) -> Dict[str, Any]:
        """
        Sends text message via WhatsApp Cloud API.
        """
        if not settings.WHATSAPP_API_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
             logger.error("WhatsApp configuration missing")
             return {"error": "configuration_missing"}

        url = f"https://graph.facebook.com/v18.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}",
            "Content-Type": "application/json",
        }
        
        data = {
            "messaging_product": "whatsapp",
            "to": message.user_id,
            "type": "text",
            "text": {"body": message.text},
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, headers=headers, json=data)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Failed to send WhatsApp message: {e}")
                # Don't raise, just log, so we don't crash the webhook handler
                return {"error": str(e)}
