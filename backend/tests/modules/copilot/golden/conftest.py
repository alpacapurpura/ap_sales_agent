"""Golden snapshot fixtures for the copilot baseline.

[COPILOT-REDESIGN-2026-04 F0.5] -> docs/domains/copilot/redesign-2026-04/

Approach
--------
F0 captures four deterministic surface snapshots of the copilot today so
later phases (F1 provider pattern especially) can detect drift in the
public extension surface without expensive end-to-end mocking:

1. ``module_registry_shape``       -> ``get_module_registry()`` keys + meta
2. ``route_tool_selection``        -> ``get_tools_for_route(route)`` per route
3. ``routing_policy_shape``        -> ``DEFAULT_ROUTING_POLICY`` rules + tier
4. ``studio_context_resolution``   -> ``_resolve_studio_context(route)``

Why not full conversation snapshots?
- 73 existing copilot test files already exercise behavior end-to-end.
- Full conversation goldens require pervasive LLM mocking and become
  fragile noise on every prompt tweak.
- The redesign's biggest regression risk is *contract* drift in the four
  surfaces above (everything the provider pattern in F1 will reshape).
- Full conversation goldens with LLM-judge belong in F9 (quality phase).

Updating snapshots
------------------
Run ``UPDATE_GOLDEN=1 pytest tests/modules/copilot/golden -q`` to rewrite
all snapshots when the underlying contract intentionally changes. The diff
ends up in the commit and is reviewed like any other API change.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

SNAPSHOTS_DIR = Path(__file__).parent / "snapshots"


def _normalise(value: Any) -> Any:
    """Make values stable across runs (sort dict keys, sort list of strings)."""
    if isinstance(value, dict):
        return {k: _normalise(value[k]) for k in sorted(value.keys())}
    if isinstance(value, list):
        if all(isinstance(item, str) for item in value):
            return sorted(value)
        return [_normalise(item) for item in value]
    if isinstance(value, tuple):
        return [_normalise(item) for item in value]
    return value


def assert_matches_golden(name: str, actual: Any) -> None:
    """Compare ``actual`` against the snapshot at ``snapshots/{name}.json``.

    On mismatch the assertion message includes both blobs so reviewers can
    eyeball intent. Set ``UPDATE_GOLDEN=1`` in the environment to overwrite
    the snapshot with ``actual`` (used during intentional contract changes).
    """
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    path = SNAPSHOTS_DIR / f"{name}.json"
    serialised = json.dumps(_normalise(actual), indent=2, sort_keys=True, ensure_ascii=False)

    if os.environ.get("UPDATE_GOLDEN") == "1" or not path.exists():
        path.write_text(serialised + "\n", encoding="utf-8")
        return

    expected = path.read_text(encoding="utf-8").rstrip("\n")
    if serialised != expected:
        msg = (
            f"Golden snapshot drift in {name}.\n"
            f"To accept: UPDATE_GOLDEN=1 pytest tests/modules/copilot/golden -q\n"
            f"--- expected ({path}) ---\n{expected}\n"
            f"--- actual ---\n{serialised}\n"
        )
        raise AssertionError(msg)
