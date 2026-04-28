"""Abstract repo Protocol for ``*_llm_call`` writers.

Each agent declares a concrete repo over its own table:

* Copilot: ``CopilotLlmCallRepository`` over ``copilot_llm_call``.
* Sales agent (S1): ``SalesAgentLlmCallRepository`` over
  ``sales_agent_llm_call`` (mirror schema + ``lead_id`` + ``channel_type``).

This Protocol is documentary: it captures the minimum interface the
shared :class:`~src.shared.agent_observability.recording.base_callback_handler.BaseAgentCallbackHandler`
needs from every concrete repo. Each agent is free to expose richer
read methods (per-turn aggregation, error counts, etc.) on top.

PEP 544 Protocol rather than ABC because we want structural typing —
copilot's repo uses sync ``Session``, sales_agent (S1) may use async
``AsyncSession``; both satisfy the Protocol without inheritance.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class BaseLLMCallRepoProtocol(Protocol):
    """Minimum write interface for ``*_llm_call`` repos."""

    def add(self, **row: Any) -> Any:  # noqa: ANN401 — column kwargs vary per agent table
        """Insert one row. Caller controls flush/commit."""
        ...


__all__ = ["BaseLLMCallRepoProtocol"]
