"""Architecture fitness test: Copilot Tool Registry invariants.

Verifies that every offer-section tool is:
- In OFFER_SECTION_TOOLS list (exported from offer_section_tools.py)
- In the ``offer_section`` group in TOOL_GROUPS
- The ``offer-studio`` route includes ``offer_section`` group
- All tools in OFFER_SECTION_TOOLS are callable LangChain tools (have .name)
"""

from __future__ import annotations

import pytest

EXPECTED_OFFER_SECTION_TOOLS = frozenset(
    {
        "adapt_from_brand_identity",
        "adapt_from_brand_narrative",
        "rewrite_tones",
        "validate_preset_coherence",
        "reuse_brand_buyer_personas",
        "inherit_brand_methodology",
        "high_ticket_tiering_template",
        "recurring_billing_setup",
        "detect_currency_mismatch",
        "import_scheduling_event_type",
        "detect_hybrid_split",
        "import_from_brand_vault",
        "suggest_missing_objections",
        "generate_from_preset_flags",
        "pull_sales_agent_common_questions",
        "assemble_from_brand_authority",
        "reuse_brand_team",
        "structure_objections",
    }
)


class TestCopilotRegistryInvariants:
    """Architectural invariants for the copilot tool registry."""

    def test_offer_section_tools_count(self) -> None:
        """OFFER_SECTION_TOOLS must have exactly 17 tools."""
        from src.modules.copilot.application.tools.offer_section_tools import (
            OFFER_SECTION_TOOLS,
        )

        assert len(OFFER_SECTION_TOOLS) == 18, (
            f"Expected 18 offer-section tools, got {len(OFFER_SECTION_TOOLS)}. "
            "Update this test when intentionally adding/removing tools."
        )

    def test_all_expected_tools_present(self) -> None:
        """Every expected offer-section tool name must appear in OFFER_SECTION_TOOLS."""
        from src.modules.copilot.application.tools.offer_section_tools import (
            OFFER_SECTION_TOOLS,
        )

        registered_names = {t.name for t in OFFER_SECTION_TOOLS}
        missing = EXPECTED_OFFER_SECTION_TOOLS - registered_names
        extra = registered_names - EXPECTED_OFFER_SECTION_TOOLS
        assert not missing, f"Missing tools in OFFER_SECTION_TOOLS: {missing}"
        assert not extra, f"Unexpected tools in OFFER_SECTION_TOOLS: {extra}"

    def test_all_tools_are_callable_langchain_tools(self) -> None:
        """Every entry in OFFER_SECTION_TOOLS must have a .name attribute (LangChain tool)."""
        from src.modules.copilot.application.tools.offer_section_tools import (
            OFFER_SECTION_TOOLS,
        )

        for t in OFFER_SECTION_TOOLS:
            assert hasattr(t, "name"), f"Tool {t!r} is not a LangChain tool (missing .name)"
            assert callable(t.invoke), f"Tool {t.name!r} is not invocable"

    def test_offer_section_group_in_tool_groups(self) -> None:
        """TOOL_GROUPS must contain the 'offer_section' key."""
        from src.modules.copilot.application.tools.registry import TOOL_GROUPS

        assert "offer_section" in TOOL_GROUPS, (
            "'offer_section' group missing from TOOL_GROUPS in registry.py. Add: 'offer_section': OFFER_SECTION_TOOLS"
        )

    def test_offer_section_group_matches_exported_list(self) -> None:
        """TOOL_GROUPS['offer_section'] must be identical to OFFER_SECTION_TOOLS."""
        from src.modules.copilot.application.tools.offer_section_tools import (
            OFFER_SECTION_TOOLS,
        )
        from src.modules.copilot.application.tools.registry import TOOL_GROUPS

        group_names = {t.name for t in TOOL_GROUPS["offer_section"]}
        exported_names = {t.name for t in OFFER_SECTION_TOOLS}
        assert group_names == exported_names, (
            "TOOL_GROUPS['offer_section'] and OFFER_SECTION_TOOLS are out of sync. "
            f"Diff: group_extra={group_names - exported_names}, exported_extra={exported_names - group_names}"
        )

    def test_offer_studio_route_includes_offer_section(self) -> None:
        """The 'offer-studio' route entry must include 'offer_section' group."""
        from src.modules.copilot.application.tools.registry import ROUTE_TOOL_MAP

        offer_studio_groups = ROUTE_TOOL_MAP.get("offer-studio", [])
        assert "offer_section" in offer_studio_groups, (
            "'offer_section' missing from ROUTE_TOOL_MAP['offer-studio']. "
            "Add it so the copilot activates offer-section tools in the Offer Studio."
        )

    def test_no_offer_section_tool_name_collision_with_other_groups(self) -> None:
        """Offer-section tool names must not collide with tools in other groups."""
        from src.modules.copilot.application.tools.offer_section_tools import (
            OFFER_SECTION_TOOLS,
        )
        from src.modules.copilot.application.tools.registry import TOOL_GROUPS

        offer_section_names = {t.name for t in OFFER_SECTION_TOOLS}
        collisions: list[str] = []
        for group_key, tools in TOOL_GROUPS.items():
            if group_key == "offer_section":
                continue
            for t in tools:
                if t.name in offer_section_names:
                    collisions.append(f"{t.name!r} (group: {group_key!r})")

        assert not collisions, (
            f"Offer-section tool names collide with other groups: {collisions}. "
            "Rename to avoid ambiguity in LLM tool selection."
        )

    def test_get_tools_for_offer_studio_includes_offer_section_tools(self) -> None:
        """get_tools_for_route('/tenant/offer-studio/sections/promise') must include ≥1 offer-section tool."""
        from src.modules.copilot.application.tools.offer_section_tools import (
            OFFER_SECTION_TOOLS,
        )
        from src.modules.copilot.application.tools.registry import get_tools_for_route

        tools = get_tools_for_route("/tenant-123/offer-studio/sections/promise")
        tool_names = {t.name for t in tools}
        offer_section_names = {t.name for t in OFFER_SECTION_TOOLS}

        intersection = tool_names & offer_section_names
        assert intersection, (
            "get_tools_for_route for offer-studio returned no offer-section tools. "
            "Check that 'offer_section' is in ROUTE_TOOL_MAP['offer-studio']."
        )
