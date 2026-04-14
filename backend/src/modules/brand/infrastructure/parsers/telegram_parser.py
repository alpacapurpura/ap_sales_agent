"""Telegram Desktop JSON export parser."""

import contextlib
import json
import re
from collections import Counter
from datetime import datetime

from .base import Message

# Same emoji regex — kept local to avoid coupling between parsers
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


def _extract_text(raw_text: str | list) -> str:
    """Handle Telegram text field being either a plain string or a list of text entities."""
    if isinstance(raw_text, str):
        return raw_text
    # List of text entities: [{type: "plain", text: "..."}, {type: "bold", text: "..."}, ...]
    parts: list[str] = []
    for entity in raw_text:
        if isinstance(entity, dict):
            parts.append(entity.get("text", ""))
        elif isinstance(entity, str):
            parts.append(entity)
    return "".join(parts)


class TelegramParser:
    """Parser for Telegram Desktop JSON chat exports."""

    def can_parse(self, content: str) -> bool:
        """Return True if content is a valid Telegram export JSON."""
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return False
        if not isinstance(data, dict) or "messages" not in data:
            return False
        messages = data.get("messages", [])
        if not messages:
            return False
        # Telegram messages have a "from" field; Instagram messages have "sender_name"
        first = messages[0] if messages else {}
        return isinstance(first, dict) and "from" in first

    def parse(self, content: str, user_name: str | None = None) -> list[Message]:
        """Parse Telegram export and return messages from the target user."""
        data = json.loads(content)
        raw_messages: list[dict] = data.get("messages", [])

        # Filter only actual messages (skip service events)
        msg_entries = [m for m in raw_messages if m.get("type") == "message"]

        # Determine target user (most frequent sender if not specified)
        if user_name is None:
            counts: Counter[str] = Counter(m.get("from", "") for m in msg_entries if m.get("from"))
            if not counts:
                return []
            user_name = counts.most_common(1)[0][0]

        messages: list[Message] = []
        for msg in msg_entries:
            sender: str = msg.get("from", "")
            if sender != user_name:
                continue

            raw_text = msg.get("text", "")
            text = _extract_text(raw_text)

            # Skip empty messages (media-only, etc.)
            if not text.strip():
                continue

            date_str: str | None = msg.get("date")
            ts: datetime | None = None
            if date_str:
                with contextlib.suppress(ValueError):
                    ts = datetime.fromisoformat(date_str)

            messages.append(
                Message(
                    text=text,
                    timestamp=ts,
                    has_emoji=_has_emoji(text),
                    word_count=_word_count(text),
                    sender=sender,
                )
            )

        return messages
