"""Tests for LLM streaming timeout in CopilotOrchestrator."""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest

from luana_core_copilot.api.dto import SSEEvent
from luana_core_copilot.application.orchestrator.chat import (
    COPILOT_STREAM_TIMEOUT_SECONDS,
    CopilotOrchestrator,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


# ── Helpers ──────────────────────────────────────────────────────────


async def _fake_stream_events_slow(
    state: dict,
    *,
    version: str = "v2",
    config: dict | None = None,
) -> AsyncGenerator[dict, None]:
    """Simulate a stream that hangs after emitting a few chunks."""
    # Emit two chunks quickly
    yield {
        "event": "on_chat_model_stream",
        "data": {"chunk": MagicMock(content="Hola, ")},
    }
    yield {
        "event": "on_chat_model_stream",
        "data": {"chunk": MagicMock(content="esto es ")},
    }
    # Then hang indefinitely
    await asyncio.sleep(3600)


async def _fake_stream_events_fast(
    state: dict,
    *,
    version: str = "v2",
    config: dict | None = None,
) -> AsyncGenerator[dict, None]:
    """Simulate a fast stream that completes before timeout."""
    from langchain_core.messages import AIMessage

    yield {
        "event": "on_chat_model_stream",
        "data": {"chunk": MagicMock(content="Respuesta rápida")},
    }
    yield {
        "event": "on_chat_model_end",
        "data": {"output": AIMessage(content="Respuesta rápida")},
    }


def _parse_sse_events(sse_strings: list[str]) -> list[dict[str, Any]]:
    """Parse SSE strings into dicts with event type and data."""
    events = []
    for sse in sse_strings:
        lines = sse.strip().split("\n")
        event_type = None
        data = None
        for line in lines:
            if line.startswith("event: "):
                event_type = line[7:]
            elif line.startswith("data: "):
                data = json.loads(line[6:])
        if event_type and data is not None:
            events.append({"event": event_type, "data": data})
    return events


async def _collect_sse_events(
    orchestrator: CopilotOrchestrator,
    message: str = "Hola",
) -> list[str]:
    """Collect all SSE events from stream_chat into a list."""
    return [
        sse
        async for sse in orchestrator.stream_chat(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            message=message,
        )
    ]


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture()
def mock_db() -> MagicMock:
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture()
def orchestrator(mock_db: MagicMock) -> CopilotOrchestrator:
    """Create orchestrator with mocked dependencies."""
    with patch(
        "luana_core_copilot.application.orchestrator.chat.ConversationRepository",
    ) as mock_repo_cls:
        mock_repo = MagicMock()
        mock_conv = MagicMock()
        mock_conv.title = None
        mock_conv.messages = []
        mock_repo.get_by_id.return_value = mock_conv
        mock_repo.create.return_value = mock_conv
        mock_repo_cls.return_value = mock_repo

        orch = CopilotOrchestrator(mock_db)
    return orch


def _setup_orchestrator_mocks(orchestrator: CopilotOrchestrator) -> MagicMock:
    """Set up common mocks for orchestrator tests. Returns mock_repo."""
    mock_repo = MagicMock()
    mock_conv = MagicMock()
    mock_conv.title = None
    mock_conv.messages = []
    mock_repo.get_by_id.return_value = mock_conv
    orchestrator.conv_repo = mock_repo
    return mock_repo


# ── Tests ────────────────────────────────────────────────────────────


class TestStreamingTimeout:
    """Tests for LLM streaming timeout behavior."""

    def test_default_timeout_value(self) -> None:
        """Default timeout should be 60 seconds."""
        assert COPILOT_STREAM_TIMEOUT_SECONDS == 60

    @pytest.mark.parametrize("env_value,expected", [("30", 30), ("120", 120), ("10", 10)])
    def test_timeout_configurable_via_env(
        self,
        env_value: str,
        expected: int,
    ) -> None:
        """COPILOT_STREAM_TIMEOUT_SECONDS should be configurable via env var."""
        import importlib

        import src.modules.copilot.application.orchestrator.chat as chat_mod

        with patch.dict(
            "os.environ",
            {"COPILOT_STREAM_TIMEOUT_SECONDS": env_value},
        ):
            importlib.reload(chat_mod)
            assert expected == chat_mod.COPILOT_STREAM_TIMEOUT_SECONDS

        # Restore default
        importlib.reload(chat_mod)

    async def test_timeout_emits_error_event(self, orchestrator: CopilotOrchestrator) -> None:
        """When LLM streaming times out, an SSE error event must be emitted."""
        with (
            patch(
                "luana_core_copilot.application.orchestrator.chat.build_deep_agent_graph",
            ) as mock_build_graph,
            patch(
                "luana_core_copilot.application.orchestrator.chat.COPILOT_STREAM_TIMEOUT_SECONDS",
                0.1,  # 100ms timeout for fast test
            ),
            patch(
                "luana_core_copilot.application.orchestrator.chat.redis_client",
                None,
            ),
            patch(
                "luana_core_copilot.application.orchestrator.chat.ConversationRepository",
            ) as mock_repo_cls,
        ):
            mock_repo_cls.return_value = _setup_orchestrator_mocks(orchestrator)

            mock_build_graph.return_value.astream_events = _fake_stream_events_slow

            events = await _collect_sse_events(orchestrator)
            parsed = _parse_sse_events(events)
            event_types = [e["event"] for e in parsed]

            # Must contain an error event
            assert "error" in event_types, f"Expected error event, got: {event_types}"

            # Error event must have the timeout message
            error_events = [e for e in parsed if e["event"] == "error"]
            assert len(error_events) == 1
            error_msg = error_events[0]["data"]["message"]
            assert "timeout" in error_msg.lower() or "tiempo" in error_msg.lower()

    async def test_timeout_preserves_partial_response(
        self,
        orchestrator: CopilotOrchestrator,
    ) -> None:
        """Partial text chunks emitted before timeout must still be received."""
        with (
            patch(
                "luana_core_copilot.application.orchestrator.chat.build_deep_agent_graph",
            ) as mock_build_graph,
            patch(
                "luana_core_copilot.application.orchestrator.chat.COPILOT_STREAM_TIMEOUT_SECONDS",
                0.1,
            ),
            patch(
                "luana_core_copilot.application.orchestrator.chat.redis_client",
                None,
            ),
            patch(
                "luana_core_copilot.application.orchestrator.chat.ConversationRepository",
            ) as mock_repo_cls,
        ):
            mock_repo_cls.return_value = _setup_orchestrator_mocks(orchestrator)

            mock_build_graph.return_value.astream_events = _fake_stream_events_slow

            events = await _collect_sse_events(orchestrator)
            parsed = _parse_sse_events(events)
            # F8 §5.4 — block_delta is the canonical render path now.
            partial_chunks = [e["data"]["delta"]["markdown"] for e in parsed if e["event"] == "block_delta"]

            # Partial chunks should be preserved
            assert len(partial_chunks) >= 1
            partial_text = "".join(partial_chunks)
            assert "Hola, " in partial_text

    async def test_no_timeout_on_fast_response(
        self,
        orchestrator: CopilotOrchestrator,
    ) -> None:
        """Fast responses should complete normally without timeout error."""
        with (
            patch(
                "luana_core_copilot.application.orchestrator.chat.build_deep_agent_graph",
            ) as mock_build_graph,
            patch(
                "luana_core_copilot.application.orchestrator.chat.COPILOT_STREAM_TIMEOUT_SECONDS",
                5,
            ),
            patch(
                "luana_core_copilot.application.orchestrator.chat.redis_client",
                None,
            ),
            patch(
                "luana_core_copilot.application.orchestrator.chat.ConversationRepository",
            ) as mock_repo_cls,
        ):
            mock_repo_cls.return_value = _setup_orchestrator_mocks(orchestrator)

            mock_build_graph.return_value.astream_events = _fake_stream_events_fast

            events = await _collect_sse_events(orchestrator)
            parsed = _parse_sse_events(events)
            event_types = [e["event"] for e in parsed]

            # Should NOT contain an error event
            assert "error" not in event_types
            # Should contain v2 streaming + done
            assert "block_delta" in event_types
            assert "done" in event_types

    async def test_timeout_still_emits_done_event(
        self,
        orchestrator: CopilotOrchestrator,
    ) -> None:
        """Even on timeout, the stream must end with status:done and done events."""
        with (
            patch(
                "luana_core_copilot.application.orchestrator.chat.build_deep_agent_graph",
            ) as mock_build_graph,
            patch(
                "luana_core_copilot.application.orchestrator.chat.COPILOT_STREAM_TIMEOUT_SECONDS",
                0.1,
            ),
            patch(
                "luana_core_copilot.application.orchestrator.chat.redis_client",
                None,
            ),
            patch(
                "luana_core_copilot.application.orchestrator.chat.ConversationRepository",
            ) as mock_repo_cls,
        ):
            mock_repo_cls.return_value = _setup_orchestrator_mocks(orchestrator)

            mock_build_graph.return_value.astream_events = _fake_stream_events_slow

            events = await _collect_sse_events(orchestrator)
            parsed = _parse_sse_events(events)
            event_types = [e["event"] for e in parsed]

            # Must end with done event
            assert "done" in event_types
            # The done event must come after the error event
            error_idx = event_types.index("error")
            done_idx = event_types.index("done")
            assert done_idx > error_idx

    async def test_timeout_persists_partial_response(
        self,
        orchestrator: CopilotOrchestrator,
    ) -> None:
        """On timeout with partial response, the partial text should be persisted."""
        with (
            patch(
                "luana_core_copilot.application.orchestrator.chat.build_deep_agent_graph",
            ) as mock_build_graph,
            patch(
                "luana_core_copilot.application.orchestrator.chat.COPILOT_STREAM_TIMEOUT_SECONDS",
                0.1,
            ),
            patch(
                "luana_core_copilot.application.orchestrator.chat.redis_client",
                None,
            ),
            patch(
                "luana_core_copilot.application.orchestrator.chat.ConversationRepository",
            ) as mock_repo_cls,
        ):
            mock_repo = _setup_orchestrator_mocks(orchestrator)
            mock_repo_cls.return_value = mock_repo

            mock_build_graph.return_value.astream_events = _fake_stream_events_slow

            await _collect_sse_events(orchestrator)

            # _persist_messages should have been called with partial response
            mock_repo.append_messages.assert_called_once()
            call_args = mock_repo.append_messages.call_args
            messages_arg = call_args[0][2]  # 3rd positional arg = new_messages
            # Should have user message + assistant partial response
            assert len(messages_arg) >= 2
            assistant_msgs = [m for m in messages_arg if m.get("role") == "assistant"]
            assert len(assistant_msgs) == 1
            # Partial text should be preserved
            assert "Hola, " in assistant_msgs[0]["content"]


class TestSSEEventErrorFormat:
    """Tests for the SSE error event format consistency."""

    def test_error_event_serializes_correctly(self) -> None:
        """Error SSE events must match the expected wire format."""
        event = SSEEvent(
            event="error",
            data={
                "message": "La respuesta del asistente excedió el tiempo límite. "
                "Tu mensaje parcial se ha conservado. Intenta de nuevo.",
            },
        )
        sse_str = event.to_sse()
        assert "event: error\n" in sse_str
        assert '"message"' in sse_str
        assert "tiempo" in sse_str.lower()
