"""Tests for SSE v2 block events emitted by the CopilotOrchestrator.

F8 §5.4 — only v2 is emitted now. The legacy ``text_chunk`` channel
was removed once the FE migrated to the block_delta render path.
- Text streaming: block_start / block_delta / block_end (per text block).
- Tool results: ``tool_result`` + ``block_append`` for typed blocks.
- UI actions: ``ui_action`` + ``block_append`` for CardBlocks.
- ``message_start`` precedes every block.
- ``message_end`` carries the finalized blocks list + tokens_used.

Tests use hand-crafted LangGraph events; no real LLM required.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.copilot.application.orchestrator.chat import (
    CopilotOrchestrator,
    _StreamAccumulator,
)

# ── Helpers ────────────────────────────────────────────────────────────────────


def _parse_sse(raw: str) -> dict[str, Any]:
    """Parse a single SSE frame into {event, data}."""
    event_type: str | None = None
    data: dict | None = None
    for line in raw.strip().split("\n"):
        if line.startswith("event: "):
            event_type = line[len("event: ") :]
        elif line.startswith("data: "):
            data = json.loads(line[len("data: ") :])
    assert event_type is not None, f"No event line: {raw!r}"
    assert data is not None, f"No data line: {raw!r}"
    return {"event": event_type, "data": data}


def _split_frames(raw_stream: list[str]) -> list[dict[str, Any]]:
    """Parse a list of raw SSE strings into parsed event dicts."""
    return [_parse_sse(frame) for frame in raw_stream if frame.strip()]


def _make_orchestrator() -> CopilotOrchestrator:
    """Build an orchestrator with fully mocked ConversationRepository."""
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

    orch.conv_repo = mock_repo  # expose for further patching
    return orch


def _make_text_chunk_event(content: str) -> dict:
    """Build an on_chat_model_stream event for the given text content."""
    mock_chunk = MagicMock()
    mock_chunk.content = content
    return {"event": "on_chat_model_stream", "data": {"chunk": mock_chunk}}


# ── Tests: _emit_text_chunk_v2 (unit) ─────────────────────────────────────────


class TestEmitTextChunkV2:
    """Unit tests for _emit_text_chunk_v2 static method."""

    @pytest.mark.asyncio
    async def test_first_chunk_emits_block_start_and_block_delta(self) -> None:
        """First text chunk emits block_start (empty markdown) + block_delta."""
        acc = _StreamAccumulator()
        msg_id = "test-msg-id"
        frames: list[str] = []

        async for sse in CopilotOrchestrator._emit_text_chunk_v2(acc, msg_id, "Hola"):
            frames.append(sse)

        assert len(frames) == 2  # block_start + block_delta
        start = _parse_sse(frames[0])
        delta = _parse_sse(frames[1])

        assert start["event"] == "block_start"
        assert start["data"]["type"] == "text"
        assert start["data"]["message_id"] == msg_id
        assert start["data"]["index"] == 0
        assert start["data"]["partial"]["markdown"] == ""

        assert delta["event"] == "block_delta"
        assert delta["data"]["delta"]["markdown"] == "Hola"
        assert delta["data"]["block_id"] == start["data"]["block_id"]

    @pytest.mark.asyncio
    async def test_subsequent_chunks_emit_only_block_delta(self) -> None:
        """After first chunk, subsequent chunks emit only block_delta (no block_start)."""
        acc = _StreamAccumulator()
        msg_id = "msg-x"

        # First chunk
        async for _ in CopilotOrchestrator._emit_text_chunk_v2(acc, msg_id, "Uno"):
            pass

        # Second chunk — should not re-emit block_start
        frames: list[str] = []
        async for sse in CopilotOrchestrator._emit_text_chunk_v2(acc, msg_id, " dos"):
            frames.append(sse)

        assert len(frames) == 1
        parsed = _parse_sse(frames[0])
        assert parsed["event"] == "block_delta"
        assert parsed["data"]["delta"]["markdown"] == " dos"

    @pytest.mark.asyncio
    async def test_accumulator_markdown_grows_with_chunks(self) -> None:
        """Accumulator markdown is the concatenation of all chunks."""
        acc = _StreamAccumulator()
        msg_id = "msg-y"

        for chunk in ["Parte ", "uno", " y dos"]:
            async for _ in CopilotOrchestrator._emit_text_chunk_v2(acc, msg_id, chunk):
                pass

        assert acc.text_block_markdown == "Parte uno y dos"

    @pytest.mark.asyncio
    async def test_block_id_stable_across_chunks(self) -> None:
        """The same block_id is reused for all chunks in a single text block."""
        acc = _StreamAccumulator()
        msg_id = "msg-z"

        block_ids: list[str] = []
        for chunk in ["A", "B", "C"]:
            async for sse in CopilotOrchestrator._emit_text_chunk_v2(acc, msg_id, chunk):
                parsed = _parse_sse(sse)
                if "block_id" in parsed["data"]:
                    block_ids.append(parsed["data"]["block_id"])

        assert len(set(block_ids)) == 1, "All chunks should share the same block_id"


# ── Tests: _tool_result_to_block helper ──────────────────────────────────────


class TestToolResultToBlock:
    """Unit tests for _tool_result_to_block adapter."""

    def test_search_knowledge_base_returns_citation_blocks(self) -> None:
        """search_knowledge_base output → list of CitationBlock dicts."""
        from src.modules.copilot.application.orchestrator.chat import _tool_result_to_block

        result_json = json.dumps(
            [
                {
                    "type": "citation",
                    "source": "Doc: brand-book.md",
                    "snippet": "La voz de la marca es cálida.",
                    "score": 0.9,
                    "url": None,
                }
            ]
        )
        blocks = _tool_result_to_block("search_knowledge_base", result_json)

        assert blocks is not None
        assert len(blocks) == 1
        assert blocks[0]["type"] == "citation"
        assert blocks[0]["source"] == "Doc: brand-book.md"
        assert "snippet" in blocks[0]

    def test_search_assets_image_returns_image_block(self) -> None:
        """search_assets with image asset → ImageBlock."""
        from uuid import uuid4

        from src.modules.copilot.application.orchestrator.chat import _tool_result_to_block

        asset_id = str(uuid4())
        result_json = json.dumps(
            [
                {
                    "asset_id": asset_id,
                    "public_url": "https://cdn.example.com/img.png",
                    "mime": "image/png",
                    "kind": "image",
                    "filename": "hero.png",
                    "description": "Hero image",
                }
            ]
        )
        blocks = _tool_result_to_block("search_assets", result_json)

        assert blocks is not None
        assert len(blocks) == 1
        assert blocks[0]["type"] == "image"
        assert blocks[0]["asset_id"] == asset_id

    def test_get_asset_audio_returns_audio_block(self) -> None:
        """get_asset with audio asset → AudioBlock."""
        from uuid import uuid4

        from src.modules.copilot.application.orchestrator.chat import _tool_result_to_block

        asset_id = str(uuid4())
        result_json = json.dumps(
            {
                "asset_id": asset_id,
                "public_url": "https://cdn.example.com/voice.webm",
                "mime": "audio/webm",
                "kind": "audio",
                "filename": "voice.webm",
                "description": "Voice note",
            }
        )
        blocks = _tool_result_to_block("get_asset", result_json)

        assert blocks is not None
        assert len(blocks) == 1
        assert blocks[0]["type"] == "audio"
        assert blocks[0]["asset_id"] == asset_id
        assert "transcript" in blocks[0]

    def test_get_asset_document_returns_document_block(self) -> None:
        """get_asset with document asset → DocumentBlock."""
        from uuid import uuid4

        from src.modules.copilot.application.orchestrator.chat import _tool_result_to_block

        asset_id = str(uuid4())
        result_json = json.dumps(
            {
                "asset_id": asset_id,
                "public_url": "https://cdn.example.com/doc.pdf",
                "mime": "application/pdf",
                "kind": "document",
                "filename": "report.pdf",
                "description": "Annual report",
            }
        )
        blocks = _tool_result_to_block("get_asset", result_json)

        assert blocks is not None
        assert len(blocks) == 1
        assert blocks[0]["type"] == "document"
        assert blocks[0]["filename"] == "report.pdf"

    def test_get_asset_video_returns_video_block(self) -> None:
        """get_asset with video asset → VideoBlock."""
        from uuid import uuid4

        from src.modules.copilot.application.orchestrator.chat import _tool_result_to_block

        asset_id = str(uuid4())
        result_json = json.dumps(
            {
                "asset_id": asset_id,
                "public_url": "https://cdn.example.com/clip.mp4",
                "mime": "video/mp4",
                "kind": "video",
                "filename": "promo.mp4",
                "description": "Promo video",
            }
        )
        blocks = _tool_result_to_block("get_asset", result_json)

        assert blocks is not None
        assert len(blocks) == 1
        assert blocks[0]["type"] == "video"

    def test_unknown_tool_returns_none(self) -> None:
        """Tools not mapped to blocks return None (emit only legacy tool_result)."""
        from src.modules.copilot.application.orchestrator.chat import _tool_result_to_block

        blocks = _tool_result_to_block("analyze_offer_ladder", '{"result": "ok"}')
        assert blocks is None

    def test_invalid_json_returns_none(self) -> None:
        """Malformed JSON from tool → None (safe fallback, no crash)."""
        from src.modules.copilot.application.orchestrator.chat import _tool_result_to_block

        blocks = _tool_result_to_block("search_knowledge_base", "not-json")
        assert blocks is None

    def test_empty_list_returns_empty_list(self) -> None:
        """search_knowledge_base returning empty list → empty list (not None)."""
        from src.modules.copilot.application.orchestrator.chat import _tool_result_to_block

        blocks = _tool_result_to_block("search_knowledge_base", "[]")
        assert blocks == []

    def test_search_assets_not_found_error_returns_none(self) -> None:
        """search_assets error response → None."""
        from src.modules.copilot.application.orchestrator.chat import _tool_result_to_block

        blocks = _tool_result_to_block("search_assets", '{"error": "not_found"}')
        assert blocks is None


# ── Tests: _handle_tool_end v2 block_append events ────────────────────────────


class TestHandleToolEndV2BlockAppend:
    """Verify _handle_tool_end emits block_append events for mapped tool results."""

    @pytest.fixture()
    def orch(self) -> CopilotOrchestrator:
        return _make_orchestrator()

    def test_search_knowledge_base_emits_block_append_citation(self, orch: CopilotOrchestrator) -> None:
        """search_knowledge_base tool result → block_append with CitationBlock."""
        from uuid import uuid4

        msg_id = str(uuid4())
        acc = _StreamAccumulator()

        citation_raw = json.dumps(
            [
                {
                    "type": "citation",
                    "source": "Doc: playbook.md",
                    "snippet": "Texto relevante",
                    "score": 0.85,
                }
            ]
        )
        event = {
            "event": "on_tool_end",
            "name": "search_knowledge_base",
            "data": {"output": citation_raw},
        }

        # _handle_tool_end_v2 is the new method that emits block_append
        result = orch._handle_tool_end_v2(event, [], {}, acc, msg_id)

        # Must include legacy tool_result
        assert "tool_result" in result

        # Must include block_append for citation
        frames = [f + "\n\n" for f in result.split("\n\n") if f.strip()]
        event_types = [_parse_sse(f)["event"] for f in frames]
        assert "block_append" in event_types

        # The block_append must carry a CitationBlock
        append_frames = [_parse_sse(f) for f in frames if _parse_sse(f)["event"] == "block_append"]
        assert len(append_frames) == 1
        block = append_frames[0]["data"]["block"]
        assert block["type"] == "citation"

    def test_search_assets_image_emits_block_append_image(self, orch: CopilotOrchestrator) -> None:
        """search_assets (image) → block_append with ImageBlock."""
        from uuid import uuid4

        msg_id = str(uuid4())
        acc = _StreamAccumulator()
        asset_id = str(uuid4())

        assets_raw = json.dumps(
            [
                {
                    "asset_id": asset_id,
                    "public_url": "https://cdn.example.com/img.png",
                    "mime": "image/png",
                    "kind": "image",
                    "filename": "hero.png",
                    "description": "Hero image",
                }
            ]
        )
        event = {
            "event": "on_tool_end",
            "name": "search_assets",
            "data": {"output": assets_raw},
        }

        result = orch._handle_tool_end_v2(event, [], {}, acc, msg_id)

        frames = [f + "\n\n" for f in result.split("\n\n") if f.strip()]
        event_types = [_parse_sse(f)["event"] for f in frames]
        assert "block_append" in event_types

        append_frame = next(_parse_sse(f) for f in frames if _parse_sse(f)["event"] == "block_append")
        assert append_frame["data"]["block"]["type"] == "image"
        assert append_frame["data"]["block"]["asset_id"] == asset_id

    def test_unknown_tool_no_block_append(self, orch: CopilotOrchestrator) -> None:
        """Tools not mapped to blocks emit only legacy tool_result, no block_append."""
        from uuid import uuid4

        msg_id = str(uuid4())
        acc = _StreamAccumulator()

        event = {
            "event": "on_tool_end",
            "name": "analyze_offer_ladder",
            "data": {"output": "Análisis completo"},
        }

        result = orch._handle_tool_end_v2(event, [], {}, acc, msg_id)

        frames = [f + "\n\n" for f in result.split("\n\n") if f.strip()]
        event_types = [_parse_sse(f)["event"] for f in frames]
        assert "block_append" not in event_types
        assert "tool_result" in event_types

    def test_tool_call_trace_event_records_duration_ms(self, orch: CopilotOrchestrator) -> None:
        """TP4-B3 regression — tool_call trace event must carry the
        per-tool elapsed time so /trazas + DeepEval latency targets
        are observable. The recorder API supports ``duration_ms``;
        before this fix the chat orchestrator never populated it."""
        from uuid import uuid4

        msg_id = str(uuid4())
        run_id = str(uuid4())
        recorded: list[dict[str, Any]] = []

        class _Recorder:
            def record(self, **kwargs: Any) -> Any:
                recorded.append(kwargs)
                return uuid4()

        acc = _StreamAccumulator()
        acc.recorder = _Recorder()
        # Simulate the on_tool_start branch having captured the start instant.
        import time

        acc.tool_started_at[run_id] = time.monotonic() - 0.250  # 250ms ago

        event = {
            "event": "on_tool_end",
            "name": "ask_tenant_data",
            "run_id": run_id,
            "data": {"output": '{"status": "ok", "kind": "lead_count", "answer": "x"}'},
        }
        orch._handle_tool_end_v2(event, [], {}, acc, msg_id)

        tool_call_rows = [r for r in recorded if r.get("event_type") == "tool_call"]
        assert tool_call_rows, "expected exactly one tool_call recorder.record call"
        row = tool_call_rows[0]
        assert isinstance(row.get("duration_ms"), int), row
        assert row["duration_ms"] >= 200, row  # ~250ms with allowance for clock jitter
        # Bookkeeping — start entry consumed so it never leaks across turns.
        assert run_id not in acc.tool_started_at

    def test_block_append_added_to_accumulator_emitted_blocks(self, orch: CopilotOrchestrator) -> None:
        """block_append blocks are added to acc.emitted_blocks for message_end."""
        from uuid import uuid4

        msg_id = str(uuid4())
        acc = _StreamAccumulator()

        citation_raw = json.dumps(
            [
                {
                    "type": "citation",
                    "source": "Doc: test.md",
                    "snippet": "Snippet",
                    "score": 0.5,
                }
            ]
        )
        event = {
            "event": "on_tool_end",
            "name": "search_knowledge_base",
            "data": {"output": citation_raw},
        }

        orch._handle_tool_end_v2(event, [], {}, acc, msg_id)

        assert len(acc.emitted_blocks) == 1
        assert acc.emitted_blocks[0]["type"] == "citation"


# ── Tests: ui_action → CardBlock wrap ─────────────────────────────────────────


class TestUiActionToCardBlock:
    """Verify ui_action tool results are wrapped as CardBlock in v2."""

    @pytest.fixture()
    def orch(self) -> CopilotOrchestrator:
        return _make_orchestrator()

    def test_ui_action_proposal_emits_block_append_card(self, orch: CopilotOrchestrator) -> None:
        """ui_action with type='proposal' → block_append with CardBlock(card_kind='proposal')."""
        from uuid import uuid4

        msg_id = str(uuid4())
        acc = _StreamAccumulator()

        ui_payload = {
            "type": "proposal",
            "updates": [{"field": "tagline", "value": "Nueva tagline"}],
        }
        tool_output = json.dumps({"result": "ok", "ui_action": ui_payload})
        event = {
            "event": "on_tool_end",
            "name": "mutate_field",
            "data": {"output": tool_output},
        }

        result = orch._handle_tool_end_v2(event, [], {}, acc, msg_id)

        frames = [f + "\n\n" for f in result.split("\n\n") if f.strip()]
        event_types = [_parse_sse(f)["event"] for f in frames]
        assert "ui_action" in event_types  # legacy still fires
        assert "block_append" in event_types  # v2 fires too

        card_frame = next(_parse_sse(f) for f in frames if _parse_sse(f)["event"] == "block_append")
        block = card_frame["data"]["block"]
        assert block["type"] == "card"
        assert block["card_kind"] == "proposal"
        assert block["payload"] == ui_payload

    def test_ui_action_clarify_emits_card_block(self, orch: CopilotOrchestrator) -> None:
        """ui_action clarify → CardBlock with card_kind='clarify'."""
        from uuid import uuid4

        msg_id = str(uuid4())
        acc = _StreamAccumulator()

        ui_payload = {"type": "clarify", "question": "¿Cuál es tu objetivo?"}
        tool_output = json.dumps({"ui_action": ui_payload})
        event = {
            "event": "on_tool_end",
            "name": "some_tool",
            "data": {"output": tool_output},
        }

        result = orch._handle_tool_end_v2(event, [], {}, acc, msg_id)

        frames = [f + "\n\n" for f in result.split("\n\n") if f.strip()]
        card_frames = [_parse_sse(f) for f in frames if _parse_sse(f)["event"] == "block_append"]
        assert len(card_frames) == 1
        assert card_frames[0]["data"]["block"]["card_kind"] == "clarify"


# ── Helper: run orchestrator stream_chat with fake graph ─────────────────────


async def _run_stream_chat(
    orch: CopilotOrchestrator,
    graph_events: list[dict],
) -> list[dict[str, Any]]:
    """Drive stream_chat using a fake async generator for the deep-agent graph."""

    async def fake_graph_stream(state: dict, *, version: str = "v2"):
        for ev in graph_events:
            yield ev

    fake_graph = MagicMock()
    fake_graph.astream_events = fake_graph_stream

    with (
        patch(
            "src.modules.copilot.application.orchestrator.chat.build_deep_agent_graph",
            return_value=fake_graph,
        ),
        patch(
            "src.modules.copilot.application.orchestrator.chat.redis_client",
            None,
        ),
    ):
        raw_frames = [
            frame
            async for frame in orch.stream_chat(
                user_id=MagicMock(),
                tenant_id=MagicMock(),
                message="Test",
            )
        ]

    return _split_frames(raw_frames)


def _make_text_stream_events(texts: list[str]) -> list[dict]:
    """Build a sequence of on_chat_model_stream events from a list of text chunks."""
    events = []
    for text in texts:
        chunk = MagicMock()
        chunk.content = text
        events.append({"event": "on_chat_model_stream", "data": {"chunk": chunk}})
    return events


# ── Tests: stream_chat v2 event ordering ─────────────────────────────────────


class TestStreamChatV2EventOrdering:
    """Integration tests verifying message_start, block_start/delta/end, message_end ordering."""

    @pytest.mark.asyncio
    async def test_message_start_emitted_before_blocks(self) -> None:
        """message_start must precede any block_* event (CONTRACT §6 ordering)."""
        orch = _make_orchestrator()
        events = await _run_stream_chat(orch, _make_text_stream_events(["Respuesta"]))
        event_types = [e["event"] for e in events]

        assert "message_start" in event_types
        assert "block_start" in event_types
        idx_message_start = next(i for i, e in enumerate(events) if e["event"] == "message_start")
        idx_block_start = next(i for i, e in enumerate(events) if e["event"] == "block_start")
        assert idx_message_start < idx_block_start

    @pytest.mark.asyncio
    async def test_text_streaming_emits_only_v2(self) -> None:
        """F8 §5.4 — text streaming emits ONLY block_delta. ``text_chunk`` is gone."""
        orch = _make_orchestrator()
        events = await _run_stream_chat(orch, _make_text_stream_events(["Hola", " mundo"]))
        event_types = [e["event"] for e in events]

        assert "block_delta" in event_types, "v2 block_delta must always be emitted"
        assert "text_chunk" not in event_types, "Legacy text_chunk SSE was removed in F8 §5.4 — it must not be emitted"

    @pytest.mark.asyncio
    async def test_message_end_contains_final_blocks(self) -> None:
        """message_end.blocks contains the finalized text block."""
        orch = _make_orchestrator()
        events = await _run_stream_chat(orch, _make_text_stream_events(["Texto final"]))

        message_end_events = [e for e in events if e["event"] == "message_end"]

        assert len(message_end_events) == 1
        me = message_end_events[0]
        assert "blocks" in me["data"]
        assert len(me["data"]["blocks"]) >= 1
        text_blocks = [b for b in me["data"]["blocks"] if b["type"] == "text"]
        assert len(text_blocks) == 1
        assert "Texto final" in text_blocks[0]["markdown"]

    @pytest.mark.asyncio
    async def test_block_end_precedes_message_end(self) -> None:
        """block_end must occur before message_end (CONTRACT ordering guarantee)."""
        orch = _make_orchestrator()
        events = await _run_stream_chat(orch, _make_text_stream_events(["Hola"]))
        event_types = [e["event"] for e in events]

        assert "block_end" in event_types
        assert "message_end" in event_types
        idx_block_end = max(i for i, e in enumerate(events) if e["event"] == "block_end")
        idx_message_end = next(i for i, e in enumerate(events) if e["event"] == "message_end")
        assert idx_block_end < idx_message_end

    @pytest.mark.asyncio
    async def test_message_end_before_done(self) -> None:
        """message_end must precede done (CONTRACT ordering guarantee)."""
        orch = _make_orchestrator()
        events = await _run_stream_chat(orch, _make_text_stream_events(["Hola"]))
        event_types = [e["event"] for e in events]

        assert "message_end" in event_types
        assert "done" in event_types
        idx_me = next(i for i, e in enumerate(events) if e["event"] == "message_end")
        idx_done = next(i for i, e in enumerate(events) if e["event"] == "done")
        assert idx_me < idx_done
