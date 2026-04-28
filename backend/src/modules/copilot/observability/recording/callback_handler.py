"""LangChain callback handler for copilot — event-sourced ingress.

Subclass of :class:`~src.shared.agent_observability.recording.base_callback_handler.BaseAgentCallbackHandler`
(S11A retrofit). Wired into the orchestrator via
``RunnableConfig(callbacks=[handler])``.

What it captures (mapped to columns / event types):

* ``on_chat_model_start`` — opens a span (in-memory). Captures provider,
  model_requested, started_at, run_id.
* ``on_llm_end``           — closes the open chat span. Drains
  ``usage_metadata`` from ``response.generations[0][0].message`` (an
  :class:`~langchain_core.messages.AIMessage`), runs the cost calculator,
  resolves FX, persists one row in ``copilot_llm_call`` and a mirror
  row in ``copilot_trace_event`` (event_type='llm_call').
* ``on_llm_error``         — same close with status='error' + zero cost.
* ``on_tool_start`` / ``on_tool_end`` / ``on_tool_error`` — persist a
  ``tool_call`` trace event with duration_ms.
* ``on_chain_start`` / ``on_chain_end`` — node_enter/node_exit rows.

**Best-effort.** Any exception during persistence is swallowed and
logged via ``logger.warning`` — never propagated. Pattern mirrors
``application/observability/trace_recorder.py``.

Copilot-specific columns: ``conversation_id`` + ``user_id``. The
abstract overrides inject them via ``**agent_specific`` on the base's
:class:`BaseAgentCallbackHandler` Template Method.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from src.modules.copilot.observability.persistence.llm_call_repository import (
    LlmCallRepository,
)
from src.modules.copilot.observability.persistence.trace_event_repository import (
    TraceEventRepository,
)
from src.shared.agent_observability.recording.base_callback_handler import (
    BaseAgentCallbackHandler,
)


@dataclass
class ObservabilityCallbackHandler(BaseAgentCallbackHandler):
    """Self-contained recorder. One instance per turn.

    Inherits the 8 LangChain callbacks + ``_persist_llm_call`` Template
    Method skeleton from :class:`BaseAgentCallbackHandler`. This class
    only carries copilot-specific repos + ``conversation_id`` / ``user_id``
    fields, and overrides the abstract persisters to inject those onto
    every row.
    """

    conversation_id: UUID | None = None
    user_id: UUID | None = None
    llm_call_repo: LlmCallRepository = None  # type: ignore[assignment]
    trace_repo: TraceEventRepository = None  # type: ignore[assignment]

    # ── abstract method overrides (Template Method) ──────────────────────

    def _persist_llm_call_row(self, **kwargs: Any) -> None:  # noqa: ANN401 — Template Method passthrough
        """Persist one row to ``copilot_llm_call``."""
        self.llm_call_repo.add(
            conversation_id=self.conversation_id,
            user_id=self.user_id,
            parent_span_id=None,
            **kwargs,
        )

    def _persist_trace_event_row(self, **kwargs: Any) -> None:  # noqa: ANN401 — Template Method passthrough
        """Persist one row to ``copilot_trace_event``."""
        self.trace_repo.add(
            conversation_id=self.conversation_id,
            user_id=self.user_id,
            **kwargs,
        )


__all__ = ["ObservabilityCallbackHandler"]
