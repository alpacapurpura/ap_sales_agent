"""Stage-scoped tool registry for the sales agent (S8).

Today the LLM sees the full ``TOOL_REGISTRY`` regardless of stage. That
made sense early — but post-S8 we now have ~14 tools and some are only
appropriate in specific stages (e.g. ``create_booking_link`` should not
appear in ``rapport`` because the lead is unqualified). This registry
filters tools per stage without altering the existing dict-style
contract.

DRY:

* ``TOOL_REGISTRY`` (in ``application/agents/sales/tools.py``) remains
  the SSoT for tool implementations.
* This file owns the **scoping** map — adding a new stage or moving a
  tool between stages touches one place.

Cohesion:

* ``ALWAYS_AVAILABLE`` for cross-stage utilities (escalation, intent).
* ``STAGE_TOOL_SCOPE`` for stage-specific gates.

Coupling:

* Imports only ``TOOL_REGISTRY`` symbol — no orchestrator, no LLM, no
  state. Pure mapping.
* Tests assert that every name in ``ALWAYS_AVAILABLE`` plus the
  union of ``STAGE_TOOL_SCOPE.values()`` exists in ``TOOL_REGISTRY``.
"""

# [SALES-AGENT-S8-TOOLS]  # noqa: ERA001

from __future__ import annotations

from typing import Any

# ──────────────────────────────────────────────────────────────
# Scoping map
# ──────────────────────────────────────────────────────────────


ALWAYS_AVAILABLE: frozenset[str] = frozenset(
    {
        # Safety net — every stage must allow these.
        "escalate_to_human",
        "recommend_product",
        # Read-only verifications — useful at any stage post-creation.
        "verify_booking_status",
        "check_schedule",
        "check_payment_status",
    },
)


STAGE_TOOL_SCOPE: dict[str, frozenset[str]] = {
    "rapport": frozenset(),
    "discovery": frozenset(
        {
            "get_available_slots",
            "list_public_editions",
        },
    ),
    "presentation": frozenset(
        {
            "get_available_slots",
            "create_booking_link",
            "list_public_editions",
            "list_waitlist",
        },
    ),
    "closing": frozenset(
        {
            "create_booking_link",
            "get_available_slots",
            "send_payment_link",
            "create_enrollment",
            "generate_payment_link",
            "mark_enrollment_paid_manual",
            "promote_waitlist_to_edition",
            "list_public_editions",
            "list_waitlist",
        },
    ),
}


def get_tools_for_stage(
    stage: str,
    tool_registry: dict[str, Any],
) -> dict[str, Any]:
    """Return ``{name: callable}`` filtered to the stage's allowed set.

    Unknown stages fall back to ``rapport`` (most restrictive). Tools
    referenced in the scoping but missing from ``tool_registry`` are
    silently skipped — keeps the runtime resilient if a tool is
    deactivated for a tenant via feature flag.
    """
    stage_set = STAGE_TOOL_SCOPE.get(stage, STAGE_TOOL_SCOPE["rapport"])
    allowed = ALWAYS_AVAILABLE | stage_set
    return {name: tool_registry[name] for name in allowed if name in tool_registry}


def is_tool_available_in_stage(tool_name: str, stage: str) -> bool:
    """Return True if ``tool_name`` is allowed at ``stage``."""
    stage_set = STAGE_TOOL_SCOPE.get(stage, STAGE_TOOL_SCOPE["rapport"])
    return tool_name in (ALWAYS_AVAILABLE | stage_set)
