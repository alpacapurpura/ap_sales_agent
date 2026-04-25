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
