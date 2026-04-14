"""Base types and auto-detection for chat parsers."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable


@dataclass
class Message:
    """A single parsed message from a chat export."""

    text: str
    timestamp: datetime | None = None
    has_emoji: bool = False
    word_count: int = 0
    sender: str = ""


@runtime_checkable
class ChatParser(Protocol):
    """Protocol for chat format parsers."""

    def can_parse(self, content: str) -> bool:
        """Check if this parser can handle the given content."""
        ...

    def parse(self, content: str, user_name: str | None = None) -> list[Message]:
        """Parse chat content and return messages from the target user only."""
        ...


def detect_and_parse(content: str, user_name: str | None = None) -> list[Message]:
    """Auto-detect format and parse. Tries each parser in order."""
    from .instagram_parser import InstagramParser
    from .telegram_parser import TelegramParser
    from .whatsapp_parser import WhatsAppParser

    parsers = [WhatsAppParser(), InstagramParser(), TelegramParser()]
    for parser in parsers:
        if parser.can_parse(content):
            return parser.parse(content, user_name)
    msg = "Unsupported chat format. Supported: WhatsApp .txt, Instagram DM JSON, Telegram JSON"
    raise ValueError(msg)
