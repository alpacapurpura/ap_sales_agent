"""Shared base envelope — single lifecycle definition for every agent.

Anti-duplication LIFT (PR-2 PI-1.1, 2026-05-01): the lifecycle that used
to live monolithically in ``copilot/observability/recording/turn_envelope.py``
is now an abstract base here. Concrete subclasses implement three
abstract hooks and inherit the rest:

* :meth:`_add_trace_event` — agent-specific trace event row insert
  (copilot uses ``conversation_id`` + ``user_id`` kwargs; sales_agent
  uses ``lead_id`` + ``channel_type``).
* :meth:`_aggregate_totals` — sums the agent-specific ``*_llm_call``
  rows for the turn.
* :meth:`_legacy_compat_keys_or_empty` — copilot returns the JSONB
  legacy shape Streamlit consumes; sales_agent returns ``{}``.

Locked methods (``observe_turn``, ``_write_turn_*``, ``set_turn_*``,
``langchain_config``, ``_commit_session``) live concretely on the base
— subclasses MUST NOT override them. Enforced by an arch test that
parses the AST of every concrete subclass.

Best-effort: every persistence path is wrapped in ``try/except`` so an
observability failure never bubbles out of the orchestrator. The
``observe_turn`` body uses ``try / except BaseException / finally`` so a
client disconnect (``asyncio.CancelledError``) still lands a
``turn_end`` row — without this, dropped SSEs leak open turns.
"""

from __future__ import annotations

import contextlib
import time
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

import structlog

from src.shared.agent_observability.recording.sanitization import sanitize_payload, truncate

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

logger = structlog.get_logger()


@dataclass
class _TurnSummary:
    """Stream-shape totals supplied by the orchestrator before turn close.

    Mirrors copilot's pre-refactor shape verbatim. Sales_agent will leave
    these zeroed (no Streamlit consumer); copilot keeps the projection
    via ``_legacy_compat_keys_or_empty``.
    """

    response_length: int = 0
    message_count: int = 0
    block_count: int = 0


@dataclass
class _TurnErrorFlag:
    """Out-of-band error flag set by the orchestrator.

    The orchestrator catches stream errors (TimeoutError,
    ToolCallLoopDetected, generic Exception) so it can emit a
    user-facing SSE error and persist partial state. Those catches
    used to leave the turn marked ``status='ok'`` — observability
    lied (2026-04-27 incident). Calling ``set_turn_error`` from the
    except block ensures ``turn_end`` records the truth.
    """

    error_kind: str
    error_message: str | None = None


def _empty_totals() -> dict[str, Any]:
    """Default zeros for an aggregation that failed best-effort."""
    return {
        "llm_call_count": 0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_cached_read_tokens": 0,
        "total_cost_usd": "0",
        "model_responded": "",
    }


