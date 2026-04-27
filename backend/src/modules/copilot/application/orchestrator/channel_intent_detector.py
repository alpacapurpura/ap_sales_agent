"""FP2 — channel intent detection middleware (B24).

Detects when a user explicitly asks for output in a specific output channel
(WhatsApp / email / SMS / Instagram DM / Telegram / voice). The orchestrator
uses this signal to inject a system-prompt hint forcing the AGENT to invoke
``format_for_channel`` before finalising the turn — Kimi K2.6 phrasing-
sensitive routing (B11-TP6) drops the tool call inconsistently otherwise.

Design choices:

* **Regex normalised** (lowercase + word boundary + URL negative lookahead)
  rather than embedding similarity. Pre-research insight 2026-04: short
  utterances (5-30 chars, "armame copy WhatsApp") are well-served by
  keyword detection — embeddings overfit on noise and add LLM call cost.
* **AC7 false-positive guard**: ``whatsapp.com`` / ``https://wa.me/...``
  must NOT match. Negative lookahead on URL-ish trailing chars (``.com``
  / ``.org`` / ``.net`` / ``/``) and look-behind on URL scheme (``://``).
* **ChannelIntent dataclass** carries channel id + label + match span so
  observability (trace events) records *why* the formatter was forced.
* **Backwards compat**: ``output_sanitizer.detect_channel_in_user_msg``
  re-exports the legacy string API, no callers break.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChannelIntent:
    """A detected request to format output for a specific channel.

    Attributes:
        channel: Canonical id (``whatsapp`` / ``email`` / ``sms`` /
            ``telegram`` / ``instagram_dm`` / ``voice``). Matches the
            ids in ``copilot.domain.output_channels.CHANNEL_FORMATS``
            so the system-prompt hint can directly name the
            ``format_for_channel`` ``channel_id`` argument.
        label: Human-readable Spanish-neutro label for telemetry.
        matched_span: ``(start, end)`` index in the user message where
            the keyword landed — useful when the trace recorder wants
            to surface the exact phrase.
    """

    channel: str
    label: str
    matched_span: tuple[int, int]


# Negative lookahead applied right after every channel keyword: rejects
# typical URL trailing patterns. ``\.[a-z]{2,}`` covers ``.com`` / ``.org``
# / ``.net`` / ``.com.au`` etc; ``/`` rejects ``wa.me/...``. Look-BEHIND
# on ``://`` would be ideal but variable-width lookbehind is unsupported
# in the stdlib ``re`` module — instead we wrap the keyword detection so
# ``https://whatsapp.com`` is filtered by the trailing ``.com`` guard.
_URL_TAIL = r"(?!\.[a-z]{2,}|/)"


# Order matters: more specific patterns (``instagram_dm``) come before
# generic single-word ones to win the alternation. Each entry is
# ``(compiled regex, canonical channel id, human label)``.
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
    in pattern order wins — Instagram DM beats Email beats WhatsApp etc.,
    matching the priority in ``_CHANNEL_PATTERNS``.
    """
    if not user_msg:
        return None
    text = user_msg
    for pattern, channel_id, label in _CHANNEL_PATTERNS:
        match = pattern.search(text)
        if match is None:
            continue
        # Look-behind URL scheme guard (variable-width — done manually
        # since stdlib ``re`` cannot express it). When the match starts
        # mid-URL ("https://wa.me/..."), reject it.
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
    """Legacy string API — returns just the channel id or ``None``.

    Kept so ``output_sanitizer`` and existing tests don't rebuild the
    intent dataclass when they only need the id. New callers should use
    ``detect_channel_intent`` so the trace recorder can record the matched
    span + label.
    """
    intent = detect_channel_intent(user_msg)
    return intent.channel if intent is not None else None


__all__ = (
    "ChannelIntent",
    "detect_channel_in_user_msg",
    "detect_channel_intent",
)
