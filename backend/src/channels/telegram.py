import httpx
from typing import Dict, Any, Optional
from src.core.schema import IncomingMessage, OutgoingMessage
from src.channels.base import BaseChannel
from src.config import settings
import logging

logger = logging.getLogger(__name__)

class TelegramChannel(BaseChannel):
    """
    Adapter for Telegram Bot API.
    """
    
    def normalize_payload(self, payload: Dict[str, Any]) -> Optional[IncomingMessage]:
        """
        Extracts message from Telegram webhook update.
        Structure: { "update_id": ..., "message": { "message_id": ..., "from": {...}, "text": ... } }
        """
        # We only care about text messages for now
        message = payload.get("message")
        
        if not message:
            # Ignore other updates like edited_message, channel_post, etc.
            return None
            
        if "text" not in message:
            # Ignore non-text messages (photos, stickers) for now
            return None
            
        user_data = message.get("from", {})
        user_id = str(user_data.get("id"))
        text = message.get("text", "")
        
        # Extract useful metadata for the agent profile
        metadata = {
            "first_name": user_data.get("first_name", ""),
            "last_name": user_data.get("last_name", ""),
            "username": user_data.get("username", ""),
            "language_code": user_data.get("language_code", ""),
            "source": "telegram"
        }
        
        return IncomingMessage(
            user_id=user_id,
            text=text,
            channel_type="telegram",
            metadata=metadata
        )

    async def send_message(self, message: OutgoingMessage) -> Dict[str, Any]:
        """
        Sends text message to Telegram Chat ID.
        Retries without Markdown if it fails (400 Bad Request).
        """
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.error("TELEGRAM_BOT_TOKEN not set")
            return {"error": "configuration_missing"}
            
        token = settings.TELEGRAM_BOT_TOKEN.strip()
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        
        # Try with Markdown first
        payload = {
            "chat_id": message.user_id,
            "text": message.text,
            "parse_mode": "Markdown" 
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, timeout=10.0)
                response.raise_for_status()
                logger.info(f"Message sent to Telegram user {message.user_id}")
                return response.json()
            except httpx.HTTPStatusError as e:
                # If 400 Bad Request (likely Markdown error), retry as plain text
                if e.response.status_code == 400:
                    logger.warning(f"Telegram Markdown send failed ({e}), retrying as plain text...")
                    payload.pop("parse_mode")
                    retry_response = await client.post(url, json=payload, timeout=10.0)
                    retry_response.raise_for_status()
                    return retry_response.json()
                else:
                    logger.error(f"Failed to send Telegram message: {e}")
                    raise e
            except httpx.HTTPError as e:
                logger.error(f"Failed to send Telegram message (Network): {e}")
                raise e

    async def set_typing_status(self, user_id: str) -> None:
        """
        Sends 'typing' action to Telegram.
        """
        if not settings.TELEGRAM_BOT_TOKEN:
            return

        token = settings.TELEGRAM_BOT_TOKEN.strip()
        url = f"https://api.telegram.org/bot{token}/sendChatAction"
        
        payload = {
            "chat_id": user_id,
            "action": "typing"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                # Fire and forget
                await client.post(url, json=payload, timeout=5.0)
            except Exception as e:
                logger.warning(f"Failed to send typing status to Telegram: {e}")
