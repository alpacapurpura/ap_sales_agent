"""Context window configuration for the rolling summary mechanism."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ContextWindowConfig:
    """Configuration constants for the context window / rolling summarizer.

    Defaults reflect CONTRACT §2.3 values.
    """

    RAW_WINDOW_TOKENS: int = 2000
    RAW_WINDOW_MAX_MESSAGES: int = 10
    RAW_WINDOW_MIN_MESSAGES: int = 4
    SUMMARY_MAX_CHARS: int = 400
    SUMMARY_TARGET_TOKENS: int = 150
    NUDGE_AFTER_TOTAL_TOKENS: int = 8000
    NUDGE_HARD_LIMIT_TOKENS: int = 16000
    NUDGE_AFTER_MESSAGE_COUNT: int = 12
    TOKEN_COUNTER: str = "tiktoken:cl100k_base"


DEFAULT_CONTEXT_WINDOW_CONFIG = ContextWindowConfig()


# PI-5 PR-2 — Telegram context window (D-PI5-006).
#
# Telegram sessions are intermittent: a user may message the bot at 9am
# from the bus and again at 3pm from the office. Web sessions are
# typically a single focused work session. The Telegram config keeps a
# wider raw window (3000 tokens vs 2000 web) and a longer summary cap
# (600 chars vs 400 web) so the agent can re-thread context without
# pinging the user with "remember when you said...".
TELEGRAM_CONTEXT_WINDOW_CONFIG: ContextWindowConfig = ContextWindowConfig(
    RAW_WINDOW_TOKENS=3000,
    RAW_WINDOW_MAX_MESSAGES=15,
    RAW_WINDOW_MIN_MESSAGES=4,
    SUMMARY_MAX_CHARS=600,
    SUMMARY_TARGET_TOKENS=200,
    NUDGE_AFTER_TOTAL_TOKENS=12_000,
    NUDGE_HARD_LIMIT_TOKENS=20_000,
    NUDGE_AFTER_MESSAGE_COUNT=20,
    TOKEN_COUNTER="tiktoken:cl100k_base",
)


def get_context_window_config(channel: str | None) -> ContextWindowConfig:
    """Resolve the context-window config for ``channel``.

    Pure side-effect-free dispatcher. Returns ``TELEGRAM_CONTEXT_WINDOW_CONFIG``
    only on the literal string ``"telegram"``; everything else (including
    ``None``, ``"web"``, ``"whatsapp"``, unknown variants, case-mismatched
    inputs) falls back to ``DEFAULT_CONTEXT_WINDOW_CONFIG`` for backward
    compatibility.

    The strict equality check is intentional — silently widening the
    matcher (e.g., case-insensitive comparison) would mask config drift
    in upstream callers.
    """
    if channel == "telegram":
        return TELEGRAM_CONTEXT_WINDOW_CONFIG
    return DEFAULT_CONTEXT_WINDOW_CONFIG


__all__ = (
    "DEFAULT_CONTEXT_WINDOW_CONFIG",
    "TELEGRAM_CONTEXT_WINDOW_CONFIG",
    "ContextWindowConfig",
    "get_context_window_config",
)
