"""Tests for context-aware (mode-based) tool selection."""

from src.modules.copilot.application.tools.registry import (
    TOOL_GROUPS,
    get_tools_for_context,
)


class TestToolSelectionByMode:
    def test_interview_mode_returns_interview_and_knowledge_tools(self) -> None:
        ctx = {"current_route": "/brand-studio", "interview_session_id": "session-123"}
        tools = get_tools_for_context(ctx)
        tool_names = {t.name for t in tools}
        for t in TOOL_GROUPS["interview"]:
            assert t.name in tool_names, f"Missing interview tool: {t.name}"
        for t in TOOL_GROUPS["knowledge"]:
            assert t.name in tool_names, f"Missing knowledge tool: {t.name}"
        for t in TOOL_GROUPS.get("mutation", []):
            assert t.name not in tool_names, f"Unexpected mutation tool: {t.name}"

    def test_interview_mode_ignores_route(self) -> None:
        ctx_brand = {"current_route": "/brand-studio", "interview_session_id": "s-1"}
        ctx_offer = {"current_route": "/offer-studio/offer/456", "interview_session_id": "s-2"}
        tools_brand = {t.name for t in get_tools_for_context(ctx_brand)}
        tools_offer = {t.name for t in get_tools_for_context(ctx_offer)}
        assert tools_brand == tools_offer

    def test_chat_mode_uses_route_based_selection(self) -> None:
        ctx = {"current_route": "/growth-studio"}
        tools = get_tools_for_context(ctx)
        tool_names = {t.name for t in tools}
        for t in TOOL_GROUPS["analytics"]:
            assert t.name in tool_names, f"Missing analytics tool: {t.name}"

    def test_empty_context_uses_fallback(self) -> None:
        tools = get_tools_for_context({})
        assert len(tools) > 0

    def test_none_context_uses_fallback(self) -> None:
        tools = get_tools_for_context(None)
        assert len(tools) > 0

    def test_all_returned_tools_have_name_attribute(self) -> None:
        ctx = {"interview_session_id": "s-1"}
        tools = get_tools_for_context(ctx)
        for t in tools:
            assert hasattr(t, "name"), f"Tool {t!r} missing .name"
            assert t.name, f"Tool {t!r} has empty .name"
