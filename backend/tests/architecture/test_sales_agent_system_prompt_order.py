"""Architectural fitness — S3 sales_agent system-prompt cache-friendly order.

Locks the canonical order in ``sales_agent.application.prompts.compose`` so
that adding a new fragment without thinking about cache placement fails the
build. Order changes require updating this snapshot intentionally — the diff
is the audit trail.

Mirror of ``backend/tests/architecture/test_system_prompt_order.py`` (F8 copilot).

# [SALES-AGENT-CACHE-PREFIX-S3] -> docs/domains/sales-agent/redesign-2026-04/phases/S3-prompt-cache-boundary.md
"""

from __future__ import annotations

from luana_core_sales_agent.application.prompts.compose import (
    CACHEABLE_FRAGMENTS,
    PROMPT_FRAGMENT_ORDER,
    VOLATILE_FRAGMENTS,
    PromptFragment,
)

# ── Frozen snapshot — the S3 §3.4 contract ────────────────────────────
EXPECTED_CACHEABLE: tuple[PromptFragment, ...] = (
    PromptFragment.STATIC_IDENTITY,
    PromptFragment.STATIC_TOOLS_HINT,
    PromptFragment.SALES_PLAYBOOK_HINT,
    PromptFragment.AGENT_IDENTITY,
    PromptFragment.BRAND_VOICE,
    PromptFragment.CHANNEL_FORMAT_HINT,
    PromptFragment.CAMPAIGN_CONTEXT,
)

EXPECTED_VOLATILE: tuple[PromptFragment, ...] = (
    PromptFragment.STAGE_HINT,
    PromptFragment.LEAD_SIGNALS,
    PromptFragment.SESSION_CONTINUITY,
    PromptFragment.TOOL_REQUEST_FORMAT,
)


def test_cacheable_fragment_order_is_frozen() -> None:
    """Cacheable prefix order must match S3 §3.4 exactly.

    Reorder rationale:
        1. STATIC_IDENTITY — universally cacheable across tenants.
        2. STATIC_TOOLS_HINT — tools description, stable per-route.
        3. SALES_PLAYBOOK_HINT — humanization + signals + active specialist body.
        4. AGENT_IDENTITY — per-tenant brand+offer+channel render.
        5. BRAND_VOICE — placeholder for S7 brand voice split.
        6. CHANNEL_FORMAT_HINT — placeholder for S5 channel registry split.
        7. CAMPAIGN_CONTEXT — PR-7 outbound campaign instructions (only when outbound_mode=True).
    """
    assert CACHEABLE_FRAGMENTS == EXPECTED_CACHEABLE


def test_volatile_fragment_order_is_frozen() -> None:
    """Volatile tail order must match S3 §3.4 exactly."""
    assert VOLATILE_FRAGMENTS == EXPECTED_VOLATILE


def test_full_order_is_cacheable_then_volatile() -> None:
    """Cache boundary lives between the two halves; never interleaved."""
    assert PROMPT_FRAGMENT_ORDER == EXPECTED_CACHEABLE + EXPECTED_VOLATILE


def test_no_fragment_appears_in_both_halves() -> None:
    overlap = set(CACHEABLE_FRAGMENTS) & set(VOLATILE_FRAGMENTS)
    assert not overlap, f"Fragments present in both halves: {overlap}"


def test_every_enum_member_has_an_order_slot() -> None:
    missing = set(PromptFragment) - set(PROMPT_FRAGMENT_ORDER)
    assert not missing, (
        f"PromptFragment values not slotted into CACHEABLE/VOLATILE: {missing}. "
        "Add the new fragment to one of the tuples in compose.py."
    )
