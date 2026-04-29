"""Typing-simulation CPM wiring tests (S12).

Wires ``ChannelFormat.typing_simulation_cpm`` into
``OutputManager._calculate_typing_time``: when the registry declares a
custom CPM for the channel, the typing latency scales accordingly. When
``typing_simulation_cpm`` is ``None`` (the case for all seven S5
baseline channels), the calculator falls back to the global
``CPM_SPEED`` constant — preserving §3 protected behavior.

# [SALES-AGENT-CHANNEL-REGISTRY-S5] -> docs/domains/sales-agent/redesign-2026-04/phases/S5-channel-registry.md
# [SALES-AGENT-TYPING-CPM-S12] -> docs/domains/sales-agent/redesign-2026-04/phases/S12-final-hardening-zero-debt.md
"""

from __future__ import annotations

import random

import pytest

from src.modules.sales_agent.infrastructure.external.output_manager import (
    OutputManager,
)
from src.shared.agent_observability.channels.format import (
    ChannelFormat,
    register_channel,
    reset_registry_for_tests,
)


@pytest.fixture(autouse=True)
def _reset_registry() -> None:
    reset_registry_for_tests()
    yield
    reset_registry_for_tests()


@pytest.fixture(autouse=True)
def _freeze_jitter(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin random.uniform → 1.0 so jitter is deterministic for math asserts."""
    real_uniform = random.uniform

    def _fake_uniform(a: float, b: float) -> float:
        # JITTER_RANGE typically (0.85, 1.15). Force midpoint stable = 1.0
        # for predictable arithmetic. Other ranges (MICRO_DELAY) keep real
        # behavior — they only fire between chunks, not in typing calc.
        if a <= 1.0 <= b:
            return 1.0
        return real_uniform(a, b)

    monkeypatch.setattr(random, "uniform", _fake_uniform)


class TestTypingCpmFallback:
    def test_no_channel_uses_cpm_speed(self) -> None:
        # 600 chars / CPM_SPEED * 60 = baseline. No channel → no override.
        text = "x" * 600
        baseline = OutputManager._calculate_typing_time(text)
        manual = (len(text) / OutputManager.CPM_SPEED) * 60
        # Clamped to MAX_TYPING_TIME if manual exceeds it.
        expected = max(
            OutputManager.MIN_TYPING_TIME,
            min(manual, OutputManager.MAX_TYPING_TIME),
        )
        assert baseline == pytest.approx(expected, abs=0.01)

    def test_baseline_channel_with_none_cpm_falls_back(self) -> None:
        # All 7 S5 baseline channels declare typing_simulation_cpm=None →
        # falls back to global CPM_SPEED. Each call yields the same time
        # as the no-channel call.
        text = "x" * 400
        without = OutputManager._calculate_typing_time(text)
        with_telegram = OutputManager._calculate_typing_time(text, channel_type="telegram")
        with_whatsapp = OutputManager._calculate_typing_time(text, channel_type="whatsapp")
        assert without == with_telegram == with_whatsapp


class TestTypingCpmOverride:
    def test_custom_channel_with_higher_cpm_types_faster(self) -> None:
        # CPM 4x larger → typing time ~4x shorter. 30 chars at CPM 320
        # = 5.625s (within MIN/MAX). At CPM 1280 = 1.40625s → clamps to
        # MIN_TYPING_TIME (1.5s). Either way fast < baseline.
        register_channel(
            ChannelFormat(
                id="ultra_fast",
                label_es="Ultra Fast",
                max_chars=4000,
                emoji_allowed=True,
                line_break_style="\n\n",
                markdown_allowed=True,
                structure_hint="test",
                typing_simulation_cpm=OutputManager.CPM_SPEED * 4,
            ),
        )
        text = "x" * 30
        baseline = OutputManager._calculate_typing_time(text)
        fast = OutputManager._calculate_typing_time(text, channel_type="ultra_fast")
        assert fast < baseline

    def test_custom_channel_with_lower_cpm_types_slower(self) -> None:
        # CPM / 4 → typing time ~4x longer. 30 chars at CPM 320 = 5.625s.
        # At CPM 80 = 22.5s → clamps to MAX_TYPING_TIME (6s). Slow ≥ baseline.
        register_channel(
            ChannelFormat(
                id="ultra_slow",
                label_es="Ultra Slow",
                max_chars=4000,
                emoji_allowed=True,
                line_break_style="\n\n",
                markdown_allowed=True,
                structure_hint="test",
                typing_simulation_cpm=max(1, OutputManager.CPM_SPEED // 4),
            ),
        )
        text = "x" * 30
        baseline = OutputManager._calculate_typing_time(text)
        slow = OutputManager._calculate_typing_time(text, channel_type="ultra_slow")
        assert slow >= baseline

    def test_zero_or_negative_cpm_falls_back_to_cpm_speed(self) -> None:
        # Defensive: a 0 or negative value in the registry must not
        # divide-by-zero. We treat it like None (fallback).
        register_channel(
            ChannelFormat(
                id="bad_cpm",
                label_es="Bad CPM",
                max_chars=4000,
                emoji_allowed=True,
                line_break_style="\n\n",
                markdown_allowed=True,
                structure_hint="test",
                typing_simulation_cpm=0,
            ),
        )
        text = "x" * 400
        bad = OutputManager._calculate_typing_time(text, channel_type="bad_cpm")
        baseline = OutputManager._calculate_typing_time(text)
        assert bad == baseline
