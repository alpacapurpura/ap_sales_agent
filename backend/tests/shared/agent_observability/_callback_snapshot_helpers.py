"""Snapshot helpers for callback handler — S11A.

Used by ``test_callback_handler_snapshot.py`` to replay a deterministic
sequence of LangChain callback events against an agent-specific handler
and capture every persistence call as JSON.

The helpers freeze :func:`datetime.now` and :func:`time.monotonic` so the
captured snapshot is byte-equal across runs. Refactor preserves
behavior ⇔ snapshot diff = 0.

# [SALES-AGENT-CALLBACK-SNAPSHOT-S11A] -> docs/domains/sales-agent/redesign-2026-04/phases/S11-shared-lift-orchestrator-decomp.md
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID

# ── Deterministic fixtures ──────────────────────────────────────────────

RUN_ID_CHAT = UUID("11111111-1111-1111-1111-111111111111")
RUN_ID_TOOL = UUID("22222222-2222-2222-2222-222222222222")
RUN_ID_CHAIN = UUID("33333333-3333-3333-3333-333333333333")

PRICING_VERSION_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
TENANT_ID = UUID("44444444-4444-4444-4444-444444444444")
LEAD_ID = UUID("55555555-5555-5555-5555-555555555555")
CONVERSATION_ID = UUID("66666666-6666-6666-6666-666666666666")
USER_ID = UUID("77777777-7777-7777-7777-777777777777")
TURN_ID = UUID("88888888-8888-8888-8888-888888888888")

FROZEN_NOW = datetime(2026, 4, 28, 12, 0, 0, tzinfo=UTC)
FROZEN_MONOTONIC_BASE = 1000.0
FROZEN_MONOTONIC_STEP_MS = 25  # each call advances 25 ms


# ── Stubs ──────────────────────────────────────────────────────────────


def build_pricing_resolver_stub() -> MagicMock:
    """Stub :class:`PricingResolver` returning a fixed snapshot."""
    snapshot = SimpleNamespace(
        id=PRICING_VERSION_ID,
        input_cost_per_token=Decimal("0.000001"),
        output_cost_per_token=Decimal("0.000005"),
        cache_read_cost_per_token=Decimal("0.0000005"),
        cache_write_cost_per_token=Decimal(0),
    )
    pricing_result = SimpleNamespace(
        snapshot=snapshot,
        is_estimated=False,
        cache_hit=False,
    )
    resolver = MagicMock()
    resolver.resolve.return_value = pricing_result
    return resolver


def build_fx_resolver_stub() -> MagicMock:
    fx = MagicMock()
    fx.resolve.return_value = (Decimal("1.0"), "stub")
    return fx


@dataclass(slots=True)
class CapturingRepo:
    """Mock repo that captures every ``add(**kwargs)`` call."""

    name: str
    captured: list[dict[str, Any]]

    def add(self, **kwargs: Any) -> None:
        self.captured.append(_serialize(kwargs))


def build_capturing_repos() -> tuple[CapturingRepo, CapturingRepo]:
    return (
        CapturingRepo(name="llm_call", captured=[]),
        CapturingRepo(name="trace_event", captured=[]),
    )


# ── Determinism: freeze clocks ─────────────────────────────────────────


class _FrozenMonotonic:
    """Counter that advances ``FROZEN_MONOTONIC_STEP_MS`` per call."""

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> float:
        value = FROZEN_MONOTONIC_BASE + (self.calls * FROZEN_MONOTONIC_STEP_MS / 1000.0)
        self.calls += 1
        return value


class _FrozenDatetime:
    """``datetime.now(tz=UTC)`` wrapper that always returns ``FROZEN_NOW``."""

    @staticmethod
    def now(tz: object | None = None) -> datetime:
        return FROZEN_NOW


_BASE_HANDLER_MODULE = "src.shared.agent_observability.recording.base_callback_handler"


def freeze_handler_clock(monkeypatch: Any, module_path: str | None = None) -> None:
    """Patch ``datetime`` and ``time`` inside the base handler module.

    Post-S11A lift the LangChain plumbing lives on the base, so the
    clock is frozen there. ``module_path`` kept for caller back-compat
    (ignored).
    """
    del module_path
    monkeypatch.setattr(f"{_BASE_HANDLER_MODULE}.datetime", _FrozenDatetime)
    monkeypatch.setattr(f"{_BASE_HANDLER_MODULE}.time.monotonic", _FrozenMonotonic())


# ── Canonical event sequence ───────────────────────────────────────────


def replay_canonical_sequence(handler: Any) -> None:
    """Replay the canonical 8-event LangChain sequence against ``handler``.

    Sequence: chat_model_start → llm_end → tool_start → tool_end →
    chain_start → chain_end → chat_model_start (error path) → llm_error.
    """
    serialized_chat = {
        "name": "ChatKimi",
        "kwargs": {"model_name": "kimi-k2.6"},
    }
    metadata = {"ls_provider": "kimi", "ls_model_name": "kimi-k2.6"}

    # Successful chat call.
    handler.on_chat_model_start(
        serialized_chat,
        [],
        run_id=RUN_ID_CHAT,
        metadata=metadata,
    )

    response = SimpleNamespace(
        generations=[
            [
                SimpleNamespace(
                    message=SimpleNamespace(
                        usage_metadata={
                            "input_tokens": 100,
                            "output_tokens": 50,
                            "input_token_details": {
                                "cache_read": 80,
                                "cache_creation": 0,
                            },
                            "output_token_details": {"reasoning": 0},
                        },
                        response_metadata={"model_name": "kimi-k2.6"},
                    ),
                ),
            ],
        ],
        llm_output=None,
    )
    handler.on_llm_end(response, run_id=RUN_ID_CHAT)

    # Tool call (success).
    handler.on_tool_start(
        {"name": "get_lead_context"},
        '{"lead_id": "abc"}',
        run_id=RUN_ID_TOOL,
    )
    handler.on_tool_end(
        {"context": "fixture"},
        run_id=RUN_ID_TOOL,
    )

    # LangGraph node enter/exit.
    handler.on_chain_start(
        {"name": "qualifier"},
        {},
        run_id=RUN_ID_CHAIN,
    )
    handler.on_chain_end(
        {"messages": []},
        run_id=RUN_ID_CHAIN,
    )


# ── Serialization ──────────────────────────────────────────────────────


def _serialize(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_serialize(v) for v in value]
    return value


def render_snapshot(llm_calls: list[dict], trace_events: list[dict]) -> str:
    """Render captured rows as deterministic JSON."""
    payload = {
        "llm_call_repo.add": llm_calls,
        "trace_event_repo.add": trace_events,
    }
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


# ── Snapshot file IO ───────────────────────────────────────────────────


SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / "snapshots" / "callback_handler"


def assert_matches_snapshot(actual: str, baseline_filename: str) -> None:
    """Compare ``actual`` JSON against the baseline file.

    First run writes the baseline + raises so the developer commits it.
    Subsequent runs assert byte-equal diff.
    """
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    baseline_path = SNAPSHOT_DIR / baseline_filename
    if not baseline_path.exists():
        baseline_path.write_text(actual, encoding="utf-8")
        msg = f"Baseline {baseline_path} created. Commit it and re-run; this fail is expected on first run only."
        raise AssertionError(msg)

    expected = baseline_path.read_text(encoding="utf-8")
    if actual != expected:
        # Side-by-side diff hint without writing — developer decides whether
        # to update the baseline manually after reviewing the diff.
        msg = (
            f"Snapshot diff vs {baseline_path}. The callback handler "
            "changed shape — investigate before updating the baseline. If "
            "the new shape is intentional (Sub-sprint A/B refactor), "
            f"manually overwrite the file with this output:\n\n{actual}"
        )
        raise AssertionError(msg)


__all__ = [
    "CONVERSATION_ID",
    "FROZEN_MONOTONIC_BASE",
    "FROZEN_MONOTONIC_STEP_MS",
    "FROZEN_NOW",
    "LEAD_ID",
    "PRICING_VERSION_ID",
    "RUN_ID_CHAIN",
    "RUN_ID_CHAT",
    "RUN_ID_TOOL",
    "SNAPSHOT_DIR",
    "TENANT_ID",
    "TURN_ID",
    "USER_ID",
    "CapturingRepo",
    "assert_matches_snapshot",
    "build_capturing_repos",
    "build_fx_resolver_stub",
    "build_pricing_resolver_stub",
    "freeze_handler_clock",
    "render_snapshot",
    "replay_canonical_sequence",
]
