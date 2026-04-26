"""F9 — node_enter / node_exit emission contract.

# [COPILOT-NODE-TRACE-F9]
"""

from __future__ import annotations

from src.modules.copilot.application.observability.node_trace import (
    emit_node_trace_event,
)


class _FakeRecorder:
    def __init__(self):
        self.calls: list[dict] = []

    def record(self, **kwargs):
        self.calls.append(kwargs)


def test_emits_node_enter_for_on_chain_start_with_langgraph_node():
    rec = _FakeRecorder()
    emit_node_trace_event(
        rec,
        {
            "event": "on_chain_start",
            "metadata": {"langgraph_node": "agent", "langgraph_step": 1},
            "data": {"input": {"messages": ["hola"]}},
        },
    )
    assert len(rec.calls) == 1
    call = rec.calls[0]
    assert call["event_type"] == "node_enter"
    assert call["name"] == "agent"
    assert call["data"]["node"] == "agent"
    assert call["data"]["graph_step"] == 1
    assert "input_preview" in call["data"]


def test_emits_node_exit_for_on_chain_end_with_output_preview():
    rec = _FakeRecorder()
    emit_node_trace_event(
        rec,
        {
            "event": "on_chain_end",
            "metadata": {"langgraph_node": "tool_executor", "langgraph_step": 2},
            "data": {"output": {"result": "ok"}},
        },
    )
    assert len(rec.calls) == 1
    assert rec.calls[0]["event_type"] == "node_exit"
    assert "output_preview" in rec.calls[0]["data"]


def test_skips_events_without_langgraph_node_metadata():
    rec = _FakeRecorder()
    emit_node_trace_event(
        rec,
        {
            "event": "on_chain_start",
            "metadata": {"some_other": "tag"},  # no langgraph_node
            "data": {"input": {}},
        },
    )
    assert rec.calls == []


def test_skips_non_chain_events():
    rec = _FakeRecorder()
    for kind in ("on_chat_model_stream", "on_tool_start", "on_tool_end"):
        emit_node_trace_event(
            rec,
            {"event": kind, "metadata": {"langgraph_node": "agent"}},
        )
    assert rec.calls == []


def test_truncates_long_previews():
    rec = _FakeRecorder()
    huge = "x" * 5_000
    emit_node_trace_event(
        rec,
        {
            "event": "on_chain_end",
            "metadata": {"langgraph_node": "agent"},
            "data": {"output": huge},
        },
    )
    preview = rec.calls[0]["data"]["output_preview"]
    assert "[truncated]" in preview
    assert len(preview) <= 600  # MAX_PREVIEW_CHARS + truncate suffix


def test_no_op_if_recorder_lacks_record_method():
    """Defensive: a NoopRecorder shape mismatch must not raise."""

    class _NoRecord:
        pass

    emit_node_trace_event(
        _NoRecord(),
        {
            "event": "on_chain_start",
            "metadata": {"langgraph_node": "agent"},
            "data": {},
        },
    )  # must not raise


def test_swallows_recorder_exceptions():
    class _BoomRecorder:
        def record(self, **_kwargs):
            msg = "db down"
            raise RuntimeError(msg)

    emit_node_trace_event(
        _BoomRecorder(),
        {
            "event": "on_chain_end",
            "metadata": {"langgraph_node": "agent"},
            "data": {"output": "ok"},
        },
    )  # must not raise


def test_propagates_run_id_as_span_id_for_pairing_enter_exit():
    # B15-TP8 — node_enter and node_exit must share span_id (LangGraph
    # ``astream_events`` v2 yields the same ``run_id`` for paired chain
    # start/end). Without this, the span tree collapses to a flat list.
    from uuid import UUID

    rec = _FakeRecorder()
    run_id = UUID("11111111-1111-1111-1111-111111111111")
    emit_node_trace_event(
        rec,
        {
            "event": "on_chain_start",
            "run_id": run_id,
            "parent_ids": [],
            "metadata": {"langgraph_node": "agent"},
            "data": {"input": "x"},
        },
    )
    emit_node_trace_event(
        rec,
        {
            "event": "on_chain_end",
            "run_id": run_id,
            "parent_ids": [],
            "metadata": {"langgraph_node": "agent"},
            "data": {"output": "y"},
        },
    )
    assert rec.calls[0]["span_id"] == run_id
    assert rec.calls[1]["span_id"] == run_id


def test_propagates_immediate_parent_run_id_as_parent_span_id():
    # B15-TP8 — ``parent_ids`` is the chain of ancestor run_ids; the last
    # entry is the immediate parent (LangGraph convention). Without this
    # all rows persist with parent_span_id=NULL → tree no reconstruible.
    from uuid import UUID

    rec = _FakeRecorder()
    parent_run = UUID("22222222-2222-2222-2222-222222222222")
    own_run = UUID("33333333-3333-3333-3333-333333333333")
    emit_node_trace_event(
        rec,
        {
            "event": "on_chain_start",
            "run_id": own_run,
            "parent_ids": [parent_run],
            "metadata": {"langgraph_node": "model"},
            "data": {"input": "x"},
        },
    )
    assert rec.calls[0]["parent_span_id"] == parent_run
    assert rec.calls[0]["span_id"] == own_run


def test_omits_run_id_kwargs_when_event_lacks_them():
    # Defensive: tests + older event shapes may not provide ``run_id``;
    # caller never breaks the existing contract for unrelated callers.
    rec = _FakeRecorder()
    emit_node_trace_event(
        rec,
        {
            "event": "on_chain_start",
            "metadata": {"langgraph_node": "agent"},
            "data": {"input": "x"},
        },
    )
    call = rec.calls[0]
    assert call.get("span_id") is None
    assert call.get("parent_span_id") is None
