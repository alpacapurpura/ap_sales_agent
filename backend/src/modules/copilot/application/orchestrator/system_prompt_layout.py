"""Cache-friendly system-prompt layout (F8 §5.2).

OpenAI prompt cache (April 2026) requires ≥1024 tokens of unchanged prefix
to activate; below the threshold the cache is not consulted at all. This
module is the *single source of truth* for fragment ordering — every other
piece of the orchestrator declares which slot its content goes into and
``compose_system_prompt`` enforces the canonical sequence.

Order rationale:

    1-2. Static identity + tools hint — universally cacheable across tenants.
    3.   Marketing KB hint — universally cacheable, instructs the LLM to
         consult ``knowledge_search`` and cite the framework when responding
         (F10).
    4.   Lighthouse (brand summary) — per-tenant cacheable, changes on save.
    5.   Editable catalog — per-session stable.
    6.   Modules list — per-session stable.
    --- CACHE BOUNDARY (≥1024 tokens by design above this line) ---
    7.   Studio snapshot (completion) — changes per turn.
    8.   Workflow state (procedure / behavior / selected fields) — per turn.
    9.   Inspirations — semi-volatile but state-aware.
    10+. Conversation messages — handled by LangChain outside this module.

Adding a new fragment? Append to ``PromptFragment``, slot it into either
``CACHEABLE_FRAGMENTS`` or ``VOLATILE_FRAGMENTS``, and update the matching
arch-test invariant. Order changes are deliberate — the test file is the
audit log.

# [COPILOT-CACHE-PREFIX-F8] -> docs/domains/copilot/redesign-2026-04/phases/F8-routing-cost-optim.md
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping


class PromptFragment(StrEnum):
    """Named slots in the system prompt assembly.

    The string value is also used in trace recorder payloads so changing
    one is a wire-format change.
    """

    # ── Cacheable prefix (stable across turns) ────────────────────────
    STATIC_IDENTITY = "static_identity"
    STATIC_TOOLS_HINT = "static_tools_hint"
    MARKETING_KB_HINT = "marketing_kb_hint"  # F10 — cite framework
    # PI-5 PR-2 — D-PI5-009. Cross-tenant cacheable Telegram-only conventions
    # block. Returns "" when channel != "telegram" so web bytes stay
    # byte-identical (cache prefix invariance preserved per channel).
    TELEGRAM_CHANNEL_CONTEXT = "telegram_channel_context"
    LIGHTHOUSE = "lighthouse"
    EDITABLE_CATALOG = "editable_catalog"
    MODULES_LIST = "modules_list"
    # ── Volatile tail (changes per turn) ──────────────────────────────
    STUDIO_SNAPSHOT = "studio_snapshot"
    WORKFLOW_STATE = "workflow_state"
    INSPIRATIONS = "inspirations"


CACHEABLE_FRAGMENTS: tuple[PromptFragment, ...] = (
    PromptFragment.STATIC_IDENTITY,
    PromptFragment.STATIC_TOOLS_HINT,
    PromptFragment.MARKETING_KB_HINT,
    PromptFragment.TELEGRAM_CHANNEL_CONTEXT,  # PI-5 PR-2 (D-PI5-009)
    PromptFragment.LIGHTHOUSE,
    PromptFragment.EDITABLE_CATALOG,
    PromptFragment.MODULES_LIST,
)

VOLATILE_FRAGMENTS: tuple[PromptFragment, ...] = (
    PromptFragment.STUDIO_SNAPSHOT,
    PromptFragment.WORKFLOW_STATE,
    PromptFragment.INSPIRATIONS,
)

PROMPT_FRAGMENT_ORDER: tuple[PromptFragment, ...] = CACHEABLE_FRAGMENTS + VOLATILE_FRAGMENTS

CACHE_BOUNDARY_MARKER: str = "\n\n<!-- ==== CACHE BOUNDARY (F8) ==== -->\n\n"
"""Inserted between the cacheable prefix and the volatile tail. Renders as
an HTML comment in markdown (LLM ignores it) but is greppable in trace
inspections to confirm the boundary is where it should be."""

_FRAGMENT_SEPARATOR: str = "\n\n"


def compose_system_prompt(fragments: Mapping[PromptFragment, str]) -> str:
    """Assemble fragments in canonical F8 cache-friendly order.

    Empty / missing fragments are skipped. Each rendered fragment has its
    leading and trailing whitespace stripped; double-newline separates
    consecutive fragments. The cache-boundary marker is inserted only when
    at least one fragment exists on each side (skips it for trivial
    bootstrap cases).

    The function is deterministic, side-effect free, and pure data — call
    it from any thread without coordination.
    """
    cache_parts = _take(fragments, CACHEABLE_FRAGMENTS)
    volatile_parts = _take(fragments, VOLATILE_FRAGMENTS)

    if not cache_parts and not volatile_parts:
        return ""
    if not volatile_parts:
        return _FRAGMENT_SEPARATOR.join(cache_parts)
    if not cache_parts:
        return _FRAGMENT_SEPARATOR.join(volatile_parts)

    return _FRAGMENT_SEPARATOR.join(cache_parts) + CACHE_BOUNDARY_MARKER + _FRAGMENT_SEPARATOR.join(volatile_parts)


def _take(
    fragments: Mapping[PromptFragment, str],
    slots: tuple[PromptFragment, ...],
) -> list[str]:
    """Pull fragments by slot order, dropping empty / whitespace-only entries."""
    out: list[str] = []
    for slot in slots:
        raw = fragments.get(slot, "")
        cleaned = (raw or "").strip()
        if cleaned:
            out.append(cleaned)
    return out


__all__ = (
    "CACHEABLE_FRAGMENTS",
    "CACHE_BOUNDARY_MARKER",
    "PROMPT_FRAGMENT_ORDER",
    "VOLATILE_FRAGMENTS",
    "PromptFragment",
    "compose_system_prompt",
)
