"""LangChain callback handler for sales_agent — event-sourced ingress.

Subclass of :class:`~src.shared.agent_observability.recording.base_callback_handler.BaseAgentCallbackHandler`
(S0 abstract Template Method, S11A lift). Wired into the orchestrator
via ``RunnableConfig(callbacks=[handler])`` from
``application/orchestrator/chat.py``.

What it captures (mapped to columns / event types):

* ``on_chat_model_start`` — opens an LLM span (in-memory). Captures
  provider, model_requested, started_at, run_id.
* ``on_llm_end``           — closes the open chat span. Pulls usage
  metadata, runs the shared cost calculator, resolves FX, persists one
  row in ``sales_agent_llm_call`` and a mirror row in
  ``sales_agent_trace_event`` (event_type='llm_call').
* ``on_llm_error``         — same close, with status='error' + zero cost.
* ``on_tool_start`` / ``on_tool_end`` / ``on_tool_error`` — persist a
  ``tool_call`` trace event with duration_ms.
* ``on_chain_start`` / ``on_chain_end`` — node_enter / node_exit rows
  for LangGraph nodes.

**Best-effort.** Any exception during persistence is swallowed and
logged via ``logger.warning`` — never propagated. ``_safe_rollback`` on
the base handles the SQLAlchemy session via the ``db_session`` field.

Sales-agent-specific columns: ``lead_id`` + ``channel_type``. The
abstract overrides inject them via ``**agent_specific`` on the base's
:class:`BaseAgentCallbackHandler` Template Method.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from src.modules.sales_agent.observability.persistence.llm_call_repository import (
    SalesAgentLlmCallRepository,
)
from src.modules.sales_agent.observability.persistence.trace_event_repository import (
    SalesAgentTraceEventRepository,
)
from src.shared.agent_observability.recording.base_callback_handler import (
    BaseAgentCallbackHandler,
)


@dataclass
class SalesAgentCallbackHandler(BaseAgentCallbackHandler):
    """Self-contained recorder for sales_agent. One instance per turn.

    Inherits the 8 LangChain callbacks + ``_persist_llm_call`` Template
    Method skeleton from :class:`BaseAgentCallbackHandler`. This class
    only carries sales-specific repos + ``lead_id`` / ``channel_type``
    + ``db_session`` for ``_safe_rollback``, and overrides the abstract
    persisters to inject those onto every row.
    """

    lead_id: UUID = None  # type: ignore[assignment] — required, defaulted only for dataclass inheritance ordering
    channel_type: str = ""
    llm_call_repo: SalesAgentLlmCallRepository = None  # type: ignore[assignment]
    trace_repo: SalesAgentTraceEventRepository = None  # type: ignore[assignment]
    db_session: Any = None  # SQLAlchemy Session — typed Any to keep Protocol structural

    # ── abstract method overrides (Template Method) ──────────────────────

    def _persist_llm_call_row(self, **kwargs: Any) -> None:  # noqa: ANN401 — Template Method passthrough
        """Persist one row to ``sales_agent_llm_call`` (sync repo)."""
        self.llm_call_repo.add(
            parent_span_id=None,
            lead_id=self.lead_id,
            channel_type=self.channel_type,
            **kwargs,
        )

    def _persist_trace_event_row(self, **kwargs: Any) -> None:  # noqa: ANN401 — Template Method passthrough
        """Persist one row to ``sales_agent_trace_event`` (sync repo)."""
        self.trace_repo.add(
            lead_id=self.lead_id,
            channel_type=self.channel_type,
            **kwargs,
        )


__all__ = ["SalesAgentCallbackHandler"]
