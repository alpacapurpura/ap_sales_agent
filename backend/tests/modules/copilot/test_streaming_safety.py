"""Tests for stream-level safety guards in CopilotOrchestrator.

Two non-negotiable invariants live here:

1. ``recursion_limit`` is configured (overridable via env var) and reaches
   LangGraph's ``astream_events(config=...)`` so production can tune it
   without code changes. Default 25 (LangGraph's own default) preserves
   existing behaviour.

2. Tool-call dedup: when the agent emits the same ``(tool_name, args)``
   pair more than ``COPILOT_TOOL_CALL_DEDUP_THRESHOLD`` times in a turn,
   the orchestrator must inject an explicit signal to break the loop
   instead of letting it run to ``GraphRecursionError``.

The 2026-04-27 incident (conversation fbc79125-…) hit GraphRecursionError
because the deep-agent kept calling ``get_module_data(module='offer',
section=...)`` with rotating section args; nothing capped it. These
tests are the regression net so the bug can't return silently.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest

from luana_core_copilot.application.orchestrator.chat import (
    COPILOT_RECURSION_LIMIT,
    CopilotOrchestrator,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


# ── Helpers ──────────────────────────────────────────────────────────


async def _fake_stream_short(
    state: dict,
    *,
    version: str = "v2",
    config: dict | None = None,
) -> AsyncGenerator[dict, None]:
    """A minimal stream that records the config passed to astream_events."""
    _CAPTURED_CONFIG.clear()
    if config is not None:
        _CAPTURED_CONFIG.update(config)
    from langchain_core.messages import AIMessage

    yield {
        "event": "on_chat_model_stream",
        "data": {"chunk": MagicMock(content="ok")},
    }
    yield {
        "event": "on_chat_model_end",
        "data": {"output": AIMessage(content="ok")},
    }


_CAPTURED_CONFIG: dict[str, Any] = {}


def _parse_sse_events(sse_strings: list[str]) -> list[dict[str, Any]]:
    events = []
    for sse in sse_strings:
        lines = sse.strip().split("\n")
        event_type: str | None = None
        data: Any = None
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
def orchestrator() -> CopilotOrchestrator:
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
        return CopilotOrchestrator(MagicMock())


def _setup_orchestrator_mocks(orchestrator: CopilotOrchestrator) -> MagicMock:
    mock_repo = MagicMock()
    mock_conv = MagicMock()
    mock_conv.title = None
    mock_conv.messages = []
    mock_repo.get_by_id.return_value = mock_conv
    orchestrator.conv_repo = mock_repo
    return mock_repo


# ── Tests — recursion_limit setting ─────────────────────────────────


class TestRecursionLimitSetting:
    """Fix 2 — COPILOT_RECURSION_LIMIT configurable + reaches astream_events."""

    def test_default_recursion_limit_value(self) -> None:
        """Default must remain LangGraph's own default (25) so the patch
        does not silently relax existing behaviour."""
        assert COPILOT_RECURSION_LIMIT == 25

    @pytest.mark.parametrize(
        "env_value,expected",
        [("12", 12), ("40", 40), ("25", 25)],
    )
    def test_recursion_limit_configurable_via_env(
        self,
        env_value: str,
        expected: int,
    ) -> None:
        import importlib

        import src.modules.copilot.application.orchestrator.chat as chat_mod

        with patch.dict(
            "os.environ",
            {"COPILOT_RECURSION_LIMIT": env_value},
        ):
            importlib.reload(chat_mod)
            assert expected == chat_mod.COPILOT_RECURSION_LIMIT
        importlib.reload(chat_mod)

    async def test_recursion_limit_reaches_astream_events_config(
        self,
        orchestrator: CopilotOrchestrator,
    ) -> None:
        """The configured limit must be passed through to LangGraph so a
        future GraphRecursionError fires at the configured cap, not the
        library default. Captures the ``config`` kwarg from astream_events.
        """
        with (
            patch(
                "luana_core_copilot.application.orchestrator.chat.build_deep_agent_graph",
            ) as mock_build_graph,
            patch(
                "luana_core_copilot.application.orchestrator.chat.COPILOT_RECURSION_LIMIT",
                17,
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
            mock_build_graph.return_value.astream_events = _fake_stream_short

            await _collect_sse_events(orchestrator)

            # The orchestrator already passes other keys (callbacks etc.) via
            # ``acc.obs.langchain_config()``. We only assert recursion_limit
            # was merged in — anything else is out of scope for this test.
            assert _CAPTURED_CONFIG.get("recursion_limit") == 17


# ── Tests — graph recursion error path emits SSE error ──────────────


class TestGraphRecursionErrorHandling:
    """Fix 4 — partial persistence + Fix 5 — turn_end status — share the
    same fault path. We start with the simplest invariant: when LangGraph
    raises ``GraphRecursionError`` the user must receive a friendly SSE
    error event (not a raw exception leak)."""

    async def test_graph_recursion_error_emits_sse_error(
        self,
        orchestrator: CopilotOrchestrator,
    ) -> None:
        from langgraph.errors import GraphRecursionError

        async def _raise_recursion(
            state: dict,
            *,
            version: str = "v2",
            config: dict | None = None,
        ) -> AsyncGenerator[dict, None]:
            # Yield once so the stream is "live" before raising.
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": MagicMock(content="Empezando")},
            }
            err_msg = "Recursion limit of 25 reached"
            raise GraphRecursionError(err_msg)

        with (
            patch(
                "luana_core_copilot.application.orchestrator.chat.build_deep_agent_graph",
            ) as mock_build_graph,
            patch(
                "luana_core_copilot.application.orchestrator.chat.redis_client",
                None,
            ),
            patch(
                "luana_core_copilot.application.orchestrator.chat.ConversationRepository",
            ) as mock_repo_cls,
        ):
            mock_repo_cls.return_value = _setup_orchestrator_mocks(orchestrator)
            mock_build_graph.return_value.astream_events = _raise_recursion

            events = await _collect_sse_events(orchestrator)
            parsed = _parse_sse_events(events)
            event_types = [e["event"] for e in parsed]

            assert "error" in event_types
            error_events = [e for e in parsed if e["event"] == "error"]
            assert len(error_events) >= 1
            # Spanish neutro user-facing message — never raw exception text.
            msg = error_events[0]["data"]["message"].lower()
            assert "recursion" not in msg  # internal detail must not leak
            assert "error" in msg or "intenta" in msg or "limite" in msg or "límite" in msg


# ── Tests — partial persistence on error (Fix 4) ────────────────────


class TestPartialPersistenceOnError:
    """Fix 4 — when the stream raises (recursion / loop / unknown), the
    accumulator must NOT be wiped before persistence so the user keeps
    the user-message + plan-card + tool outputs already accumulated.

    Pre-fix behaviour (chat.py:1078-1080): ``acc.full_response = ""``
    and ``acc.messages = []`` happened inside the catch-all Exception
    block, so the recursion-error path persisted an empty conversation
    even though the LLM had already done useful work.
    """

    async def test_recursion_error_preserves_partial_messages(
        self,
        orchestrator: CopilotOrchestrator,
    ) -> None:
        """Reproduces the 2026-04-27 incident: read_document + write_todos
        ran successfully, then a recursion error fired. Partial state must
        survive into ``_persist_messages``."""
        from langchain_core.messages import AIMessage, ToolMessage
        from langgraph.errors import GraphRecursionError

        async def _useful_work_then_recursion(
            state: dict,
            *,
            version: str = "v2",
            config: dict | None = None,
        ) -> AsyncGenerator[dict, None]:
            # Some honest accumulation first.
            yield {
                "event": "on_chat_model_end",
                "data": {
                    "output": AIMessage(
                        content="",
                        tool_calls=[
                            {
                                "name": "read_document",
                                "args": {"asset_id": "abc"},
                                "id": "tc:1",
                            },
                        ],
                    ),
                },
            }
            yield {
                "event": "on_tool_end",
                "name": "read_document",
                "data": {
                    "input": {"asset_id": "abc"},
                    "output": ToolMessage(
                        content="contenido leído",
                        tool_call_id="tc:1",
                    ),
                },
            }
            # Then graph blows up.
            err_msg = "Recursion limit of 25 reached"
            raise GraphRecursionError(err_msg)

        captured: dict[str, Any] = {}

        original_persist = orchestrator._persist_messages

        def _spy_persist(*args, **kwargs):  # type: ignore[no-untyped-def]
            # Positional signature: (conv_uuid, tenant_id, conv_id, user_msg,
            # full_response, messages, existing_conv, emitted_blocks=...)
            captured["full_response"] = args[4]
            captured["messages"] = args[5]
            captured["user_msg"] = args[3]
            return original_persist(*args, **kwargs)

        with (
            patch(
                "luana_core_copilot.application.orchestrator.chat.build_deep_agent_graph",
            ) as mock_build_graph,
            patch(
                "luana_core_copilot.application.orchestrator.chat.redis_client",
                None,
            ),
            patch(
                "luana_core_copilot.application.orchestrator.chat.ConversationRepository",
            ) as mock_repo_cls,
            patch.object(orchestrator, "_persist_messages", side_effect=_spy_persist),
        ):
            mock_repo_cls.return_value = _setup_orchestrator_mocks(orchestrator)
            mock_build_graph.return_value.astream_events = _useful_work_then_recursion

            await _collect_sse_events(orchestrator, message="extrae el doc")

        # Persistence MUST have been called even though the graph blew up.
        assert "messages" in captured, "_persist_messages never called"
        # And the messages list must NOT be empty — we accumulated a real
        # ToolMessage before the failure. Pre-fix: empty list.
        msgs = captured["messages"]
        assert len(msgs) >= 1, f"expected partial messages preserved, got {msgs!r}"
        tool_msgs = [m for m in msgs if isinstance(m, ToolMessage) or getattr(m, "type", "") == "tool"]
        assert tool_msgs, "expected the read_document ToolMessage to survive"
        # The user message text must reach persistence too — losing it
        # leaves the conversation looking blank on refresh.
        assert captured["user_msg"] == "extrae el doc"


# ── Tests — anti-loop dedup wiring (Fix 3) ──────────────────────────


class TestToolCallDedupWiring:
    """End-to-end wiring of ToolCallDedupTracker into _handle_tool_end_v2.

    Replays the 2026-04-27 incident in miniature: a fake graph emits the
    same ``get_module_data(module='offer', section='psychology')`` call
    five times. Without the guard, this would be 5 wasted LLM round-trips
    plus eventual GraphRecursionError. With the guard:

    * Hits 1-2 → pass through unchanged.
    * Hit 3   → ToolMessage in accumulator gains the anti-loop directive.
    * Hit 5   → ToolCallLoopDetected raised; orchestrator emits SSE error
                instead of letting the loop continue.
    """

    async def test_warn_directive_injected_into_tool_message_at_threshold(
        self,
        orchestrator: CopilotOrchestrator,
    ) -> None:
        from langchain_core.messages import AIMessage, ToolMessage

        async def _three_identical_calls(
            state: dict,
            *,
            version: str = "v2",
            config: dict | None = None,
        ) -> AsyncGenerator[dict, None]:
            args = {"module": "offer", "section": "psychology"}
            for i in range(3):
                # AIMessage carrying the tool_call binding.
                yield {
                    "event": "on_chat_model_end",
                    "data": {
                        "output": AIMessage(
                            content="",
                            tool_calls=[
                                {
                                    "name": "get_module_data",
                                    "args": args,
                                    "id": f"tc:{i}",
                                },
                            ],
                        ),
                    },
                }
                yield {
                    "event": "on_tool_end",
                    "name": "get_module_data",
                    "data": {
                        "input": args,
                        "output": ToolMessage(
                            content=f"## Ofertas (call {i})",
                            tool_call_id=f"tc:{i}",
                        ),
                    },
                }
            # Final assistant text so the turn ends cleanly without raising.
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": MagicMock(content="ok")},
            }

        with (
            patch(
                "luana_core_copilot.application.orchestrator.chat.build_deep_agent_graph",
            ) as mock_build_graph,
            patch(
                "luana_core_copilot.application.orchestrator.chat.redis_client",
                None,
            ),
            patch(
                "luana_core_copilot.application.orchestrator.chat.ConversationRepository",
            ) as mock_repo_cls,
        ):
            mock_repo_cls.return_value = _setup_orchestrator_mocks(orchestrator)
            mock_build_graph.return_value.astream_events = _three_identical_calls

            captured_acc_messages: list = []
            real_handler = orchestrator._handle_tool_end_v2  # type: ignore[attr-defined]

            def _spy_handler(event, accumulated_messages, last_tool_call_ids, acc, msg_id):  # type: ignore[no-untyped-def]
                result = real_handler(event, accumulated_messages, last_tool_call_ids, acc, msg_id)
                # Snapshot AFTER the handler ran so the dedup wrap, if any,
                # is visible.
                captured_acc_messages.append(list(accumulated_messages))
                return result

            with patch.object(
                orchestrator,
                "_handle_tool_end_v2",
                side_effect=_spy_handler,
            ):
                await _collect_sse_events(orchestrator)

            # Latest snapshot reflects the final accumulator state. The
            # third ToolMessage in there must carry the directive.
            assert captured_acc_messages, "tool_end handler never ran"
            final = captured_acc_messages[-1]
            tool_messages = [m for m in final if isinstance(m, ToolMessage)]
            assert len(tool_messages) >= 3, f"expected ≥3 tool msgs, got {len(tool_messages)}"
            third = tool_messages[2]
            assert "GUARD ANTI-LOOP" in third.content
            assert "get_module_data" in third.content

    async def test_hard_limit_aborts_with_friendly_sse_error(
        self,
        orchestrator: CopilotOrchestrator,
    ) -> None:
        from langchain_core.messages import AIMessage, ToolMessage

        async def _five_identical_calls(
            state: dict,
            *,
            version: str = "v2",
            config: dict | None = None,
        ) -> AsyncGenerator[dict, None]:
            args = {"module": "offer", "section": "psychology"}
            for i in range(6):
                yield {
                    "event": "on_chat_model_end",
                    "data": {
                        "output": AIMessage(
                            content="",
                            tool_calls=[
                                {
                                    "name": "get_module_data",
                                    "args": args,
                                    "id": f"tc:{i}",
                                },
                            ],
                        ),
                    },
                }
                yield {
                    "event": "on_tool_end",
                    "name": "get_module_data",
                    "data": {
                        "input": args,
                        "output": ToolMessage(
                            content=f"## Ofertas (call {i})",
                            tool_call_id=f"tc:{i}",
                        ),
                    },
                }

        with (
            patch(
                "luana_core_copilot.application.orchestrator.chat.build_deep_agent_graph",
            ) as mock_build_graph,
            patch(
                "luana_core_copilot.application.orchestrator.chat.redis_client",
                None,
            ),
            patch(
                "luana_core_copilot.application.orchestrator.chat.ConversationRepository",
            ) as mock_repo_cls,
        ):
            mock_repo_cls.return_value = _setup_orchestrator_mocks(orchestrator)
            mock_build_graph.return_value.astream_events = _five_identical_calls

            events = await _collect_sse_events(orchestrator)
            parsed = _parse_sse_events(events)
            event_types = [e["event"] for e in parsed]

            # Loop must be aborted with a user-facing SSE error.
            assert "error" in event_types
            error_msg = next(e["data"]["message"] for e in parsed if e["event"] == "error").lower()
            # Internal mechanism must not leak; user sees a friendly message.
            assert "tool_call_loop" not in error_msg
            assert "guard" not in error_msg
            assert "intenta" in error_msg or "error" in error_msg or "limite" in error_msg or "límite" in error_msg


# Required to silence unused-import lint when running file standalone.
_ = asyncio
