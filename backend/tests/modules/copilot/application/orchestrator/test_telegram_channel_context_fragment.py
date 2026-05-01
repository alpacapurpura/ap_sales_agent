"""Tests for the TELEGRAM_CHANNEL_CONTEXT cacheable fragment (PI-5 PR-2).

The fragment is byte-identical cross-tenant cross-turn — NO interpolation
of timestamps, conv_ids, tenant_ids, message counts, or anything that
varies between requests. Only ``{tenant_slug}`` and ``{ruta}`` may
appear and they are LITERAL strings the LLM substitutes at output time.
"""

from __future__ import annotations

import re

from src.modules.copilot.application.orchestrator.graph import (
    _build_telegram_channel_context_fragment,
)
from src.modules.copilot.application.orchestrator.system_prompt_layout import (
    CACHEABLE_FRAGMENTS,
    PROMPT_FRAGMENT_ORDER,
    PromptFragment,
)


def _state(channel: str | None) -> dict:
    """Minimal state for fragment tests."""
    if channel is None:
        return {}
    return {"client_context": {"channel": channel}}


# ── Conditional emission ────────────────────────────────────────────────


def test_fragment_emits_when_channel_is_telegram() -> None:
    out = _build_telegram_channel_context_fragment(_state("telegram"))
    assert out, "fragment must emit non-empty content for channel='telegram'"


def test_fragment_empty_when_channel_is_web() -> None:
    out = _build_telegram_channel_context_fragment(_state("web"))
    assert out == ""


def test_fragment_empty_when_channel_is_none() -> None:
    out = _build_telegram_channel_context_fragment(_state(None))
    assert out == ""


def test_fragment_empty_when_client_context_missing_channel_key() -> None:
    out = _build_telegram_channel_context_fragment({"client_context": {}})
    assert out == ""


def test_fragment_empty_when_state_is_empty() -> None:
    out = _build_telegram_channel_context_fragment({})
    assert out == ""


def test_fragment_empty_for_unknown_channel() -> None:
    out = _build_telegram_channel_context_fragment(_state("whatsapp"))
    assert out == ""


# ── Content invariants ──────────────────────────────────────────────────


def test_fragment_carries_anchor() -> None:
    out = _build_telegram_channel_context_fragment(_state("telegram"))
    assert "[COPILOT-TELEGRAM-CHANNEL-CONTEXT]" in out


def test_fragment_no_pii_or_dynamic_interpolation_python_side() -> None:
    """Python code MUST NOT interpolate per-tenant or per-turn data into the prefix.

    ``{tenant_slug}`` and ``{ruta}`` are literal strings the LLM emits to
    the user; everything else inside curly braces that looks like a Python
    identifier would indicate a Python f-string interpolation that would
    invalidate the cache prefix on every turn.

    The regex matches ONLY Python-identifier-shaped placeholders so the
    literal ``{`` / ``}`` chars from the MarkdownV2 escape table (mentioned
    explicitly in the prose as characters the LLM must not emit raw) are
    not counted as interpolations.
    """
    out = _build_telegram_channel_context_fragment(_state("telegram"))
    placeholders_in_output = re.findall(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", out)
    allowed = {"tenant_slug", "ruta"}
    unexpected = set(placeholders_in_output) - allowed
    assert not unexpected, (
        f"Unexpected curly-brace placeholders in cacheable fragment: {sorted(unexpected)}. "
        "These would break the Anthropic prompt cache prefix invariance."
    )


def test_fragment_byte_identical_across_calls_same_channel() -> None:
    """Two invocations with channel='telegram' must yield the SAME bytes (cache invariance)."""
    a = _build_telegram_channel_context_fragment(_state("telegram"))
    b = _build_telegram_channel_context_fragment(_state("telegram"))
    assert a == b
    assert a.encode("utf-8") == b.encode("utf-8")


def test_fragment_byte_identical_across_tenants() -> None:
    """Cross-tenant same-channel calls must yield identical bytes (cross-tenant cache slot)."""
    state_a = {
        "client_context": {"channel": "telegram", "tenant_id": "tenant-a"},
        "tenant_id": "tenant-a",
    }
    state_b = {
        "client_context": {"channel": "telegram", "tenant_id": "tenant-b"},
        "tenant_id": "tenant-b",
    }
    assert _build_telegram_channel_context_fragment(state_a) == _build_telegram_channel_context_fragment(state_b)


# ── Slot registration ───────────────────────────────────────────────────


def test_telegram_channel_context_slot_registered_in_enum() -> None:
    assert hasattr(PromptFragment, "TELEGRAM_CHANNEL_CONTEXT")


def test_telegram_channel_context_in_cacheable_fragments() -> None:
    assert PromptFragment.TELEGRAM_CHANNEL_CONTEXT in CACHEABLE_FRAGMENTS


def test_telegram_channel_context_position_after_marketing_kb_hint_before_lighthouse() -> None:
    """Slot ordering preserves F10 anchor + lighthouse positions."""
    cacheable = list(CACHEABLE_FRAGMENTS)
    idx_kb = cacheable.index(PromptFragment.MARKETING_KB_HINT)
    idx_telegram = cacheable.index(PromptFragment.TELEGRAM_CHANNEL_CONTEXT)
    idx_lighthouse = cacheable.index(PromptFragment.LIGHTHOUSE)
    assert idx_kb < idx_telegram < idx_lighthouse


def test_telegram_channel_context_in_full_order() -> None:
    """The new fragment must be slotted into PROMPT_FRAGMENT_ORDER (arch-test invariant)."""
    assert PromptFragment.TELEGRAM_CHANNEL_CONTEXT in PROMPT_FRAGMENT_ORDER
