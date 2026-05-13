"""Golden snapshot: studio context resolution per canonical route.

[COPILOT-REDESIGN-2026-04 F0.5]

``_resolve_studio_context(route)`` decides which studio + section the
system prompt focuses on. F3 (brand summary lighthouse) and F1 (provider
pattern context_injector) both depend on this mapping. Snapshot it now.
"""

from __future__ import annotations

from luana_core_copilot.application.orchestrator.graph import _resolve_studio_context
from tests.modules.copilot.golden.conftest import assert_matches_golden

CANONICAL_ROUTES: tuple[str | None, ...] = (
    None,
    "/",
    "/brand-studio",
    "/brand-studio/positioning",
    "/brand-studio/visuals",
    "/offer-studio",
    "/offer-studio/promise",
    "/offer-studio/value-stack",
    "/offer-studio/audience",
    "/landing-studio",
    "/growth-studio",
    "/growth-studio/attraction",
    "/sales-studio",
    "/connections",
    "/inbox",
)


def test_studio_context_resolution_matches_baseline() -> None:
    snapshot: dict[str, list[str | None] | None] = {}
    for route in CANONICAL_ROUTES:
        result = _resolve_studio_context(route)
        snapshot[route or "<none>"] = list(result) if result is not None else None
    assert_matches_golden("studio_context_resolution", snapshot)
