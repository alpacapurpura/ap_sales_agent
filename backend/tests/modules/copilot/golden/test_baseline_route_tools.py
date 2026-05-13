"""Golden snapshot: tool selection per route.

[COPILOT-REDESIGN-2026-04 F0.5]

Captures which tool *names* the copilot binds for each canonical route. F1
will inject tools via providers; the resulting active set per route must
remain stable unless explicitly extended.
"""

from __future__ import annotations

from luana_core_copilot.application.tools.registry import get_tools_for_route
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
    # Sort tool names per route so the snapshot is order-independent.
    # ``get_tools_for_route`` order depends on tool-registry insertion
    # which varies between fresh CI runs and locally cached interpreters.
    # The contract we care about is the SET of tools bound per route, not
    # the order — so we normalise here and lock the alphabetical
    # representation in the golden file.
    # Filter test-only synth tools (``_tp*`` prefix). The
    # ``test_route_tool_mapping.py::TestProviderRouteMerging`` suite
    # injects a synthetic provider with ``_tp10_synth_tool`` to verify
    # the F1 routes-merging contract. That registry mutation is hard
    # to fully revert (``importlib.reload`` leaves stale references on
    # already-imported handles) so when pytest-randomly orders that
    # suite before this one the synth tool leaks into the snapshot.
    # Production tools are never named ``_tp*`` — exclude them from
    # the contract under test rather than fight the reload ordering.
    snapshot = {
        (route or "<none>"): sorted(
            name for name in (_tool_name(t) for t in get_tools_for_route(route)) if not name.startswith("_tp")
        )
        for route in CANONICAL_ROUTES
    }
    assert_matches_golden("route_tool_selection", snapshot)
