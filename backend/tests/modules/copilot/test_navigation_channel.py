"""
Tests for navigate_to_channel copilot tool.

Validates URL generation for Growth Studio deep links:
- Sidebar URL: /growth-studio/{stage}?channel={slug}
- Sidebar + tab: /growth-studio/{stage}?channel={slug}&tab={tab}
- Expanded URL: /growth-studio/{stage}/{slug}
- Expanded + tab: /growth-studio/{stage}/{slug}?tab={tab}
"""

from src.modules.copilot.application.tools.navigation import navigate_to_channel


class TestNavigateToChannel:
    def test_sidebar_url(self):
        """Basic sidebar deep link without tab."""
        result = navigate_to_channel.invoke(
            {
                "stage": "atraccion-captura",
                "channel_slug": "meta-ads",
            },
        )
        assert result["success"] is True
        action = result["ui_action"]
        assert action["type"] == "navigate"
        assert "atraccion-captura" in action["route"]
        assert "channel=meta-ads" in action["route"]
        assert "tab=" not in action["route"]

    def test_sidebar_url_with_tab(self):
        """Sidebar deep link with specific tab."""
        result = navigate_to_channel.invoke(
            {
                "stage": "atraccion-captura",
                "channel_slug": "meta-ads",
                "tab": "campanas",
            },
        )
        assert result["success"] is True
        action = result["ui_action"]
        assert "channel=meta-ads" in action["route"]
        assert "tab=campanas" in action["route"]

    def test_expanded_url(self):
        """Expanded (full-page) deep link."""
        result = navigate_to_channel.invoke(
            {
                "stage": "atraccion-captura",
                "channel_slug": "meta-ads",
                "expanded": True,
            },
        )
        assert result["success"] is True
        action = result["ui_action"]
        assert action["route"].endswith("/atraccion-captura/meta-ads")
        assert "channel=" not in action["route"]

    def test_expanded_url_with_tab(self):
        """Expanded deep link with tab query param."""
        result = navigate_to_channel.invoke(
            {
                "stage": "atraccion-captura",
                "channel_slug": "meta-ads",
                "expanded": True,
                "tab": "campanas",
            },
        )
        assert result["success"] is True
        action = result["ui_action"]
        assert "/atraccion-captura/meta-ads" in action["route"]
        assert "tab=campanas" in action["route"]
        assert "channel=" not in action["route"]

    def test_different_stage(self):
        """Works with non-default stages."""
        result = navigate_to_channel.invoke(
            {
                "stage": "nutricion-oportunidad",
                "channel_slug": "email-nurture",
            },
        )
        assert result["success"] is True
        action = result["ui_action"]
        assert "nutricion-oportunidad" in action["route"]
        assert "channel=email-nurture" in action["route"]

    def test_result_includes_navigate_type(self):
        """UI action type is 'navigate' for frontend router.push."""
        result = navigate_to_channel.invoke(
            {
                "stage": "ventas",
                "channel_slug": "shopify",
            },
        )
        assert result["ui_action"]["type"] == "navigate"

    def test_tool_in_navigation_tools(self):
        """navigate_to_channel is part of NAVIGATION_TOOLS."""
        from src.modules.copilot.application.tools.navigation import NAVIGATION_TOOLS

        tool_names = [t.name for t in NAVIGATION_TOOLS]
        assert "navigate_to_channel" in tool_names

    def test_tool_available_in_growth_studio_route(self):
        """navigate_to_channel is available when on growth-studio routes."""
        from src.modules.copilot.application.tools.registry import (
            get_tool_names_for_route,
        )

        names = get_tool_names_for_route("/tenant/growth-studio/atraccion-captura")
        assert "navigate_to_channel" in names
