"""
Tests for copilot route-based tool selection.

Validates that:
- Every route in ROUTE_TOOL_MAP resolves to at least one tool
- Known routes resolve to expected tool groups
- Fallback ("*") is used for unknown routes
- get_tools_for_route returns callable LangChain tools (have .name attribute)
- None route uses the "*" fallback
"""


class TestRouteToolMapping:
    def test_all_routes_resolve_to_at_least_one_tool(self):
        """Every route entry in ROUTE_TOOL_MAP yields at least 1 tool."""
        from src.modules.copilot.application.tools.registry import (
            ROUTE_TOOL_MAP,
            get_tools_for_route,
        )

        for route_prefix in ROUTE_TOOL_MAP:
            if route_prefix == "*":
                continue
            tools = get_tools_for_route(f"/tenant-123/{route_prefix}/something")
            assert tools, f"Route '{route_prefix}' resolved to 0 tools"

    def test_brand_studio_includes_mutation_and_awareness(self):
        """brand-studio route includes both mutation and awareness tool groups."""
        from src.modules.copilot.application.tools.registry import ROUTE_TOOL_MAP

        groups = ROUTE_TOOL_MAP.get("brand-studio", [])
        assert "mutation" in groups
        assert "awareness" in groups

    def test_growth_studio_includes_analytics_tools(self):
        """growth-studio route includes the analytics tool group."""
        from src.modules.copilot.application.tools.registry import ROUTE_TOOL_MAP

        groups = ROUTE_TOOL_MAP.get("growth-studio", [])
        assert "analytics" in groups
        assert "crm" in groups

    def test_unknown_route_uses_fallback(self):
        """An unrecognised route uses the '*' fallback group list."""
        from src.modules.copilot.application.tools.registry import get_tools_for_route

        tools_unknown = get_tools_for_route("/tenant/totally-unknown-page")
        tools_fallback = get_tools_for_route(None)  # None also hits fallback

        assert len(tools_unknown) > 0
        assert len(tools_fallback) > 0

    def test_none_route_equals_fallback(self):
        """get_tools_for_route(None) == get_tools_for_route on an unknown route."""
        from src.modules.copilot.application.tools.registry import get_tools_for_route

        none_tools = {t.name for t in get_tools_for_route(None)}
        unknown_tools = {t.name for t in get_tools_for_route("/totally/unknown")}
        assert none_tools == unknown_tools

    def test_tools_have_name_attribute(self):
        """All resolved tools expose a .name attribute (LangChain tool contract)."""
        from src.modules.copilot.application.tools.registry import get_all_tools

        tools = get_all_tools()
        assert tools, "No tools registered at all"
        for t in tools:
            assert hasattr(t, "name"), f"Tool {t!r} is missing .name"
            assert t.name, f"Tool {t!r} has empty .name"
