"""Tests for :class:`BaseExtractionOrchestrator`.

Verifies the shared helpers that brand/offer (and future modules like
buyer_persona, landing) inherit: `_run_wave`, `_pause_between_waves`,
`_announce_sections`, and the wave-delay hook.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from pydantic import BaseModel

from src.shared.application.extraction.base_orchestrator import (
    BaseExtractionOrchestrator,
)


class _FakeTrace:
    """Minimal trace collector double — records calls."""

    def __init__(self) -> None:
        self.wave_starts: list[tuple[int, list[str]]] = []
        self.wave_pauses: list[tuple[int, float]] = []

    def wave_start(self, wave_num: int, sections: list[str]) -> None:
        self.wave_starts.append((wave_num, sections))

    def wave_pause(self, wave_num: int, delay: float) -> None:
        self.wave_pauses.append((wave_num, delay))


class _Section(BaseModel):
    name: str | None = None


class _RichCallback:
    """Callback that advertises rich kwargs so `_announce_sections` invokes it."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def __call__(
        self,
        pct: int,
        stage: str,
        *,
        new_fields: list[str] | None = None,
        section_completed: str | None = None,
    ) -> None:
        self.calls.append(
            {
                "pct": pct,
                "stage": stage,
                "new_fields": new_fields,
                "section_completed": section_completed,
            },
        )


class _LegacyCallback:
    """Callback with the 2-arg legacy signature."""

    def __init__(self) -> None:
        self.calls: list[tuple[int, str]] = []

    def __call__(self, pct: int, stage: str) -> None:
        self.calls.append((pct, stage))


class _DefaultOrch(BaseExtractionOrchestrator):
    """Concrete orchestrator using the default wave delay."""


class _CustomDelayOrch(BaseExtractionOrchestrator):
    """Concrete orchestrator overriding the wave delay hook."""

    def _get_wave_delay(self) -> float:
        return 0.25


@pytest.mark.asyncio()
async def test_run_wave_gathers_coros_and_logs_trace() -> None:
    orch = _DefaultOrch()
    trace = _FakeTrace()

    async def _coro(value: int) -> int:
        await asyncio.sleep(0)
        return value

    results = await orch._run_wave(
        wave_num=1,
        sections=["a", "b"],
        coros=[_coro(10), _coro(20)],
        trace=trace,
    )
    assert results == [10, 20]
    assert trace.wave_starts == [(1, ["a", "b"])]


@pytest.mark.asyncio()
async def test_run_wave_without_trace_is_safe() -> None:
    orch = _DefaultOrch()

    async def _coro() -> str:
        return "ok"

    results = await orch._run_wave(
        wave_num=2,
        sections=["only"],
        coros=[_coro()],
        trace=None,
    )
    assert results == ["ok"]


@pytest.mark.asyncio()
async def test_pause_between_waves_uses_default_delay() -> None:
    orch = _DefaultOrch()
    trace = _FakeTrace()

    # Patch asyncio.sleep to avoid real delays while still asserting the value
    sleeps: list[float] = []

    async def _fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    import src.shared.application.extraction.base_orchestrator as base_mod

    original = base_mod.asyncio.sleep
    base_mod.asyncio.sleep = _fake_sleep  # type: ignore[assignment]
    try:
        await orch._pause_between_waves(wave_num=1, trace=trace)
    finally:
        base_mod.asyncio.sleep = original  # type: ignore[assignment]

    assert sleeps == [BaseExtractionOrchestrator.default_wave_delay_seconds]
    assert trace.wave_pauses == [
        (1, BaseExtractionOrchestrator.default_wave_delay_seconds),
    ]


@pytest.mark.asyncio()
async def test_pause_between_waves_uses_subclass_hook() -> None:
    orch = _CustomDelayOrch()
    trace = _FakeTrace()

    sleeps: list[float] = []

    async def _fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    import src.shared.application.extraction.base_orchestrator as base_mod

    original = base_mod.asyncio.sleep
    base_mod.asyncio.sleep = _fake_sleep  # type: ignore[assignment]
    try:
        await orch._pause_between_waves(wave_num=2, trace=trace)
    finally:
        base_mod.asyncio.sleep = original  # type: ignore[assignment]

    assert sleeps == [0.25]
    assert trace.wave_pauses == [(2, 0.25)]


def test_announce_sections_skips_legacy_callbacks() -> None:
    orch = _DefaultOrch()
    cb = _LegacyCallback()

    orch._announce_sections(
        cb,
        sections=["a"],
        results=[_Section(name="x")],
        pct=50,
    )
    assert cb.calls == []


def test_announce_sections_emits_per_section_for_rich_callback() -> None:
    orch = _DefaultOrch()
    cb = _RichCallback()

    orch._announce_sections(
        cb,
        sections=["identity", "story"],
        results=[_Section(name="Acme"), _Section(name="Once upon a time")],
        pct=45,
    )

    assert len(cb.calls) == 2
    assert cb.calls[0]["section_completed"] == "identity"
    assert cb.calls[0]["pct"] == 45
    assert cb.calls[0]["new_fields"]  # non-empty list of filled paths
    assert cb.calls[1]["section_completed"] == "story"


def test_announce_sections_skips_empty_results() -> None:
    orch = _DefaultOrch()
    cb = _RichCallback()

    orch._announce_sections(
        cb,
        sections=["identity", "story"],
        results=[_Section(), _Section(name="filled")],
        pct=30,
    )

    # Only the filled section should emit.
    assert len(cb.calls) == 1
    assert cb.calls[0]["section_completed"] == "story"


def test_announce_sections_handles_none_callback() -> None:
    orch = _DefaultOrch()
    # Must not raise
    orch._announce_sections(
        None,
        sections=["identity"],
        results=[_Section(name="x")],
        pct=20,
    )
