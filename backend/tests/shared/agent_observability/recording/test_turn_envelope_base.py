"""Contract tests for :class:`BaseObservabilityContext` (PR-2 PI-1.1).

Anti-duplication LIFT: the lifecycle that used to live monolithically
in ``copilot/observability/recording/turn_envelope.py`` is now an
abstract base in ``shared/agent_observability/recording/turn_envelope.py``.
Concrete subclasses (copilot, sales_agent, future agents) implement
three abstract hooks:

* ``_add_trace_event`` — persists one row to the agent-specific trace
  event table (signatures vary: copilot uses ``conversation_id`` +
  ``user_id``; sales_agent uses ``lead_id`` + ``channel_type``).
* ``_aggregate_totals`` — sums the agent-specific ``*_llm_call`` rows
  for the turn.
* ``_legacy_compat_keys_or_empty`` — copilot returns the JSONB legacy
  shape that Streamlit consumes; sales_agent returns ``{}``.

Locked methods (``observe_turn``, ``_write_turn_*``, ``set_turn_*``,
``langchain_config``, ``_commit_session``) live concretely on the base
— subclasses MUST NOT override them. Enforced by an arch test that
parses the AST of every concrete subclass.

Best-effort: every persistence path is wrapped so an observability
failure never bubbles out of the orchestrator.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest


@dataclass
class _StubTraceRepo:
    """Records every ``add()`` kwargs dict for assertion."""

    calls: list[dict[str, Any]] = field(default_factory=list)
    raise_on_add: bool = False
    db: Any = None  # session-like; ``_commit_session`` reads ``getattr(.., 'db')``

    def add(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if self.raise_on_add:
            msg = "boom"
            raise RuntimeError(msg)
        return MagicMock()


@dataclass
class _StubLlmCallRepo:
    """Empty stub; ``_aggregate_totals`` is overridden in our concrete subclass."""

    db: Any = None


def _build_minimal_concrete():
    """Build a minimal concrete subclass that satisfies the 3 abstracts.

    Returns the class — instantiate per-test with ``klass.start(...)``
    so each test gets a fresh ``_TurnSummary`` + ``_turn_start_monotonic``.
    """
    from src.shared.agent_observability.recording.turn_envelope import (
        BaseObservabilityContext,
    )

    class _MinimalContext(BaseObservabilityContext):
        # Concrete subclass must own its concrete fields. We don't add any
        # to keep the surface minimal — copilot adds conversation_id/user_id,
        # sales_agent adds lead_id/channel_type.

        def _add_trace_event(
            self,
            *,
            event_type: str,
            name: str,
            data: dict[str, Any],
            duration_ms: int | None = None,
            status: str = "ok",
            span_id: UUID | None = None,
        ) -> None:
            with contextlib.suppress(Exception):
                self.trace_repo.add(
                    tenant_id=self.tenant_id,
                    turn_id=self.turn_id,
                    span_id=span_id or uuid4(),
                    event_type=event_type,
                    name=name,
                    data=data,
                    duration_ms=duration_ms,
                    status=status,
                )

        def _aggregate_totals(self) -> dict[str, Any]:
            return {
                "llm_call_count": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_cached_read_tokens": 0,
                "total_cost_usd": "0",
                "model_responded": "",
            }

        def _legacy_compat_keys_or_empty(self, totals: dict[str, Any]) -> dict[str, Any]:
            return {}

    return _MinimalContext


def _make_ctx(*, raise_on_add: bool = False):
    klass = _build_minimal_concrete()
    trace_repo = _StubTraceRepo(raise_on_add=raise_on_add)
    llm_call_repo = _StubLlmCallRepo()
    handler = MagicMock()  # not exercised by base lifecycle assertions
    return klass(
        tenant_id=uuid4(),
        turn_id=uuid4(),
        callback_handler=handler,
        trace_repo=trace_repo,
        llm_call_repo=llm_call_repo,
    ), trace_repo


class TestAbstractEnforcement:
    """Cannot instantiate :class:`BaseObservabilityContext` directly."""

    def test_abstract_class_cannot_be_instantiated(self) -> None:
        from src.shared.agent_observability.recording.turn_envelope import (
            BaseObservabilityContext,
        )

        with pytest.raises(TypeError):
            BaseObservabilityContext(  # type: ignore[abstract]
                tenant_id=uuid4(),
                turn_id=uuid4(),
                callback_handler=MagicMock(),
                trace_repo=MagicMock(),
                llm_call_repo=MagicMock(),
            )


class TestLifecycle:
    @pytest.mark.asyncio
    async def test_observe_turn_writes_turn_start_on_enter(self) -> None:
        ctx, trace_repo = _make_ctx()
        async with ctx.observe_turn(message="hola", route="test", attachments=[]):
            assert any(call["event_type"] == "turn_start" for call in trace_repo.calls), (
                "turn_start row not written on enter"
            )

    @pytest.mark.asyncio
    async def test_observe_turn_writes_turn_end_on_clean_exit(self) -> None:
        ctx, trace_repo = _make_ctx()
        async with ctx.observe_turn(message="hola", route="test", attachments=[]):
            pass

        end_calls = [c for c in trace_repo.calls if c["event_type"] == "turn_end"]
        assert len(end_calls) == 1
        assert end_calls[0]["status"] == "ok"

    @pytest.mark.asyncio
    async def test_observe_turn_writes_turn_end_status_error_on_exception(self) -> None:
        ctx, trace_repo = _make_ctx()
        with pytest.raises(RuntimeError):
            async with ctx.observe_turn(message="hola", route="test", attachments=[]):
                msg = "boom"
                raise RuntimeError(msg)

        end_calls = [c for c in trace_repo.calls if c["event_type"] == "turn_end"]
        assert len(end_calls) == 1
        assert end_calls[0]["status"] == "error"
        assert "RuntimeError" in end_calls[0]["data"].get("error_type", "")

    @pytest.mark.asyncio
    async def test_observe_turn_writes_turn_end_on_cancellation(self) -> None:
        """``asyncio.CancelledError`` from FE drop must still land turn_end."""
        import asyncio

        ctx, trace_repo = _make_ctx()
        with pytest.raises(asyncio.CancelledError):
            async with ctx.observe_turn(message="hola", route="test", attachments=[]):
                raise asyncio.CancelledError

        end_calls = [c for c in trace_repo.calls if c["event_type"] == "turn_end"]
        assert len(end_calls) == 1, "turn_end MUST land even on CancelledError"


class TestSetTurnError:
    @pytest.mark.asyncio
    async def test_set_turn_error_marks_status_when_body_clean(self) -> None:
        """Orchestrator catches stream error → body returns clean → turn_end MUST be error."""
        ctx, trace_repo = _make_ctx()
        async with ctx.observe_turn(message="hola", route="test", attachments=[]):
            ctx.set_turn_error(error_kind="graph_recursion", error_message="limit 25")

        end_calls = [c for c in trace_repo.calls if c["event_type"] == "turn_end"]
        assert end_calls[0]["status"] == "error"
        assert end_calls[0]["data"].get("error_kind") == "graph_recursion"
        assert "limit" in end_calls[0]["data"].get("error_message", "")


class TestBestEffortPersistence:
    @pytest.mark.asyncio
    async def test_trace_repo_raise_does_not_break_lifecycle(self) -> None:
        """``trace_repo.add`` raising must not propagate out of ``observe_turn``."""
        ctx, _trace_repo = _make_ctx(raise_on_add=True)
        # No exception should bubble out — best-effort.
        async with ctx.observe_turn(message="hola", route="test", attachments=[]):
            pass


class TestLangchainConfig:
    def test_langchain_config_returns_callbacks_dict(self) -> None:
        ctx, _ = _make_ctx()
        cfg = ctx.langchain_config()
        assert "callbacks" in cfg
        assert ctx.callback_handler in cfg["callbacks"]


class TestSetTurnSummary:
    def test_set_turn_summary_stashes_for_turn_end(self) -> None:
        ctx, _ = _make_ctx()
        ctx.set_turn_summary(response_length=42, message_count=3, block_count=2)
        assert ctx._summary.response_length == 42
        assert ctx._summary.message_count == 3
        assert ctx._summary.block_count == 2
