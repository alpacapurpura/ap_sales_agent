"""Domain tests — TELEGRAM_CONTEXT_WINDOW_CONFIG + dispatcher (PI-5 PR-2).

D-PI5-006: Telegram-specific context window config (more spacious than
web because Telegram sessions are intermittent).
"""

from __future__ import annotations

import pytest

from src.modules.copilot.domain.context_window import (
    DEFAULT_CONTEXT_WINDOW_CONFIG,
    TELEGRAM_CONTEXT_WINDOW_CONFIG,
    ContextWindowConfig,
    get_context_window_config,
)


def test_telegram_config_is_a_context_window_config() -> None:
    assert isinstance(TELEGRAM_CONTEXT_WINDOW_CONFIG, ContextWindowConfig)


def test_telegram_config_byte_exact_values() -> None:
    """D-PI5-006 values must be byte-exact across redeploys."""
    cfg = TELEGRAM_CONTEXT_WINDOW_CONFIG
    assert cfg.RAW_WINDOW_TOKENS == 3000
    assert cfg.RAW_WINDOW_MAX_MESSAGES == 15
    assert cfg.RAW_WINDOW_MIN_MESSAGES == 4
    assert cfg.SUMMARY_MAX_CHARS == 600
    assert cfg.SUMMARY_TARGET_TOKENS == 200
    assert cfg.NUDGE_AFTER_TOTAL_TOKENS == 12_000
    assert cfg.NUDGE_HARD_LIMIT_TOKENS == 20_000
    assert cfg.NUDGE_AFTER_MESSAGE_COUNT == 20
    assert cfg.TOKEN_COUNTER == "tiktoken:cl100k_base"


def test_dispatcher_returns_telegram_for_telegram_channel() -> None:
    assert get_context_window_config("telegram") is TELEGRAM_CONTEXT_WINDOW_CONFIG


def test_dispatcher_returns_default_for_web() -> None:
    assert get_context_window_config("web") is DEFAULT_CONTEXT_WINDOW_CONFIG


def test_dispatcher_returns_default_for_none() -> None:
    """Default ``web`` for None channel — backward compat."""
    assert get_context_window_config(None) is DEFAULT_CONTEXT_WINDOW_CONFIG


@pytest.mark.parametrize("unknown", ["whatsapp", "email", "sms", "", "WEB", "Telegram"])
def test_dispatcher_returns_default_for_unknown(unknown: str) -> None:
    """Unknown / case-mismatched channels fall back to default (graceful)."""
    assert get_context_window_config(unknown) is DEFAULT_CONTEXT_WINDOW_CONFIG


def test_telegram_config_is_distinct_instance_from_default() -> None:
    """TELEGRAM and DEFAULT must be distinct instances (different field values)."""
    assert TELEGRAM_CONTEXT_WINDOW_CONFIG is not DEFAULT_CONTEXT_WINDOW_CONFIG
    assert TELEGRAM_CONTEXT_WINDOW_CONFIG != DEFAULT_CONTEXT_WINDOW_CONFIG
