"""Golden snapshot: tool selection per route.

[COPILOT-REDESIGN-2026-04 F0.5]

Captures which tool *names* the copilot binds for each canonical route. F1
will inject tools via providers; the resulting active set per route must
remain stable unless explicitly extended.
"""

from __future__ import annotations

from src.modules.copilot.application.tools.registry import get_tools_for_route
from tests.modules.copilot.golden.conftest import assert_matches_golden

# Canonical routes covering the four studios + landing + dashboard +
# the wildcard (no route). Add new routes as they ship.
CANONICAL_ROUTES: tuple[str | None, ...] = (
    None,
    "/",
    "/brand-studio",
    "/brand-studio/positioning",
    "/offer-studio",
    "/offer-studio/promise",
    "/offer-studio/value-stack",
    "/landing-studio",
    "/growth-studio",
    "/growth-studio/attraction",
    "/sales-studio",
    "/connections",
    "/inbox",
)


def _tool_name(tool: object) -> str:
    return getattr(tool, "name", repr(tool))


def test_route_tool_selection_matches_baseline() -> None:
    snapshot = {(route or "<none>"): [_tool_name(t) for t in get_tools_for_route(route)] for route in CANONICAL_ROUTES}
    assert_matches_golden("route_tool_selection", snapshot)
