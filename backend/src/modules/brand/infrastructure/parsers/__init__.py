"""Chat parsers for personality cloning pipeline."""

from .base import ChatParser, Message, detect_and_parse
from .instagram_parser import InstagramParser
from .telegram_parser import TelegramParser
from .whatsapp_parser import WhatsAppParser

__all__ = [
    "ChatParser",
    "InstagramParser",
    "Message",
    "TelegramParser",
    "WhatsAppParser",
    "detect_and_parse",
]