@dataclass
class BaseObservabilityContext(ABC):
    """Abstract base — owns the full per-turn lifecycle.

    Concrete subclasses implement three abstract hooks. Subclasses MUST
    NOT redefine the locked methods (``observe_turn``, ``_write_turn_*``,
    ``set_turn_*``, ``langchain_config``, ``_commit_session``).
    """

    tenant_id: UUID
    turn_id: UUID
    callback_handler: Any  # ``BaseAgentCallbackHandler`` (concrete varies per agent)
    trace_repo: Any  # protocol — has ``.db`` + ``.add(...)``
    llm_call_repo: Any  # protocol — has ``.db``
    _summary: _TurnSummary = field(default_factory=_TurnSummary)
    _turn_start_monotonic: float = field(default_factory=time.monotonic)
    _error_flag: _TurnErrorFlag | None = None

    # ── Concrete locked methods — DO NOT override in subclasses ────────

    def langchain_config(self) -> dict[str, Any]:
        """Return a ``RunnableConfig``-shaped dict with the callback wired in."""
        return {"callbacks": [self.callback_handler]}

    def set_turn_summary(
        self,
        *,
        response_length: int,
        message_count: int,
        block_count: int,
    ) -> None:
        """Stash the stream-shape totals so ``turn_end`` can include them.

        Called by the orchestrator right before the ``observe_turn``
        context manager exits.
        """
        self._summary = _TurnSummary(
            response_length=int(response_length),
            message_count=int(message_count),
            block_count=int(block_count),
        )

    def set_turn_error(
        self,
        *,
        error_kind: str,
        error_message: str | None = None,
    ) -> None:
        """Flag the current turn as errored without raising.

        See :class:`_TurnErrorFlag` docstring for the rationale (2026-04-27
        incident — orchestrator caught exception, body returned clean,
        turn_end said ``ok``).
        """
        self._error_flag = _TurnErrorFlag(
            error_kind=error_kind,
            error_message=error_message,
        )

    @asynccontextmanager
    async def observe_turn(
        self,
        *,
        message: str,
        route: str,
        attachments: list[Any] | None = None,
    ) -> AsyncIterator[BaseObservabilityContext]:
        """Bracket the turn — write turn_start on enter, turn_end on exit.

        The body MUST run the orchestrator graph with
        ``config=self.langchain_config()`` so the callback handler sees
        every LLM/tool/chain event. ``turn_end`` aggregates counts via
        :meth:`_aggregate_totals` and folds in legacy keys via
        :meth:`_legacy_compat_keys_or_empty`.
        """
        self._write_turn_start(message=message, route=route, attachments=attachments or [])
        error_for_end: BaseException | None = None
        try:
            yield self
        except BaseException as exc:  # we MUST land turn_end even on CancelledError when FE drops the SSE
            error_for_end = exc
            raise
        finally:
            # ``finally`` so a client disconnect (asyncio.CancelledError —
            # BaseException, not Exception) still leaves a turn_end row.
            # Without this, dropped SSEs leak open turns.
            self._write_turn_end(error=error_for_end if isinstance(error_for_end, Exception) else None)

    # ── Internal locked helpers ────────────────────────────────────────

    def _write_turn_start(
        self,
        *,
        message: str,
        route: str,
        attachments: list[Any],
    ) -> None:
        try:
            self._add_trace_event(
                event_type="turn_start",
                name=route,
                data=sanitize_payload(
                    {
                        "message_preview": truncate(message),
                        "route": route,
                        "attachments": len(attachments),
                    },
                ),
                status="ok",
                span_id=self.turn_id,
            )
            self._commit_session()
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning("obs_turn_start_failed", error=str(exc))

    def _write_turn_end(self, *, error: BaseException | None) -> None:
        duration_ms = max(int((time.monotonic() - self._turn_start_monotonic) * 1000), 0)
        try:
            totals = self._safe_aggregate_totals()
            data: dict[str, Any] = {
                "ended_at": datetime.now(tz=UTC).isoformat(),
                **totals,
                **self._safe_legacy_compat_keys(totals),
            }
            if error is not None:
                data["error_type"] = type(error).__name__
                data["error_message"] = truncate(str(error))
            # Out-of-band error flag wins over a clean exit: the
            # orchestrator caught the exception itself so the body
            # returned normally, but the turn was still a failure.
            if self._error_flag is not None:
                data["error_kind"] = self._error_flag.error_kind
                if self._error_flag.error_message is not None:
                    data["error_message"] = truncate(self._error_flag.error_message)
            is_error = error is not None or self._error_flag is not None
            self._add_trace_event(
                event_type="turn_end",
                name="turn_end",
                data=sanitize_payload(data),
                duration_ms=duration_ms,
                status="error" if is_error else "ok",
                span_id=uuid4(),
            )
            self._commit_session()
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning("obs_turn_end_failed", error=str(exc))

    def _commit_session(self) -> None:
        """Commit the trace_repo session.

        ``observe_turn`` writes turn_start at the very start of the turn
        and turn_end at the very end — there's no other orchestrator
        commit covering them, so the rows would be discarded when the
        FastAPI request session closes. Best-effort: a failed commit is
        swallowed but never propagated.
        """
        session = getattr(self.trace_repo, "db", None)
        if session is None:
            return
        with contextlib.suppress(Exception):
            session.commit()

    def _safe_aggregate_totals(self) -> dict[str, Any]:
        """Wrap subclass aggregator with best-effort fallback."""
        try:
            return self._aggregate_totals()
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning("obs_aggregate_totals_failed", error=str(exc))
            return _empty_totals()

    def _safe_legacy_compat_keys(self, totals: dict[str, Any]) -> dict[str, Any]:
        try:
            return self._legacy_compat_keys_or_empty(totals)
        except Exception as exc:  # noqa: BLE001 — best-effort
            logger.warning("obs_legacy_compat_keys_failed", error=str(exc))
            return {}

    # ── Abstract hooks — concrete subclass MUST implement ──────────────

    @abstractmethod
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
        """Persist one row to the agent-specific trace event table.

        Concrete impls call ``self.trace_repo.add(...)`` with the
        agent-specific kwargs (e.g. ``conversation_id`` + ``user_id``
        for copilot, ``lead_id`` + ``channel_type`` for sales_agent).

        Best-effort: subclasses SHOULD wrap their ``trace_repo.add``
        call in ``try/except`` + ``logger.warning``. The base
        ``_write_turn_*`` already wraps the outer call so a raise here
        will not bubble out of ``observe_turn``.
        """

    @abstractmethod
    def _aggregate_totals(self) -> dict[str, Any]:
        """Sum the agent-specific ``*_llm_call`` rows for this turn.

        Returns dict with keys ``llm_call_count``, ``total_input_tokens``,
        ``total_output_tokens``, ``total_cached_read_tokens``,
        ``total_cost_usd`` (str), ``model_responded`` (str). Used by base
        ``_write_turn_end`` to populate the ``turn_end.data`` JSONB.

        Best-effort: return :func:`_empty_totals` on failure.
        """

    @abstractmethod
    def _legacy_compat_keys_or_empty(self, totals: dict[str, Any]) -> dict[str, Any]:
        """Return legacy JSONB keys for back-compat consumers.

        Copilot impl: returns full ``_legacy_compat_keys`` dict (model,
        prompt_tokens, completion_tokens, cache_hit_rate, response_length,
        ...). Required because Streamlit ``/trazas`` + ``/copilot-routing``
        still read JSONB.

        Sales_agent impl: returns ``{}`` — no legacy consumers.
        """


__all__ = [
    "BaseObservabilityContext",
    "_TurnErrorFlag",
    "_TurnSummary",
    "_empty_totals",
]
