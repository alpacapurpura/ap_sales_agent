"""Read-only LangGraph trajectory observer for the sales_agent eval harness.

Per ``03-arch-agentic.md`` § "Decisión arquitectónica clave" + Decision
B6 ratified 2026-05-05: the spy is a **read-only LangChain callback
handler** added as a SECOND entry in the ``RunnableConfig.callbacks``
list, alongside the production sales_agent callback handler that
persists rows to ``sales_agent_trace_event`` + ``sales_agent_llm_call``.

Composition over subclass — anti-duplication §0 absolute rule. The spy
inherits ``langchain_core.callbacks.BaseCallbackHandler`` (LangChain
native) and is appended to the production callbacks list at invoke
time. It NEVER inherits from the shared canonical abstract base in
``shared/agent_observability/recording/base_callback_handler.py`` —
doing so would require stub overrides of every abstract persistence
method, duplicating plumbing already cemented in the production
subclass.

The spy reads:
    - ``state["next_node"]`` from ``on_chain_end`` outputs (LangGraph
      node exit) → reconstructs ``specialist_history`` per Capa 1 of the
      multi-layer assertion stack (T-4).
    - ``serialized.get("name")`` cached at ``on_tool_start`` and drained
      to ``tool_calls`` at ``on_tool_end`` → Capa 2 (tool-call audit).

Best-effort per ``.claude/rules/copilot-observability.md`` + Tessl
``graceful-degradation`` Rule 6: every callback method body wraps its
logic in ``try/except`` + ``structlog.warning``. A spy raising MUST
NEVER break ``agent_app.ainvoke``.

PII safety: ``to_artifact_dict`` returns the raw observed values; the
artifacts writer (``runner/artifacts.py``) is the single point that
applies ``sanitize_payload`` (reused from shared canonical
``shared.agent_observability.recording.sanitization``) BEFORE writing
trace.json. Anti-duplication §0 + spec NFR (PII).

Cohabitation:
    - The production handler runs FIRST (DB write side effect).
    - The spy runs SECOND (in-memory append).
    - LangChain executes callbacks in list order per its public spec.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import structlog
from langchain_core.callbacks import BaseCallbackHandler

if TYPE_CHECKING:
    from uuid import UUID

logger = structlog.get_logger()


@dataclass
class TrajectorySpy(BaseCallbackHandler):
    """Pure observer over the LangGraph state machine for eval purposes.

    Attributes:
        specialist_history: Sequence of ``state["next_node"]`` values
            captured at every ``on_chain_end`` event with a string,
            non-terminal value. Terminal sentinel values (``"respond"``,
            ``None``) are filtered to prevent noise — the smoke harness
            expects the routing trail (e.g.
            ``["qualifier", "tool_executor"]``).
        tool_calls: Per-tool record dicts ``{"name": str, "input": str,
            "run_id": str}`` drained at every ``on_tool_end``. The
            ``input`` field is the raw tool arg string captured at
            ``on_tool_start`` — sanitised later by the artifacts writer.
        node_visits: Lightweight breadcrumb of every ``on_chain_end``
            seen, useful for downstream diagnostics. Each entry carries
            ``{"run_id": str, "next_node": str | None}``.
        _tool_runs_inflight: Internal cache mapping ``run_id → {"name",
            "input"}`` between ``on_tool_start`` and ``on_tool_end``.
            Drained at ``on_tool_end`` so the dict stays small.
    """

    specialist_history: list[str] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    node_visits: list[dict[str, Any]] = field(default_factory=list)
    _tool_runs_inflight: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Terminal sentinels filtered from specialist_history per arch §
    # "State machine details" — ``respond`` exits to END, ``None`` means
    # the node did not set ``next_node`` (defensive default).
    _TERMINAL_NEXT_NODE_VALUES: frozenset[str] = field(
        default=frozenset({"respond"}),
        init=False,
        repr=False,
    )

    def on_chain_end(
        self,
        outputs: Any,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Capture ``state.next_node`` after each LangGraph node exit.

        Best-effort: a malformed ``outputs`` payload (non-dict, missing
        key, unexpected type) MUST NEVER raise — the spy logs and
        continues. Decision B6 + ``copilot-observability.md``.
        """
        del parent_run_id, kwargs  # not consumed at this layer
        try:
            next_node: Any = outputs.get("next_node") if isinstance(outputs, dict) else None
            self.node_visits.append(
                {
                    "run_id": str(run_id),
                    "next_node": next_node if isinstance(next_node, str) else None,
                },
            )
            if isinstance(next_node, str) and next_node not in self._TERMINAL_NEXT_NODE_VALUES:
                self.specialist_history.append(next_node)
        except Exception as exc:  # noqa: BLE001 — best-effort observability
            logger.warning(
                "eval_trajectory_spy_on_chain_end_failed",
                run_id=str(run_id),
                error=str(exc),
            )

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Cache the tool name + raw input keyed by ``run_id``.

        Drained at the matching ``on_tool_end``. ``serialized`` is the
        LangChain canonical descriptor — name extraction via
        ``.get("name")`` matches the shared base handler contract.
        """
        del parent_run_id, kwargs
        try:
            tool_name: str = serialized.get("name", "") if isinstance(serialized, dict) else ""
            self._tool_runs_inflight[str(run_id)] = {
                "name": tool_name,
                "input": input_str,
            }
        except Exception as exc:  # noqa: BLE001 — best-effort observability
            logger.warning(
                "eval_trajectory_spy_on_tool_start_failed",
                run_id=str(run_id),
                error=str(exc),
            )

    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Drain the in-flight tool record + append to ``tool_calls``.

        If ``run_id`` is not in the in-flight cache (e.g. ``on_tool_start``
        never fired due to LangChain wiring quirk), the entry is still
        recorded with empty ``name`` — observed in tests by the
        cache-drain edge-case meta-test below.
        """
        del parent_run_id, kwargs
        try:
            run_id_str = str(run_id)
            captured = self._tool_runs_inflight.pop(run_id_str, None)
            self.tool_calls.append(
                {
                    "run_id": run_id_str,
                    "name": (captured or {}).get("name", ""),
                    "input": (captured or {}).get("input", ""),
                    "output": output if isinstance(output, str) else repr(output),
                },
            )
        except Exception as exc:  # noqa: BLE001 — best-effort observability
            logger.warning(
                "eval_trajectory_spy_on_tool_end_failed",
                run_id=str(run_id),
                error=str(exc),
            )

    def reset(self) -> None:
        """Clear every accumulator. Called at fixture teardown.

        Function-scoped fixture contract: every test starts with an
        empty spy. Reset is idempotent (calling on a fresh instance is
        a no-op).
        """
        self.specialist_history.clear()
        self.tool_calls.clear()
        self.node_visits.clear()
        self._tool_runs_inflight.clear()

    def to_artifact_dict(self) -> dict[str, Any]:
        """Serialise the observed state for downstream artifact writing.

        Returns the raw collected payload — the artifacts writer
        (``runner/artifacts.py``) is the single point applying
        ``sanitize_payload`` per anti-duplication §0 + spec NFR PII.
        """
        return {
            "specialist_history": list(self.specialist_history),
            "tool_calls": list(self.tool_calls),
            "node_visits": list(self.node_visits),
        }


__all__ = ["TrajectorySpy"]
