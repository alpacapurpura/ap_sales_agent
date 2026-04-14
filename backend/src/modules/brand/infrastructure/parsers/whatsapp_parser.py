"""WhatsApp .txt chat export parser."""

import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime

from .base import Message

# Matches all known WhatsApp timestamp + sender variants:
#   [12/25/23, 3:45:23 PM] - Sender: message
#   12/25/23, 3:45 PM - Sender: message
#   25/12/2023, 15:45 - Sender: message
_LINE_RE = re.compile(
    r"^\[?(\d{1,2}/\d{1,2}/\d{2,4}),?\s+"
    r"(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?)\]?\s*-?\s*"
    r"(.+?):\s*(.+)$"
)

# Media / omitted content patterns (case-insensitive)
_MEDIA_RE = re.compile(
    r"<media omitted>|image omitted|audio omitted|sticker omitted|video omitted|"
    r"document omitted|gif omitted|contact card omitted",
    re.IGNORECASE,
)

# Emoji detection — covers common Unicode emoji ranges
_EMOJI_RE = re.compile(
    "["
    "\U0001f600-\U0001f64f"  # emoticons
    "\U0001f300-\U0001f5ff"  # misc symbols and pictographs
    "\U0001f680-\U0001f6ff"  # transport and map symbols
    "\U0001f1e0-\U0001f1ff"  # flags
    "\U00002700-\U000027bf"  # dingbats
    "\U0001f900-\U0001f9ff"  # supplemental symbols
    "\U00002600-\U000026ff"  # misc symbols
    "\U0001fa00-\U0001fa6f"  # chess symbols + extras
    "\U0001fa70-\U0001faff"  # symbols and pictographs extended-A
    "]+",
    flags=re.UNICODE,
)

# Date formats to try when parsing timestamps (order matters — most specific first)
_DATE_FORMATS = [
    "%m/%d/%y %I:%M:%S %p",
    "%m/%d/%y %I:%M %p",
    "%m/%d/%Y %I:%M:%S %p",
    "%m/%d/%Y %I:%M %p",
    "%d/%m/%Y %H:%M",
    "%d/%m/%y %H:%M",
]


@dataclass
class _RawEntry:
    sender: str
    timestamp: datetime | None
    lines: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(self.lines)


def _parse_timestamp(date_str: str, time_str: str) -> datetime | None:
    combined = f"{date_str} {time_str.strip()}"
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(combined, fmt)  # noqa: DTZ007
        except ValueError:
            continue
    return None


def _has_emoji(text: str) -> bool:
    return bool(_EMOJI_RE.search(text))


def _word_count(text: str) -> int:
    return len(text.split())


class WhatsAppParser:
    """Parser for WhatsApp .txt chat exports."""

    def can_parse(self, content: str) -> bool:
        """Return True if at least one of the first lines matches the WhatsApp timestamp pattern."""
        return any(_LINE_RE.match(line.strip()) for line in content.splitlines()[:20])

    def parse(self, content: str, user_name: str | None = None) -> list[Message]:
        """Parse WhatsApp export and return messages from the target user."""
        if not content.strip():
            return []

        raw_entries: list[_RawEntry] = []
        current: _RawEntry | None = None

        for line in content.splitlines():
            match = _LINE_RE.match(line.strip())
            if match:
                date_s, time_s, sender, text = match.groups()
                ts = _parse_timestamp(date_s, time_s)
                current = _RawEntry(sender=sender, timestamp=ts, lines=[text])
                raw_entries.append(current)
            else:
                # Continuation line — append to current message
                stripped = line.strip()
                if stripped and current is not None:
                    current.lines.append(stripped)

        # Determine target user (most frequent sender if not specified)
        if user_name is None:
            counts: Counter[str] = Counter(e.sender for e in raw_entries)
            if not counts:
                return []
            user_name = counts.most_common(1)[0][0]

        messages: list[Message] = []
        for entry in raw_entries:
            if entry.sender != user_name:
                continue
            text = entry.text
            # Skip media-only messages
            if _MEDIA_RE.search(text):
                continue
            messages.append(
                Message(
                    text=text,
                    timestamp=entry.timestamp,
                    has_emoji=_has_emoji(text),
                    word_count=_word_count(text),
                    sender=entry.sender,
                )
            )

        return messages
