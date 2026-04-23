"""Regression: emitted_blocks survive the stream → persist → refetch round-trip.

Prior bug: cards emitted during SSE streaming (block_append) were held only
in frontend memory. When ``onDone`` invalidated the React Query cache, the
refetched conversation lost every card because ``_serialize_messages`` only
kept role+content+tool_calls. The UI showed a "flash" of the card followed
by its disappearance as the store was re-hydrated from the stripped data.

Fix: ``_persist_messages`` now accepts ``emitted_blocks`` and attaches them
to the last assistant message. ``decode_message`` already honored incoming
``blocks`` on raw dicts, so the cards survive the round-trip.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from langchain_core.messages import AIMessage, HumanMessage

from src.modules.copilot.application.orchestrator.chat import CopilotOrchestrator


class TestAttachBlocksToLastAssistant:
    def test_attaches_to_last_assistant_message(self) -> None:
        serialized = [
            {"role": "user", "content": "hola"},
            {"role": "assistant", "content": "respuesta"},
        ]
        blocks = [{"id": "b1", "type": "text", "markdown": "respuesta"}]

        CopilotOrchestrator._attach_blocks_to_last_assistant(serialized, blocks)

        assert serialized[1]["blocks"] == blocks
        assert "blocks" not in serialized[0]

    def test_attaches_to_the_final_assistant_when_tool_loop(self) -> None:
        """AI → Tool → AI: only the final AIMessage carries the blocks."""
        serialized = [
            {"role": "user", "content": "extrae"},
            {"role": "assistant", "content": "", "tool_calls": [{"id": "t1", "name": "clarify", "args": {}}]},
            {"role": "tool", "content": "{...}", "tool_call_id": "t1", "name": "clarify"},
            {"role": "assistant", "content": "Noté algo que quiero aclarar."},
        ]
        blocks = [
            {"id": "t", "type": "text", "markdown": "Noté algo..."},
            {"id": "c", "type": "card", "card_kind": "clarify", "payload": {"clarify_items": []}, "status": "pending"},
        ]

        CopilotOrchestrator._attach_blocks_to_last_assistant(serialized, blocks)

        assert serialized[-1]["blocks"] == blocks
        assert "blocks" not in serialized[1]
        assert "blocks" not in serialized[2]

    def test_noop_when_no_assistant(self) -> None:
        serialized = [{"role": "user", "content": "solo user"}]
        blocks = [{"id": "b", "type": "text", "markdown": "orphan"}]

        CopilotOrchestrator._attach_blocks_to_last_assistant(serialized, blocks)

        assert "blocks" not in serialized[0]


class TestPersistMessagesWithBlocks:
    def _make_orchestrator(self) -> CopilotOrchestrator:
        db = MagicMock()
        orch = CopilotOrchestrator(db=db)
        orch.conv_repo = MagicMock()
        orch._cache_history = MagicMock()  # type: ignore[method-assign]
        return orch

    def test_blocks_are_attached_when_emitted(self) -> None:
        from uuid import uuid4

        orch = self._make_orchestrator()
        conv_uuid = uuid4()
        tenant_id = uuid4()
        existing_conv = MagicMock(title=None, messages=[])

        blocks = [
            {"id": "t", "type": "text", "markdown": "hola"},
            {
                "id": "c",
                "type": "card",
                "card_kind": "clarify",
                "payload": {"type": "clarify_card", "clarify_items": []},
                "status": "pending",
            },
        ]

        orch._persist_messages(
            conv_uuid,
            tenant_id,
            str(conv_uuid),
            "extrae de esa URL",
            "hola",
            [AIMessage(content="hola")],
            existing_conv,
            emitted_blocks=blocks,
        )

        args, _ = orch.conv_repo.append_messages.call_args
        _, _, new_messages = args
        assert new_messages[-1]["role"] == "assistant"
        assert new_messages[-1]["blocks"] == blocks

    def test_no_blocks_when_emitted_is_empty(self) -> None:
        from uuid import uuid4

        orch = self._make_orchestrator()
        conv_uuid = uuid4()
        tenant_id = uuid4()
        existing_conv = MagicMock(title=None, messages=[])

        orch._persist_messages(
            conv_uuid,
            tenant_id,
            str(conv_uuid),
            "hola",
            "respuesta",
            [AIMessage(content="respuesta")],
            existing_conv,
            emitted_blocks=[],
        )

        args, _ = orch.conv_repo.append_messages.call_args
        _, _, new_messages = args
        assert "blocks" not in new_messages[-1]

    def test_backward_compatible_call_without_emitted_blocks(self) -> None:
        """Callers that don't pass emitted_blocks keep the previous behavior."""
        from uuid import uuid4

        orch = self._make_orchestrator()
        conv_uuid = uuid4()
        tenant_id = uuid4()
        existing_conv = MagicMock(title=None, messages=[])

        orch._persist_messages(
            conv_uuid,
            tenant_id,
            str(conv_uuid),
            "hola",
            "respuesta",
            [HumanMessage(content="hola"), AIMessage(content="respuesta")],
            existing_conv,
        )

        args, _ = orch.conv_repo.append_messages.call_args
        _, _, new_messages = args
        for msg in new_messages:
            assert "blocks" not in msg
