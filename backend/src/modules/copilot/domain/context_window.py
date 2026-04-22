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
