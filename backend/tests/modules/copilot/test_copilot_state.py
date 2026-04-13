"""Tests for CopilotState and ClientContext type definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.modules.copilot.application.orchestrator.state import (
        ClientContext,
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
