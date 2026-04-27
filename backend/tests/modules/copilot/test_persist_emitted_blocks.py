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


class TestDedupeEmittedBlocks:
    """``write_todos`` fires N times per turn — only the last plan_card stays."""

    def test_keeps_last_plan_card_only(self) -> None:
        blocks = [
            {
                "id": "p1",
                "type": "card",
                "card_kind": "plan_card",
                "payload": {"todos": [{"status": "in_progress", "content": "leer"}]},
            },
            {
                "id": "p2",
                "type": "card",
                "card_kind": "plan_card",
                "payload": {"todos": [{"status": "in_progress", "content": "extraer"}]},
            },
            {
                "id": "p3",
                "type": "card",
                "card_kind": "plan_card",
                "payload": {"todos": [{"status": "completed", "content": "extraer"}]},
            },
        ]
        deduped = CopilotOrchestrator._dedupe_emitted_blocks(blocks)
        assert len(deduped) == 1
        assert deduped[0]["id"] == "p3"

    def test_preserves_proposal_alongside_plan_card(self) -> None:
        blocks = [
            {"id": "p1", "type": "card", "card_kind": "plan_card", "payload": {}},
            {"id": "pr", "type": "card", "card_kind": "proposal", "payload": {}},
            {"id": "p2", "type": "card", "card_kind": "plan_card", "payload": {}},
            {"id": "txt", "type": "text", "markdown": "ok"},
        ]
        deduped = CopilotOrchestrator._dedupe_emitted_blocks(blocks)
        assert [b["id"] for b in deduped] == ["pr", "p2", "txt"]

    def test_noop_when_no_repeated_snapshot_kinds(self) -> None:
        blocks = [
            {"id": "txt", "type": "text", "markdown": "hola"},
            {"id": "pr", "type": "card", "card_kind": "proposal", "payload": {}},
        ]
        deduped = CopilotOrchestrator._dedupe_emitted_blocks(blocks)
        assert deduped == blocks

    def test_persist_messages_dedupes_plan_cards(self) -> None:
        """End-to-end: 3 plan_cards in → 1 plan_card persisted."""
        from uuid import uuid4

        db = MagicMock()
        orch = CopilotOrchestrator(db=db)
        orch.conv_repo = MagicMock()
        orch._cache_history = MagicMock()  # type: ignore[method-assign]
        existing_conv = MagicMock(title=None, messages=[])

        plan_cards = [
            {
                "id": f"p{i}",
                "type": "card",
                "card_kind": "plan_card",
                "payload": {"todos": [{"status": "completed" if i == 2 else "in_progress"}]},
            }
            for i in range(3)
        ]
        orch._persist_messages(
            uuid4(),
            uuid4(),
            "conv-id",
            "hola",
            "respuesta",
            [AIMessage(content="respuesta")],
            existing_conv,
            emitted_blocks=plan_cards,
        )

        args, _ = orch.conv_repo.append_messages.call_args
        _, _, new_messages = args
        plan_blocks = [b for b in new_messages[-1]["blocks"] if b.get("card_kind") == "plan_card"]
        assert len(plan_blocks) == 1
        assert plan_blocks[0]["id"] == "p2"


class TestPersistUserAttachments:
    """User-uploaded attachments must round-trip through persistence."""

    def _make_orchestrator(self) -> CopilotOrchestrator:
        db = MagicMock()
        orch = CopilotOrchestrator(db=db)
        orch.conv_repo = MagicMock()
        orch._cache_history = MagicMock()  # type: ignore[method-assign]
        return orch

    def test_user_blocks_attached_to_user_message(self) -> None:
        from uuid import uuid4

        orch = self._make_orchestrator()
        existing_conv = MagicMock(title=None, messages=[])

        user_blocks = [
            {
                "id": "doc-1",
                "type": "document",
                "asset_id": str(uuid4()),
                "filename": "brief.pdf",
                "mime": "application/pdf",
                "size_bytes": 1024,
                "url": "https://assets-dev.nicolify.com/.../brief.pdf",
            },
        ]

        orch._persist_messages(
            uuid4(),
            uuid4(),
            "conv-id",
            "actualiza con esto",
            "ok",
            [AIMessage(content="ok")],
            existing_conv,
            emitted_blocks=[],
            user_blocks=user_blocks,
        )

        args, _ = orch.conv_repo.append_messages.call_args
        _, _, new_messages = args
        user_msg = next(m for m in new_messages if m["role"] == "user")
        assert user_msg["blocks"] == user_blocks

    def test_no_user_blocks_when_none_provided(self) -> None:
        from uuid import uuid4

        orch = self._make_orchestrator()
        existing_conv = MagicMock(title=None, messages=[])

        orch._persist_messages(
            uuid4(),
            uuid4(),
            "conv-id",
            "hola sin attachments",
            "ok",
            [AIMessage(content="ok")],
            existing_conv,
        )

        args, _ = orch.conv_repo.append_messages.call_args
        _, _, new_messages = args
        user_msg = next(m for m in new_messages if m["role"] == "user")
        assert "blocks" not in user_msg
