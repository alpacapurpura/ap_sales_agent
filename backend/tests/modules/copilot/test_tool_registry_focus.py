"""Tests for focus mode tool selection in the copilot tool registry."""

from src.modules.copilot.application.tools.registry import get_tools_for_context


class TestFocusModeToolSelection:
    def test_focus_mode_returns_focus_tools(self):
        context = {"current_route": "/offer-studio/offer/123", "focus": {"domain": "offer", "entity_id": "abc-123"}}
        tools = get_tools_for_context(context)
        tool_names = {t.name for t in tools}
        assert "entity_write" in tool_names
        assert "entity_read" in tool_names
        assert "entity_undo_all" in tool_names

    def test_focus_mode_excludes_mutation_tools(self):
        context = {"current_route": "/brand-studio", "focus": {"domain": "brand"}}
        tools = get_tools_for_context(context)
        tool_names = {t.name for t in tools}
        assert "propose_field_updates" not in tool_names

    def test_focus_mode_includes_knowledge_tools(self):
        context = {"current_route": "/offer-studio/offer/123", "focus": {"domain": "offer", "entity_id": "abc-123"}}
        tools = get_tools_for_context(context)
        tool_names = {t.name for t in tools}
        assert "search_knowledge_base" in tool_names

    def test_interview_mode_takes_priority_over_focus(self):
        context = {
            "current_route": "/brand-studio/interview",
            "focus": {"domain": "brand"},
            "interview_session_id": "session-123",
        }
        tools = get_tools_for_context(context)
        tool_names = {t.name for t in tools}
        assert "extract_structured" in tool_names
        assert "entity_write" not in tool_names

    def test_chat_mode_unchanged(self):
        context = {"current_route": "/brand-studio"}
        tools = get_tools_for_context(context)
        tool_names = {t.name for t in tools}
        assert "propose_field_updates" in tool_names
        assert "entity_write" not in tool_names
