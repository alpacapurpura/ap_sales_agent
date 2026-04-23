"""SSE streaming integration tests for CopilotOrchestrator.

Verifies that the SSE wire-protocol is correctly formatted for every event type
the orchestrator can emit: text_chunk, tool_start, tool_result, ui_action,
status, done, error.

These tests do NOT require a real LLM or a real database — they exercise the
orchestrator's _process_stream_event / stream_chat logic with hand-crafted
mock events, asserting the exact bytes that reach the client.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, ToolMessage

from src.modules.copilot.api.dto import SSEEvent
from src.modules.copilot.application.orchestrator.chat import CopilotOrchestrator

# ── Helpers ───────────────────────────────────────────────────────────


def _parse_sse(raw: str) -> dict[str, Any]:
    """Parse a single SSE frame ('event: …\\ndata: …\\n\\n') into a dict."""
    event_type: str | None = None
    data: dict | None = None
    for line in raw.strip().split("\n"):
        if line.startswith("event: "):
            event_type = line[len("event: ") :]
        elif line.startswith("data: "):
            data = json.loads(line[len("data: ") :])
    assert event_type is not None, f"No event line in SSE frame: {raw!r}"
    assert data is not None, f"No data line in SSE frame: {raw!r}"
    return {"event": event_type, "data": data}


def _make_orchestrator() -> CopilotOrchestrator:
    """Return an orchestrator whose ConversationRepository is fully mocked."""
    mock_db = MagicMock()
    mock_conv = MagicMock()
    mock_conv.title = None
    mock_conv.messages = []

    with patch(
        "src.modules.copilot.application.orchestrator.chat.ConversationRepository",
    ) as mock_cls:
        mock_repo = MagicMock()
        mock_repo.get_by_id.return_value = mock_conv
        mock_repo.create.return_value = mock_conv
        mock_cls.return_value = mock_repo
        orch = CopilotOrchestrator(mock_db)

    # Make conv_repo accessible for later patching
    orch.conv_repo = mock_repo
    return orch


async def _collect(orch: CopilotOrchestrator, msg: str = "Hola") -> list[dict[str, Any]]:
    """Drive stream_chat to completion and return all parsed SSE events."""
    raw_events: list[str] = [
        frame
        async for frame in orch.stream_chat(
            user_id=MagicMock(),
            tenant_id=MagicMock(),
            message=msg,
        )
    ]
    return [_parse_sse(f) for f in raw_events]


# ── Unit tests for SSEEvent wire format ───────────────────────────────


class TestSSEEventWireFormat:
    """Verify that SSEEvent.to_sse() produces exact wire-protocol bytes."""

    def test_text_chunk_format(self) -> None:
        """text_chunk events must carry a 'content' key."""
        event = SSEEvent(event="text_chunk", data={"content": "Hola mundo"})
        raw = event.to_sse()

        assert raw.startswith("event: text_chunk\n")
        assert "data: " in raw
        assert raw.endswith("\n\n")

        parsed = _parse_sse(raw)
        assert parsed["event"] == "text_chunk"
        assert parsed["data"]["content"] == "Hola mundo"

    def test_done_event_format(self) -> None:
        """done events must carry a 'conversation_id' key."""
        event = SSEEvent(event="done", data={"conversation_id": "abc-123"})
        raw = event.to_sse()

        parsed = _parse_sse(raw)
        assert parsed["event"] == "done"
        assert parsed["data"]["conversation_id"] == "abc-123"

    def test_error_event_format(self) -> None:
        """error events must carry a 'message' key."""
        event = SSEEvent(event="error", data={"message": "Something went wrong"})
        raw = event.to_sse()

        parsed = _parse_sse(raw)
        assert parsed["event"] == "error"
        assert "message" in parsed["data"]

    def test_status_event_format(self) -> None:
        """status events must carry a 'state' key."""
        for state in ("thinking", "streaming", "done"):
            event = SSEEvent(event="status", data={"state": state})
            parsed = _parse_sse(event.to_sse())
            assert parsed["data"]["state"] == state

    def test_tool_start_format(self) -> None:
        """tool_start events must carry 'tool' and 'args' keys."""
        event = SSEEvent(
            event="tool_start",
            data={"tool": "analyze_offer_ladder", "args": {}},
        )
        parsed = _parse_sse(event.to_sse())
        assert parsed["event"] == "tool_start"
        assert "tool" in parsed["data"]
        assert "args" in parsed["data"]

    def test_tool_result_format(self) -> None:
        """tool_result events must carry 'tool' and 'result' keys."""
        event = SSEEvent(
            event="tool_result",
            data={"tool": "analyze_offer_ladder", "result": "Ladder completo"},
        )
        parsed = _parse_sse(event.to_sse())
        assert parsed["event"] == "tool_result"
        assert "tool" in parsed["data"]
        assert "result" in parsed["data"]

    def test_data_is_valid_json(self) -> None:
        """The data field in every SSE frame must be valid JSON."""
        events = [
            SSEEvent(event="text_chunk", data={"content": "test"}),
            SSEEvent(event="done", data={"conversation_id": "x"}),
            SSEEvent(event="error", data={"message": "err"}),
            SSEEvent(event="status", data={"state": "thinking"}),
        ]
        for ev in events:
            raw = ev.to_sse()
            data_line = next(line for line in raw.split("\n") if line.startswith("data: "))
            # Must not raise
            json.loads(data_line[len("data: ") :])

    def test_unicode_preserved_in_spanish(self) -> None:
        """Spanish accents and eñes must survive the wire encoding."""
        event = SSEEvent(event="text_chunk", data={"content": "Próximamente días niño"})
        raw = event.to_sse()
        assert "Próximamente" in raw
        assert "días" in raw
        assert "niño" in raw


# ── _process_stream_event unit tests ─────────────────────────────────


class TestProcessStreamEvent:
    """Test the _process_stream_event dispatcher in isolation."""

    @pytest.fixture()
    def orch(self) -> CopilotOrchestrator:
        return _make_orchestrator()

    def test_text_chunk_event_returns_sse_and_content(self, orch: CopilotOrchestrator) -> None:
        mock_chunk = MagicMock()
        mock_chunk.content = "Hola, "
        event = {"event": "on_chat_model_stream", "data": {"chunk": mock_chunk}}

        sse, text = orch._process_stream_event(event, [], {})

        assert text == "Hola, "
        assert sse is not None
        parsed = _parse_sse(sse)
        assert parsed["event"] == "text_chunk"
        assert parsed["data"]["content"] == "Hola, "

    def test_empty_chunk_content_returns_none(self, orch: CopilotOrchestrator) -> None:
        mock_chunk = MagicMock()
        mock_chunk.content = ""
        event = {"event": "on_chat_model_stream", "data": {"chunk": mock_chunk}}

        sse, text = orch._process_stream_event(event, [], {})

        assert sse is None
        assert text is None

    def test_on_chat_model_end_accumulates_message(self, orch: CopilotOrchestrator) -> None:
        ai_msg = AIMessage(content="Respuesta completa")
        event = {"event": "on_chat_model_end", "data": {"output": ai_msg}}
        accumulated: list = []

        sse, text = orch._process_stream_event(event, accumulated, {})

        assert sse is None
        assert text is None
        assert len(accumulated) == 1
        assert accumulated[0] is ai_msg

    def test_on_tool_start_emits_tool_start_event(self, orch: CopilotOrchestrator) -> None:
        event = {
            "event": "on_tool_start",
            "name": "analyze_offer_ladder",
            "data": {"input": {"query": "test"}},
        }

        sse, text = orch._process_stream_event(event, [], {})

        assert text is None
        assert sse is not None
        parsed = _parse_sse(sse)
        assert parsed["event"] == "tool_start"
        assert parsed["data"]["tool"] == "analyze_offer_ladder"

    def test_unknown_event_returns_none_none(self, orch: CopilotOrchestrator) -> None:
        event = {"event": "on_unknown_event_type", "data": {}}

        sse, text = orch._process_stream_event(event, [], {})

        assert sse is None
        assert text is None

    def test_on_tool_end_emits_tool_result_event(self, orch: CopilotOrchestrator) -> None:
        event = {
            "event": "on_tool_end",
            "name": "analyze_offer_ladder",
            "data": {"output": "Ladder analizado correctamente"},
        }

        sse = orch._handle_tool_end(event, [], {})

        assert sse is not None
        # The result_sse contains at least one SSE frame
        parsed = _parse_sse(sse.split("\n\n")[0] + "\n\n")
        assert parsed["event"] == "tool_result"
        assert parsed["data"]["tool"] == "analyze_offer_ladder"

    def test_on_tool_end_with_ui_action_emits_extra_event(self, orch: CopilotOrchestrator) -> None:
        """When tool output JSON contains 'ui_action', an extra ui_action SSE is emitted."""
        ui_payload = {"type": "navigate", "route": "/brand"}
        tool_output = json.dumps({"result": "ok", "ui_action": ui_payload})
        event = {
            "event": "on_tool_end",
            "name": "some_tool",
            "data": {"output": tool_output},
        }

        sse = orch._handle_tool_end(event, [], {})

        # Split on double-newline to get individual frames
        frames = [f + "\n\n" for f in sse.split("\n\n") if f.strip()]
        assert len(frames) == 2  # tool_result + ui_action

        parsed_second = _parse_sse(frames[1])
        assert parsed_second["event"] == "ui_action"

    def test_tool_result_truncated_at_4000_chars(self, orch: CopilotOrchestrator) -> None:
        """Tool results longer than 4000 chars are truncated in the SSE event.

        Cap raised from 500 → 4000 to fit full AsyncToolJob dispatch payloads
        (job_id, poll_endpoint, target_label_es, etc.) which the frontend must
        parse to register polling. Matches trace recorder MAX_PAYLOAD_CHARS.
        """
        long_output = "x" * 5000
        event = {
            "event": "on_tool_end",
            "name": "some_tool",
            "data": {"output": long_output},
        }

        sse = orch._handle_tool_end(event, [], {})

        parsed = _parse_sse(sse.split("\n\n")[0] + "\n\n")
        result_value = parsed["data"]["result"]
        assert len(result_value) <= 4000


# ── Integration: stream_chat event sequence ───────────────────────────


class TestStreamChatEventSequence:
    """Integration tests for the full stream_chat event sequence."""

    async def _run_with_mock_graph(
        self,
        orch: CopilotOrchestrator,
        fake_stream,
        timeout_seconds: float = 5.0,
    ) -> list[dict[str, Any]]:
        with (
            patch(
                "src.modules.copilot.application.orchestrator.chat.copilot_graph",
            ) as mock_graph,
            patch(
                "src.modules.copilot.application.orchestrator.chat.COPILOT_STREAM_TIMEOUT_SECONDS",
                timeout_seconds,
            ),
            patch(
                "src.modules.copilot.application.orchestrator.chat.redis_client",
                None,
            ),
        ):
            mock_graph.astream_events = fake_stream
            return await _collect(orch)

    @pytest.fixture()
    def orch(self) -> CopilotOrchestrator:
        return _make_orchestrator()

    async def test_happy_path_event_sequence(self, orch: CopilotOrchestrator) -> None:
        """Happy path: status→streaming→text_chunk→status→done→done."""

        async def fake_stream(state, *, version="v2"):
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": MagicMock(content="Buenos ")},
            }
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": MagicMock(content="días")},
            }
            yield {
                "event": "on_chat_model_end",
                "data": {"output": AIMessage(content="Buenos días")},
            }

        events = await self._run_with_mock_graph(orch, fake_stream)
        event_types = [e["event"] for e in events]

        # Must start with status:thinking
        assert events[0] == {"event": "status", "data": {"state": "thinking"}}
        # Must contain text_chunk events
        assert "text_chunk" in event_types
        # Must end with done
        assert event_types[-1] == "done"
        # Must not contain error
        assert "error" not in event_types

    async def test_text_chunks_content_is_correct(self, orch: CopilotOrchestrator) -> None:
        """All text_chunk contents concatenated must equal the full response."""

        async def fake_stream(state, *, version="v2"):
            for word in ["Hola", " mundo", " desde", " Nicolify"]:
                yield {
                    "event": "on_chat_model_stream",
                    "data": {"chunk": MagicMock(content=word)},
                }
            yield {
                "event": "on_chat_model_end",
                "data": {"output": AIMessage(content="Hola mundo desde Nicolify")},
            }

        events = await self._run_with_mock_graph(orch, fake_stream)
        chunks = [e["data"]["content"] for e in events if e["event"] == "text_chunk"]
        assert "".join(chunks) == "Hola mundo desde Nicolify"

    async def test_tool_call_produces_tool_events(self, orch: CopilotOrchestrator) -> None:
        """Tool calls must produce tool_start and tool_result SSE events."""

        async def fake_stream(state, *, version="v2"):
            yield {
                "event": "on_tool_start",
                "name": "analyze_offer_ladder",
                "data": {"input": {}},
            }
            yield {
                "event": "on_tool_end",
                "name": "analyze_offer_ladder",
                "data": {"output": "Análisis completo"},
            }

        events = await self._run_with_mock_graph(orch, fake_stream)
        event_types = [e["event"] for e in events]

        assert "tool_start" in event_types
        assert "tool_result" in event_types

        tool_start = next(e for e in events if e["event"] == "tool_start")
        assert tool_start["data"]["tool"] == "analyze_offer_ladder"

    async def test_error_on_graph_exception(self, orch: CopilotOrchestrator) -> None:
        """When the graph raises an unexpected exception, an error SSE is emitted."""

        async def fake_stream_raises(state, *, version="v2"):
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": MagicMock(content="Starting...")},
            }
            err_msg = "Unexpected LLM failure"
            raise RuntimeError(err_msg)

        events = await self._run_with_mock_graph(orch, fake_stream_raises)
        event_types = [e["event"] for e in events]

        assert "error" in event_types
        error_ev = next(e for e in events if e["event"] == "error")
        assert "message" in error_ev["data"]
        # Stream must still terminate with done
        assert "done" in event_types

    async def test_done_event_carries_conversation_id(self, orch: CopilotOrchestrator) -> None:
        """The final done event must carry the conversation_id."""

        async def fake_stream(state, *, version="v2"):
            yield {
                "event": "on_chat_model_end",
                "data": {"output": AIMessage(content="OK")},
            }

        events = await self._run_with_mock_graph(orch, fake_stream)
        done_events = [e for e in events if e["event"] == "done"]

        assert len(done_events) == 1
        assert "conversation_id" in done_events[0]["data"]

    async def test_empty_graph_still_emits_done(self, orch: CopilotOrchestrator) -> None:
        """An empty graph response (no events) still terminates properly."""

        async def fake_empty_stream(state, *, version="v2"):
            return
            yield  # Make it an async generator

        events = await self._run_with_mock_graph(orch, fake_empty_stream)
        event_types = [e["event"] for e in events]

        # Must still end cleanly
        assert "done" in event_types
        assert "error" not in event_types

    async def test_status_streaming_emitted_before_chunks(self, orch: CopilotOrchestrator) -> None:
        """status:streaming must be emitted before any text_chunk events."""

        async def fake_stream(state, *, version="v2"):
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": MagicMock(content="Texto")},
            }

        events = await self._run_with_mock_graph(orch, fake_stream)

        status_events = [i for i, e in enumerate(events) if e["event"] == "status"]
        chunk_events = [i for i, e in enumerate(events) if e["event"] == "text_chunk"]

        if chunk_events:
            # At least one status event must precede the first chunk
            assert min(status_events) < min(chunk_events)


# ── Serialise/Deserialise round-trip ─────────────────────────────────


class TestSerialiseRoundTrip:
    """Verify that message serialisation/deserialisation is symmetric."""

    def test_human_message_round_trip(self) -> None:
        from langchain_core.messages import HumanMessage

        orch = _make_orchestrator()
        msgs = [HumanMessage(content="¿Cómo me ayudas?")]
        serialised = orch._serialize_messages(msgs)
        deserialised = orch._deserialize_messages(serialised)

        assert len(deserialised) == 1
        assert isinstance(deserialised[0], HumanMessage)
        assert deserialised[0].content == "¿Cómo me ayudas?"

    def test_ai_message_with_tool_calls_round_trip(self) -> None:
        orch = _make_orchestrator()
        ai_msg = AIMessage(
            content="Voy a analizar tu escalera.",
            tool_calls=[{"id": "tc-1", "name": "analyze_offer_ladder", "args": {"q": "test"}}],
        )
        serialised = orch._serialize_messages([ai_msg])
        deserialised = orch._deserialize_messages(serialised)

        assert isinstance(deserialised[0], AIMessage)
        assert deserialised[0].tool_calls[0]["name"] == "analyze_offer_ladder"

    def test_tool_message_round_trip(self) -> None:
        orch = _make_orchestrator()
        tool_msg = ToolMessage(
            content="Resultado del análisis",
            tool_call_id="tc-1",
            name="analyze_offer_ladder",
        )
        serialised = orch._serialize_messages([tool_msg])
        deserialised = orch._deserialize_messages(serialised)

        assert len(deserialised) == 1
        assert isinstance(deserialised[0], ToolMessage)
        assert deserialised[0].content == "Resultado del análisis"
