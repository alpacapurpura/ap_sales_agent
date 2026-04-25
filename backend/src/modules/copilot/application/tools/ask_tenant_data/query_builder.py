"""Query builder for ``ask_tenant_data``.

Pure-Python deterministic stage that converts an :class:`IntentResult` to a
:class:`DataQueryPlan`. Period phrases are resolved via :mod:`.date_parser`
here (not in the executor) so the executor stays a thin dispatcher.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.modules.copilot.application.tools.ask_tenant_data.date_parser import (
    parse_period,
)
from src.modules.copilot.domain.ports import DataQueryPlan

if TYPE_CHECKING:
    from datetime import datetime

    from src.modules.copilot.application.tools.ask_tenant_data.intent_classifier import (
        IntentResult,
    )


def build_plan(
    intent: IntentResult,
    *,
    now: datetime | None = None,
    default_limit: int = 20,
) -> DataQueryPlan | None:
    """Build a ``DataQueryPlan`` from the classified intent.

    Returns ``None`` for ``unknown`` intent so the caller can short-circuit
    without dispatching to any provider. Default ``limit`` keeps result rows
    small enough for a copilot response payload (also bounds DB cost).
    """
    if intent.kind == "unknown":
        return None

    if intent.kind == "offer_lookup":
        filters: dict[str, Any] = {"status": "active"}
        if intent.name_query:
            filters["name_query"] = intent.name_query
        return DataQueryPlan(
            kind="offer_lookup",
            filters=filters,
            limit=default_limit,
        )

    if intent.kind in {"lead_count", "conversation_count"}:
        since, until = parse_period(intent.period_phrase, now=now)
        filters = {"since": since, "until": until}
        if intent.channel:
            filters["channel"] = intent.channel
        return DataQueryPlan(
            kind=intent.kind,
            filters=filters,
            limit=default_limit,
        )

    return None


__all__ = ("build_plan",)
