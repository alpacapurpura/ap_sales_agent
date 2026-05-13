"""Arch test: ROUTE_TOOL_MAP prefixes ordered most-specific first.

`_match_route` scans prefix keys in insertion order and returns the first
``prefix in route_lower`` hit. If a generic prefix (e.g. ``"sales"``) is
registered BEFORE a more specific one (``"sales/studio"``), the specific entry
is dead code because every ``sales/studio`` route matches ``sales`` first.

This test fails if two prefixes overlap and the shorter one is listed earlier.
"""

from __future__ import annotations

from luana_core_copilot.application.tools.registry import ROUTE_TOOL_MAP


def test_route_prefixes_are_ordered_most_specific_first() -> None:
    """If prefix A contains prefix B, B must appear earlier in the dict."""
    prefixes = [p for p in ROUTE_TOOL_MAP if p != "*"]

    violations: list[str] = []
    for i, shorter in enumerate(prefixes):
        for longer in prefixes[i + 1 :]:
            # A later (longer) prefix shadowed by an earlier (shorter) one
            if shorter in longer and shorter != longer:
                violations.append(
                    f"{longer!r} comes after {shorter!r} — any route containing "
                    f"{longer!r} will match {shorter!r} first and never reach "
                    f"{longer!r}. Move {longer!r} above {shorter!r}.",
                )

    assert not violations, "\n".join(violations)


def test_fallback_route_exists() -> None:
    """The ``*`` fallback MUST be present so unmatched routes still bind tools."""
    assert "*" in ROUTE_TOOL_MAP, "ROUTE_TOOL_MAP missing required '*' fallback entry"
