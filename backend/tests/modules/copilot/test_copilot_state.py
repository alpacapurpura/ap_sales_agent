"""Tests for CopilotState and ClientContext type definitions.

Focus mode was retired on 2026-04-21. This file used to validate the
``FocusContext`` TypedDict and the ``focus_entity_data`` CopilotState field;
both were removed. Remaining coverage: base ``ClientContext`` + interview.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from src.modules.copilot.application.orchestrator.state import (
    create_initial_copilot_state,
)

if TYPE_CHECKING:
    from src.modules.copilot.application.orchestrator.state import ClientContext


class TestClientContext:
    """Tests for the ClientContext TypedDict."""

    def test_client_context_with_interview(self) -> None:
        ctx: ClientContext = {
            "current_route": "/brand-studio/interview",
            "selected_fields": [],
            "form_data": {},
            "locale": "es",
            "interview_session_id": "abc-def-123",
        }
        assert ctx["interview_session_id"] == "abc-def-123"

    def test_client_context_without_interview(self) -> None:
        """Existing code that doesn't send interview still works."""
        ctx: ClientContext = {
            "current_route": "/brand-studio",
            "selected_fields": [],
            "form_data": {},
            "locale": "es",
        }
        assert ctx.get("interview_session_id") is None


class TestCopilotStateDefaults:
    """Tests for ``create_initial_copilot_state`` defaults."""

    def test_initial_state_has_no_focus_field(self) -> None:
        """``focus_entity_data`` was removed; confirm absence."""
        state = create_initial_copilot_state(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            conversation_id="conv-001",
        )
        assert "focus_entity_data" not in state

    def test_initial_state_has_empty_pending_actions(self) -> None:
        state = create_initial_copilot_state(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            conversation_id="conv-002",
        )
        assert state["pending_ui_actions"] == []
        assert state["active_tool_names"] == []
        assert state["active_procedure"] is None
        assert state["error"] is None
