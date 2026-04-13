"""Tests for CopilotState and ClientContext type definitions."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from src.modules.copilot.application.orchestrator.state import (
    create_initial_copilot_state,
)

if TYPE_CHECKING:
    from src.modules.copilot.application.orchestrator.state import (
        ClientContext,
        CopilotState,
        FocusContext,
    )


class TestFocusContext:
    """Tests for the FocusContext TypedDict."""

    def test_focus_context_with_entity_id(self) -> None:
        ctx: FocusContext = {
            "domain": "offer",
            "entity_id": "730e7f7a-43b9-495e-bf05-49700135d324",
        }
        assert ctx["domain"] == "offer"
        assert ctx["entity_id"] == "730e7f7a-43b9-495e-bf05-49700135d324"

    def test_focus_context_without_entity_id(self) -> None:
        ctx: FocusContext = {"domain": "brand"}
        assert ctx["domain"] == "brand"
        assert "entity_id" not in ctx

    def test_client_context_with_focus(self) -> None:
        ctx: ClientContext = {
            "current_route": "/offer-studio/offer/123",
            "selected_fields": [],
            "form_data": {},
            "locale": "es",
            "focus": {"domain": "offer", "entity_id": "123"},
        }
        assert ctx["focus"]["domain"] == "offer"

    def test_client_context_with_interview(self) -> None:
        ctx: ClientContext = {
            "current_route": "/offer-studio/offer/123",
            "selected_fields": [],
            "form_data": {},
            "locale": "es",
            "interview_session_id": "abc-def-123",
        }
        assert ctx["interview_session_id"] == "abc-def-123"

    def test_client_context_backward_compatible(self) -> None:
        """Existing code that doesn't send focus/interview still works."""
        ctx: ClientContext = {
            "current_route": "/brand-studio",
            "selected_fields": [],
            "form_data": {},
            "locale": "es",
        }
        assert ctx.get("focus") is None
        assert ctx.get("interview_session_id") is None


class TestCopilotStateFocusEntityData:
    """Tests for the focus_entity_data field in CopilotState."""

    def test_create_initial_state_has_focus_entity_data_none(self) -> None:
        """create_initial_copilot_state must initialise focus_entity_data to None."""
        state = create_initial_copilot_state(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            conversation_id="conv-001",
        )
        assert "focus_entity_data" in state
        assert state["focus_entity_data"] is None

    def test_focus_entity_data_can_hold_dict(self) -> None:
        """focus_entity_data accepts arbitrary dict payloads."""
        state = create_initial_copilot_state(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            conversation_id="conv-002",
        )
        payload: dict = {"entity_type": "offer", "name": "Pack Premium", "price": 497}
        state["focus_entity_data"] = payload
        assert state["focus_entity_data"]["entity_type"] == "offer"
        assert state["focus_entity_data"]["price"] == 497

    def test_focus_entity_data_can_be_none(self) -> None:
        """focus_entity_data can be explicitly set to None (no active focus)."""
        state = create_initial_copilot_state(
            user_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            conversation_id="conv-003",
        )
        state["focus_entity_data"] = None
        assert state["focus_entity_data"] is None
