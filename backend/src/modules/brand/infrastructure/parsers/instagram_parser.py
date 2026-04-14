"""Instagram DM JSON parser (Meta Data Export format)."""

import json
import re
from datetime import datetime, timezone

from .base import Message

# Same emoji regex as WhatsApp parser — shared logic kept local to avoid coupling
_EMOJI_RE = re.compile(
    "["
    "\U0001f600-\U0001f64f"
    "\U0001f300-\U0001f5ff"
    "\U0001f680-\U0001f6ff"
    "\U0001f1e0-\U0001f1ff"
    "\U00002700-\U000027bf"
    "\U0001f900-\U0001f9ff"
    "\U00002600-\U000026ff"
    "\U0001fa00-\U0001fa6f"
    "\U0001fa70-\U0001faff"
    "]+",
    flags=re.UNICODE,
)


def _has_emoji(text: str) -> bool:
    return bool(_EMOJI_RE.search(text))


def _word_count(text: str) -> int:
    return len(text.split())


def _decode_instagram_name(name: str) -> str:
    """Instagram encodes names in Latin-1 inside JSON strings. Decode properly."""
    try:
        return name.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return name


class InstagramParser:
    """Parser for Instagram DM JSON exports (Meta Download Your Information)."""

    def can_parse(self, content: str) -> bool:
        """Return True if the content is a valid Instagram DM JSON export."""
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return False
        return isinstance(data, dict) and "messages" in data and "participants" in data

    def parse(self, content: str, user_name: str | None = None) -> list[Message]:
        """Parse Instagram DM export and return messages from the target user."""
        data = json.loads(content)

        participants: list[dict] = data.get("participants", [])
        raw_messages: list[dict] = data.get("messages", [])

        # Determine target user
        if user_name is None and participants:
            # Use the first participant as the default user
            user_name = _decode_instagram_name(participants[0].get("name", ""))

        messages: list[Message] = []
        for msg in raw_messages:
            # Only process Generic type messages with text content
            if msg.get("type") != "Generic":
                continue
            content_text: str | None = msg.get("content")
            if not content_text:
                continue

            sender_raw: str = msg.get("sender_name", "")
            sender = _decode_instagram_name(sender_raw)

            if user_name is not None and sender != user_name:
                continue

            timestamp_ms: int | None = msg.get("timestamp_ms")
            ts: datetime | None = None
            if timestamp_ms is not None:
                ts = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).replace(tzinfo=None)

            messages.append(
                Message(
                    text=content_text,
                    timestamp=ts,
                    has_emoji=_has_emoji(content_text),
                    word_count=_word_count(content_text),
                    sender=sender,
                )
            )

        return messages
