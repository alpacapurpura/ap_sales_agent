import httpx
from typing import Any, Optional, Dict
from src.channels.base import BaseChannel
from src.core.schema import IncomingMessage, OutgoingMessage
from src.config import settings
import logging

logger = logging.getLogger(__name__)

class WhatsAppChannel(BaseChannel):
    """
    Adaptador para Meta WhatsApp Cloud API.
    """
    
    def __init__(self):
        self.api_url = f"https://graph.facebook.com/v18.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        self.headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}",
            "Content-Type": "application/json",
        }

    def normalize_payload(self, request: Dict[str, Any]) -> Optional[IncomingMessage]:
        """
        Extrae mensaje de la estructura compleja de Meta.
        """
        try:
            entry = request.get("entry", [])[0]
            changes = entry.get("changes", [])[0]
            value = changes.get("value", {})
            
            if "messages" not in value:
                return None
                
            message = value["messages"][0]
            if message["type"] != "text":
                return None
                
            user_id = message["from"] # Phone number
            text = message["text"]["body"]
            name = value.get("contacts", [{}])[0].get("profile", {}).get("name", "")
            
            return IncomingMessage(
                user_id=user_id,
                text=text,
                channel_type="whatsapp",
                metadata={"name": name, "wa_id": message["id"]}
            )
        except (IndexError, KeyError):
            return None

    async def send_message(self, message: OutgoingMessage) -> None:
        """
        Envía respuesta a WhatsApp.
        """
        data = {
            "messaging_product": "whatsapp",
            "to": message.user_id,
            "type": "text",
            "text": {"body": message.text},
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.api_url, headers=self.headers, json=data)
                response.raise_for_status()
            except Exception as e:
                logger.error(f"Error sending to WhatsApp: {e}")
                raise
