"""Turn-scoped trace recorder.

Design goals (drawn from LangSmith / OpenTelemetry best practice):

* **One row per significant event**, never per SSE chunk — the schema stays
  queryable; ``data`` is a JSONB bag for event-type specific payload.
* **Span tree**: each event has a ``span_id``; child events reference the
  parent via ``parent_span_id`` so LLM → tool → LLM chains reconstruct.
* **Duration on end**: ``*_start`` pairs with ``*_end`` to compute
  ``duration_ms`` without polluting the streaming path with timers on every
  yield.
* **Best-effort writes**: a write failure logs a warning and returns; the
  copilot turn never errors because of observability. Writes use their own
  short-lived ``SessionLocal`` so the orchestrator's async session stays
  clean.
* **Payload capping**: raw prompts/outputs are truncated to
  ``MAX_PAYLOAD_CHARS`` to protect Postgres + avoid leaking huge secrets.

Event-type catalog (see migration 059 for storage, admin panel for UI):

* ``turn_start`` / ``turn_end``  — one pair per /copilot/chat request.
* ``llm_call``  — one row per model invocation (agent node + post-tool).
* ``tool_call`` — one row per LangChain tool execution.
* ``card_emitted`` — one row per CardBlock added to the stream.
* ``node_enter`` / ``node_exit`` — LangGraph node transitions (optional).
* ``error`` — explicit failure, with exception class + message.

Consumers: the chat orchestrator, ``agent_node``, ``tool_executor_node`` and
``_handle_tool_end_v2`` call the recorder. The ``with_span`` context manager
auto-handles success/error + duration.
"""

from __future__ import annotations

import contextlib
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from collections.abc import Iterator

import structlog

from src.core.database import SessionLocal
from src.modules.copilot.infrastructure.models.trace_event_model import (
    CopilotTraceEventModel,
)

logger = structlog.get_logger()

# Max string length we keep for a single field inside the event's ``data``
# JSONB. Prompts or tool outputs bigger than this are truncated with a
# ``[truncated]`` suffix — we still see the head which is usually enough to
# diagnose a problem, without making ``copilot_trace_event`` blow up.
MAX_PAYLOAD_CHARS: int = 4_000


def _truncate(value: Any, limit: int = MAX_PAYLOAD_CHARS) -> Any:  # noqa: ANN401 — value is polymorphic
    """Return ``value`` trimmed to ``limit`` chars if it's a long string."""
    if isinstance(value, str) and len(value) > limit:
        return value[:limit] + " [truncated]"
    return value


def _sanitize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Shallow-trim every string value so JSONB stays predictable."""
    if not payload:
        return {}
    return {k: _truncate(v) for k, v in payload.items()}


@dataclass
class TraceRecorder:
    """Turn-scoped recorder. One instance per /copilot/chat request.

    Build with :meth:`start` once the tenant/user/conversation ids are
    known. Every call writes immediately — keep payloads small.
    """

    tenant_id: UUID
    user_id: UUID | None = None
    conversation_id: UUID | None = None
    message_id: UUID | None = None
    turn_id: UUID = field(default_factory=uuid4)

    def record(
        self,
        *,
        event_type: str,
        name: str | None = None,
        data: dict[str, Any] | None = None,
        duration_ms: int | None = None,
        status: str = "ok",
        parent_span_id: UUID | None = None,
        span_id: UUID | None = None,
    ) -> UUID:
        """Persist one event row. Returns its ``span_id``.

        The caller passes ``span_id`` only when it needs the same id used in
        a prior ``_start`` event (to pair durations). Most callers let the
        recorder allocate a fresh id.
        """
        sid = span_id or uuid4()
        # Wrap EVERYTHING — model instantiation, SessionLocal, add, commit —
        # because SQLAlchemy mapper configuration can raise the first time a
        # new model is touched (cross-module relationships resolving at the
        # wrong moment), and we absolutely must not surface that to the
        # orchestrator. Observability is best-effort.
        db = None
        try:
            row = CopilotTraceEventModel(
                id=uuid4(),
                tenant_id=self.tenant_id,
                user_id=self.user_id,
                conversation_id=self.conversation_id,
                message_id=self.message_id,
                turn_id=self.turn_id,
                span_id=sid,
                parent_span_id=parent_span_id,
                event_type=event_type,
                name=name,
                data=_sanitize_payload(data or {}),
                duration_ms=duration_ms,
                status=status,
            )
            db = SessionLocal()
            db.add(row)
            db.commit()
        except Exception as exc:  # noqa: BLE001 — observability is best-effort
            if db is not None:
                with contextlib.suppress(Exception):
                    db.rollback()
            logger.warning(
                "trace_event_write_failed",
                event_type=event_type,
                name=name,
                turn_id=str(self.turn_id),
                error=str(exc),
            )
        finally:
            if db is not None:
                with contextlib.suppress(Exception):
                    db.close()
        return sid

    @contextmanager
    def span(
        self,
        *,
        event_type: str,
        name: str | None = None,
        data: dict[str, Any] | None = None,
        parent_span_id: UUID | None = None,
    ) -> Iterator[UUID]:
        """Context manager that wraps a block in a span.

        On success records ``event_type`` with ``status="ok"`` and the
        elapsed duration. On exception records the same span with
        ``status="error"`` and merges ``error_type``/``error_message`` into
        ``data`` before re-raising.
        """
        start = time.monotonic()
        span_id = uuid4()
        merged: dict[str, Any] = dict(data or {})
        try:
            yield span_id
        except Exception as exc:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            self.record(
                event_type=event_type,
                name=name,
                data={
                    **merged,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc)[:MAX_PAYLOAD_CHARS],
                },
                duration_ms=elapsed_ms,
                status="error",
                parent_span_id=parent_span_id,
                span_id=span_id,
            )
            raise
        else:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            self.record(
                event_type=event_type,
                name=name,
                data=merged,
                duration_ms=elapsed_ms,
                status="ok",
                parent_span_id=parent_span_id,
                span_id=span_id,
            )


class _NoopRecorder:
    """Fallback when observability is disabled or the DB isn't reachable."""

    def record(self, **_: Any) -> UUID:  # noqa: ANN401 — pass-through sig
        return uuid4()

    @contextmanager
    def span(self, **_: Any) -> Iterator[UUID]:  # noqa: ANN401 — pass-through sig
        yield uuid4()


def start(
    *,
    tenant_id: UUID | None,
    user_id: UUID | None = None,
    conversation_id: UUID | None = None,
    message_id: UUID | None = None,
) -> TraceRecorder | _NoopRecorder:
    """Return a turn-scoped recorder, or a noop when tenant_id is missing.

    Callers invoke ``start`` once per turn and pass the recorder down to
    every node/tool that needs to append events.
    """
    if tenant_id is None:
        return _NoopRecorder()
    return TraceRecorder(
        tenant_id=tenant_id,
        user_id=user_id,
        conversation_id=conversation_id,
        message_id=message_id,
    )


__all__ = [
    "MAX_PAYLOAD_CHARS",
    "TraceRecorder",
    "start",
]
