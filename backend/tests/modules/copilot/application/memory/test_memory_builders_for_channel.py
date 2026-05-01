"""Tests for ``ContextWindowBuilder.for_channel`` + ``RollingSummarizer.for_channel``.

PI-5 PR-2 (Q6 PM-resolved): classmethod is canonical builder, ``__init__``
legacy preserved for tests.
"""

from __future__ import annotations

from src.modules.copilot.application.memory.context_window_builder import (
    ContextWindowBuilder,
)
from src.modules.copilot.application.memory.rolling_summarizer import (
    RollingSummarizer,
)
from src.modules.copilot.domain.context_window import (
    DEFAULT_CONTEXT_WINDOW_CONFIG,
    TELEGRAM_CONTEXT_WINDOW_CONFIG,
)


# ── ContextWindowBuilder.for_channel ────────────────────────────────────


def test_builder_for_telegram_uses_telegram_config() -> None:
    builder = ContextWindowBuilder.for_channel("telegram")
    # Internal field is ``_cfg`` per current class signature
    assert builder._cfg is TELEGRAM_CONTEXT_WINDOW_CONFIG


def test_builder_for_web_uses_default_config() -> None:
    builder = ContextWindowBuilder.for_channel("web")
    assert builder._cfg is DEFAULT_CONTEXT_WINDOW_CONFIG


def test_builder_for_none_uses_default_config() -> None:
    """Backward compat — None resolves to default 'web'."""
    builder = ContextWindowBuilder.for_channel(None)
    assert builder._cfg is DEFAULT_CONTEXT_WINDOW_CONFIG


def test_builder_legacy_init_still_works() -> None:
    """Existing ``__init__(config=...)`` path stays available for tests / wired callers."""
    builder = ContextWindowBuilder(DEFAULT_CONTEXT_WINDOW_CONFIG)
    assert builder._cfg is DEFAULT_CONTEXT_WINDOW_CONFIG


# ── RollingSummarizer.for_channel ───────────────────────────────────────


def test_summarizer_for_telegram_uses_telegram_max_chars() -> None:
    summarizer = RollingSummarizer.for_channel("telegram")
    # Telegram config sets SUMMARY_MAX_CHARS=600.
    assert summarizer._max_chars == TELEGRAM_CONTEXT_WINDOW_CONFIG.SUMMARY_MAX_CHARS
    assert summarizer._max_chars == 600


def test_summarizer_for_web_uses_default_max_chars() -> None:
    summarizer = RollingSummarizer.for_channel("web")
    assert summarizer._max_chars == DEFAULT_CONTEXT_WINDOW_CONFIG.SUMMARY_MAX_CHARS
    assert summarizer._max_chars == 400


def test_summarizer_for_none_uses_default_max_chars() -> None:
    summarizer = RollingSummarizer.for_channel(None)
    assert summarizer._max_chars == DEFAULT_CONTEXT_WINDOW_CONFIG.SUMMARY_MAX_CHARS


def test_summarizer_legacy_init_still_works() -> None:
    """``__init__(llm=None, max_chars=400)`` path preserved for tests / wired callers."""
    summarizer = RollingSummarizer(llm=None, max_chars=250)
    assert summarizer._max_chars == 250
    assert summarizer._llm is None


def test_summarizer_for_channel_accepts_explicit_llm() -> None:
    """``for_channel`` accepts an injected llm (test ergonomics)."""
    sentinel = object()
    summarizer = RollingSummarizer.for_channel("telegram", llm=sentinel)  # type: ignore[arg-type]
    assert summarizer._llm is sentinel
    assert summarizer._max_chars == 600
