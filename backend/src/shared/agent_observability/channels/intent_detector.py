"""Channel intent detection — regex-based (S5).

Migrado desde ``src/modules/copilot/application/orchestrator/channel_intent_detector.py``
con cero cambio de comportamiento. Sales_agent puede consumir cuando el lead
pide explícito otro canal ("mándame por WhatsApp", "preferiría correo").

Diseño preservado de F7 copilot:

* **Regex normalised** (lowercase + word boundary + URL negative lookahead).
* **AC7 false-positive guard**: ``whatsapp.com`` / ``https://wa.me/...``
  must NOT match. Negative lookahead on URL-ish trailing chars.
* **ChannelIntent dataclass** carries channel id + label + match span.

# [SALES-AGENT-CHANNEL-REGISTRY-S5] -> docs/domains/sales-agent/redesign-2026-04/phases/S5-channel-registry.md
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChannelIntent:
    """A detected request to format output for a specific channel.

    Attributes:
        channel: Canonical id (``whatsapp`` / ``email`` / ``sms`` /
            ``telegram`` / ``instagram_dm`` / ``voice``).
        label: Human-readable Spanish-neutro label for telemetry.
        matched_span: ``(start, end)`` index in the user message where the
            keyword landed.
    """

    channel: str
    label: str
    matched_span: tuple[int, int]


# Negative lookahead applied right after every channel keyword: rejects
# typical URL trailing patterns. ``\.[a-z]{2,}`` covers ``.com`` / ``.org``
# / ``.net`` / ``.com.au`` etc; ``/`` rejects ``wa.me/...``.
_URL_TAIL = r"(?!\.[a-z]{2,}|/)"


# Order matters: more specific patterns (``instagram_dm``) come before
# generic single-word ones to win the alternation.
_CHANNEL_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (
        re.compile(rf"\binstagram[ _-]?dm\b{_URL_TAIL}|\bIG[ _-]?DM\b{_URL_TAIL}", re.IGNORECASE),
        "instagram_dm",
        "Instagram DM",
    ),
    (
        re.compile(rf"\bwhats[ _-]?app\b{_URL_TAIL}|\bWA\b{_URL_TAIL}", re.IGNORECASE),
        "whatsapp",
        "WhatsApp",
    ),
    (
        re.compile(rf"\btelegram\b{_URL_TAIL}", re.IGNORECASE),
        "telegram",
        "Telegram",
    ),
    (
        re.compile(rf"\bsms\b{_URL_TAIL}|\bmensaje de texto\b", re.IGNORECASE),
        "sms",
        "SMS",
    ),
    (
        re.compile(
            rf"\bemail\b{_URL_TAIL}|\bcorreo electr[oó]nico\b|\bcorreo\b|\bgmail\b{_URL_TAIL}",
            re.IGNORECASE,
        ),
        "email",
        "Email",
    ),
    (
        re.compile(rf"\b(audio|voz|voice|tts)\b{_URL_TAIL}", re.IGNORECASE),
        "voice",
        "Audio",
    ),
]


def detect_channel_intent(user_msg: str | None) -> ChannelIntent | None:
    """Return a ``ChannelIntent`` when the user asks for a specific channel.

    Returns ``None`` when no channel keyword is found OR when every match
    is a URL mention (AC7). When multiple channels appear, the first match
    in pattern order wins.
    """
    if not user_msg:
        return None
    text = user_msg
    for pattern, channel_id, label in _CHANNEL_PATTERNS:
        match = pattern.search(text)
        if match is None:
            continue
        start = match.start()
        prefix = text[max(0, start - 8) : start].lower()
        if "://" in prefix or prefix.endswith(("www.", "http", "https")):
            continue
        return ChannelIntent(
            channel=channel_id,
            label=label,
            matched_span=(start, match.end()),
        )
    return None


def detect_channel_in_user_msg(user_msg: str | None) -> str | None:
    """Legacy string API — returns just the channel id or ``None``."""
    intent = detect_channel_intent(user_msg)
    return intent.channel if intent is not None else None


__all__ = (
    "ChannelIntent",
    "detect_channel_in_user_msg",
    "detect_channel_intent",
)
