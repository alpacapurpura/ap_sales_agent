"""Architectural fitness — F8 system-prompt cache-friendly order.

Locks the canonical order in ``system_prompt_layout`` so that adding a new
fragment without thinking about cache placement fails the build. Order
changes require updating this snapshot intentionally — the diff is the
audit trail.

# [COPILOT-CACHE-PREFIX-F8] -> docs/domains/copilot/redesign-2026-04/phases/F8-routing-cost-optim.md
"""

from __future__ import annotations

from src.modules.copilot.application.orchestrator.system_prompt_layout import (
    CACHEABLE_FRAGMENTS,
    PROMPT_FRAGMENT_ORDER,
    VOLATILE_FRAGMENTS,
    PromptFragment,
)

# ── Frozen snapshot — the F8 §5.2 contract ────────────────────────────
EXPECTED_CACHEABLE: tuple[PromptFragment, ...] = (
    PromptFragment.STATIC_IDENTITY,
    PromptFragment.STATIC_TOOLS_HINT,
    PromptFragment.LIGHTHOUSE,
    PromptFragment.EDITABLE_CATALOG,
    PromptFragment.MODULES_LIST,
)

EXPECTED_VOLATILE: tuple[PromptFragment, ...] = (
    PromptFragment.STUDIO_SNAPSHOT,
    PromptFragment.WORKFLOW_STATE,
    PromptFragment.INSPIRATIONS,
)


def test_cacheable_fragment_order_is_frozen() -> None:
    """The cacheable prefix order must match F8 §5.2 exactly.

    Reorder rationale:
        1. STATIC_IDENTITY — universally cacheable across tenants.
        2. STATIC_TOOLS_HINT — tools description, stable per-route.
        3. LIGHTHOUSE — per-tenant brand summary.
        4. EDITABLE_CATALOG — schema introspection result.
        5. MODULES_LIST — module registry render.
    """
    assert CACHEABLE_FRAGMENTS == EXPECTED_CACHEABLE


def test_volatile_fragment_order_is_frozen() -> None:
    """The volatile tail order must match F8 §5.2 exactly."""
    assert VOLATILE_FRAGMENTS == EXPECTED_VOLATILE


def test_full_order_is_cacheable_then_volatile() -> None:
    """Cache boundary lives between the two halves; never interleaved."""
    assert PROMPT_FRAGMENT_ORDER == EXPECTED_CACHEABLE + EXPECTED_VOLATILE


def test_no_fragment_appears_in_both_halves() -> None:
    """A fragment is either cacheable or volatile — never both."""
    overlap = set(CACHEABLE_FRAGMENTS) & set(VOLATILE_FRAGMENTS)
    assert not overlap, f"Fragments present in both halves: {overlap}"


def test_every_enum_member_has_an_order_slot() -> None:
    """Adding a new ``PromptFragment`` without slotting it fails here."""
    missing = set(PromptFragment) - set(PROMPT_FRAGMENT_ORDER)
    assert not missing, (
        f"PromptFragment values not slotted into CACHEABLE/VOLATILE: {missing}. "
        "Add the new fragment to one of the tuples in system_prompt_layout.py."
    )
