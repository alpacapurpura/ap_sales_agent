import httpx
from typing import Any, Optional, Dict
from src.channels.base import BaseChannel
from src.core.schema import IncomingMessage, OutgoingMessage
from src.config import settings
import logging

logger = logging.getLogger(__name__)

class TelegramChannel(BaseChannel):
    """
    Adaptador para la API de Bots de Telegram.
    """
    
    def __init__(self):
        self.api_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"

    def normalize_payload(self, request: Dict[str, Any]) -> Optional[IncomingMessage]:
        """
        Telegram envía un objeto Update:
        {
            "update_id": 1234,
            "message": {
                "message_id": 1,
                "from": {"id": 123, "first_name": "Chris", ...},
                "chat": {"id": 123, ...},
                "date": 123456,
                "text": "Hola"
            }
        }
        """
        if "message" not in request:
            # Podría ser edited_message, callback_query, etc. Ignorar por ahora.
            return None
            
        msg = request["message"]
        
        # Validar que sea texto
        if "text" not in msg:
            return None
            
        user_id = str(msg["chat"]["id"])
        text = msg["text"]
        
        # Extraer metadatos útiles
        metadata = {
            "first_name": msg.get("from", {}).get("first_name", ""),
            "username": msg.get("from", {}).get("username", ""),
            "message_id": msg.get("message_id")
        }
        
        return IncomingMessage(
            user_id=user_id,
            text=text,
            channel_type="telegram",
            metadata=metadata
        )

    async def send_message(self, message: OutgoingMessage) -> None:
        """
        Envía respuesta a Telegram usando sendMessage.
        """
        endpoint = f"{self.api_url}/sendMessage"
        
        payload = {
            "chat_id": message.user_id,
            "text": message.text,
            "parse_mode": "Markdown" # Opcional, para formato
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
            except Exception as e:
                logger.error(f"Error sending to Telegram: {e}")
                raise
