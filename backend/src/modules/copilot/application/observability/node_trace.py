"""F9 — node_enter / node_exit emission from astream_events.

# [COPILOT-NODE-TRACE-F9] -> docs/domains/copilot/redesign-2026-04/phases/F9-quality-observability.md

LangGraph's ``astream_events(version="v2")`` yields ``on_chain_start`` and
``on_chain_end`` for each node transition (deep_agent main agent_node +
subagents + middleware). The orchestrator forwards these to the
``TraceRecorder`` so a single SQL query reconstructs the per-node timeline
of a turn.

Filter: only emit when ``event["metadata"]["langgraph_node"]`` is present.
That key is set by LangGraph for actual graph nodes — chains and wrappers
that surround them lack it. Emitting on everything would multiply trace
rows by 5-10x with no diagnostic value.

Best-effort: any exception in the recorder is swallowed (the recorder
itself is best-effort but the path before it — payload truncation,
metadata access — also must not break the streaming loop).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = structlog.get_logger()

# Cap on the input/output preview sent into JSONB. Matches
# ``trace_recorder.MAX_PAYLOAD_CHARS`` so the row never exceeds the column
# size in practice (even when many nodes fire per turn).
MAX_PREVIEW_CHARS: int = 500


def _truncate_preview(value: Any) -> str:  # noqa: ANN401 — polymorphic
    """Render *value* as a short string preview suitable for JSONB storage."""
    if value is None:
        return ""
    text = value if isinstance(value, str) else repr(value)
    if len(text) > MAX_PREVIEW_CHARS:
        return text[:MAX_PREVIEW_CHARS] + " [truncated]"
    return text


def emit_node_trace_event(recorder: object, event: Mapping[str, Any]) -> None:
    """Emit ``node_enter`` / ``node_exit`` for LangGraph node transitions.

    No-op when:
    * the event is not a ``on_chain_start`` / ``on_chain_end``,
    * the event lacks ``metadata.langgraph_node`` (i.e. not a real node),
    * the recorder has no ``record`` method (best-effort fallback).
    """
    kind = event.get("event")
    if kind not in ("on_chain_start", "on_chain_end"):
        return

    metadata = event.get("metadata") or {}
    node_name = metadata.get("langgraph_node")
    if not node_name:
        return

    record = getattr(recorder, "record", None)
    if not callable(record):
        return

    event_type = "node_enter" if kind == "on_chain_start" else "node_exit"
    data: dict[str, Any] = {
        "node": node_name,
        "graph_step": metadata.get("langgraph_step"),
    }
    payload = event.get("data") or {}
    if kind == "on_chain_start":
        inp = payload.get("input")
        if inp is not None:
            data["input_preview"] = _truncate_preview(inp)
    else:
        out = payload.get("output")
        if out is not None:
            data["output_preview"] = _truncate_preview(out)

    # B15-TP8 — propagate ``run_id`` + ``parent_ids`` as span tree.
    # ``astream_events(v2)`` yields the same ``run_id`` for paired
    # ``on_chain_start``/``on_chain_end`` so node_enter and node_exit pair
    # up. ``parent_ids[-1]`` is the immediate parent run (LangGraph
    # convention) — without it the tree collapses to a flat list.
    extra_kwargs: dict[str, Any] = {}
    run_id = event.get("run_id")
    if run_id is not None:
        extra_kwargs["span_id"] = run_id
    parent_ids = event.get("parent_ids") or ()
    if parent_ids:
        extra_kwargs["parent_span_id"] = parent_ids[-1]

    try:
        record(
            event_type=event_type,
            name=str(node_name),
            data=data,
            **extra_kwargs,
        )
    except Exception as exc:  # noqa: BLE001 — observability is best-effort
        logger.warning(
            "copilot_node_trace_emit_failed",
            kind=event_type,
            node=str(node_name),
            error=str(exc)[:200],
        )


__all__ = ("MAX_PREVIEW_CHARS", "emit_node_trace_event")
