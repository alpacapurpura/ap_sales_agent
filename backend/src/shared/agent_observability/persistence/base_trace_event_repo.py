"""Abstract repo Protocol for ``*_trace_event`` writers.

Mirror of :mod:`base_llm_call_repo` for the trace-event table family.
Each agent has its own concrete:

* Copilot: ``TraceEventRepository`` over ``copilot_trace_event``.
* Sales agent (S1): ``SalesAgentTraceEventRepository`` over
  ``sales_agent_trace_event``.

Structural typing via ``Protocol`` so sync/async sessions both qualify.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from uuid import UUID


@runtime_checkable
class BaseTraceEventRepoProtocol(Protocol):
    """Minimum write interface for ``*_trace_event`` repos."""

    def add(
        self,
        *,
        tenant_id: UUID,
        turn_id: UUID,
        span_id: UUID,
        event_type: str,
        name: str | None = None,
        data: dict[str, Any] | None = None,
        duration_ms: int | None = None,
        status: str = "ok",
        **agent_specific: Any,  # noqa: ANN401 — sales_agent injects lead_id/channel_type
    ) -> Any:  # noqa: ANN401 — concrete row type varies per agent table
        """Insert one trace-event row. Caller controls flush/commit."""
        ...


__all__ = ["BaseTraceEventRepoProtocol"]
