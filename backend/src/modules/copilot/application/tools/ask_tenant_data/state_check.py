"""State-check stage for ``ask_tenant_data``.

Pure-Python annotator that reads the executor result and emits advisory flags
the synthesizer reads to phrase a more useful answer:

* ``empty`` — count is zero (lookup or count kinds).
* ``empty_window`` — count is zero AND the plan filtered by a date window.
* ``only_archived`` — offer_lookup returned rows but none are active.

No LLM call here; the next stage interprets these flags inside the response.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.modules.copilot.domain.ports import DataQueryPlan, DataQueryResult


def annotate_state(*, plan: DataQueryPlan, result: DataQueryResult) -> dict[str, Any]:
    """Inspect plan + result and return the advisory flag mapping."""
    flags: dict[str, Any] = {}
    count = int(result.metadata.get("count", 0) or 0)

    has_window = "since" in plan.filters and "until" in plan.filters
    if count == 0:
        if has_window:
            flags["empty_window"] = True
        else:
            flags["empty"] = True

    if plan.kind == "offer_lookup" and count > 0:
        active = int(result.metadata.get("active_count", 0) or 0)
        archived = int(result.metadata.get("archived_count", 0) or 0)
        if active == 0 and archived > 0:
            flags["only_archived"] = True

    return flags


__all__ = ("annotate_state",)
