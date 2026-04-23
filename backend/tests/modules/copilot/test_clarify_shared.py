"""Tests for the shared ``clarify`` tool.

Historically ``clarify`` lived under ``tools/interview/`` and capped items
at 2. It now lives in ``tools/shared_tools/`` (promoted out of the retired
interview engine) and caps at 4 to match the UI button-row capacity and
WhatsApp list messages.
"""

from __future__ import annotations

import json

import pytest

from src.modules.copilot.application.tools.shared_tools.clarify import (
    MAX_CLARIFY_ITEMS,
    clarify,
)


class TestClarifyShared:
    def test_max_items_is_four(self) -> None:
        assert MAX_CLARIFY_ITEMS == 4

    def test_single_item_passes_through(self) -> None:
        result = clarify.invoke(
            {
                "items": [
                    {
                        "field_path": "extraction.scope",
                        "issue": "¿Extraer todo o solo la sección actual?",
                        "options": ["Todo initial", "Completar faltantes", "Solo sección actual"],
                    },
                ],
            },
        )
        parsed = json.loads(result)
        assert parsed["ui_action"]["type"] == "clarify_card"
        assert len(parsed["ui_action"]["clarify_items"]) == 1
        assert parsed["ui_action"]["clarify_items"][0]["options"] == [
            "Todo initial",
            "Completar faltantes",
            "Solo sección actual",
        ]

    def test_caps_at_four_items(self) -> None:
        items = [{"field_path": f"f{i}", "issue": f"i{i}", "options": ["a", "b"]} for i in range(6)]
        result = clarify.invoke({"items": items})
        parsed = json.loads(result)
        assert len(parsed["ui_action"]["clarify_items"]) == MAX_CLARIFY_ITEMS

    def test_returns_visible_text(self) -> None:
        result = clarify.invoke(
            {"items": [{"field_path": "x", "issue": "y", "options": ["a", "b"]}]},
        )
        parsed = json.loads(result)
        assert isinstance(parsed["text"], str)
        assert parsed["text"]


class TestSharedToolsGroup:
    def test_shared_tools_exposes_clarify(self) -> None:
        from src.modules.copilot.application.tools.shared_tools import SHARED_TOOLS

        names = [t.name for t in SHARED_TOOLS]
        assert "clarify" in names

    def test_registry_has_shared_tools_group(self) -> None:
        from src.modules.copilot.application.tools.registry import TOOL_GROUPS

        assert "shared_tools" in TOOL_GROUPS
        names = {t.name for t in TOOL_GROUPS["shared_tools"]}
        assert "clarify" in names


class TestRouteBinding:
    @pytest.mark.parametrize(
        "route",
        [
            "/tenant-id/brand-studio/identity",
            "/tenant-id/offer-studio/edit/offer-id",
            "/tenant-id/landing",  # "*" fallback
        ],
    )
    def test_clarify_is_bound_on_every_route(self, route: str) -> None:
        """Clarify must be available everywhere so the LLM can ask the user
        questions before picking a tool.
        """
        from src.modules.copilot.application.tools.registry import (
            get_tool_names_for_route,
        )

        names = get_tool_names_for_route(route)
        assert "clarify" in names, f"clarify missing on route {route}; got {names}"
