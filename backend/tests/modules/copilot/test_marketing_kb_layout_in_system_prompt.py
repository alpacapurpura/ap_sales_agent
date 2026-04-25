"""F10: marketing KB hint sits in the cacheable prefix and is rendered."""

from __future__ import annotations

from src.modules.copilot.application.orchestrator.system_prompt_layout import (
    CACHEABLE_FRAGMENTS,
    PROMPT_FRAGMENT_ORDER,
    PromptFragment,
    compose_system_prompt,
)


def test_marketing_kb_hint_in_cacheable_fragments() -> None:
    """The hint must live in the cacheable prefix, not the volatile tail."""
    assert PromptFragment.MARKETING_KB_HINT in CACHEABLE_FRAGMENTS
    assert PromptFragment.MARKETING_KB_HINT in PROMPT_FRAGMENT_ORDER


def test_marketing_kb_hint_after_tools_hint_before_lighthouse() -> None:
    """Order: ``tools_hint → marketing_kb_hint → lighthouse``.

    The hint follows the static tools hint (because it instructs how to
    use ``knowledge_search``) and precedes the per-tenant lighthouse so
    the cross-tenant cacheable block stays contiguous.
    """
    order = list(CACHEABLE_FRAGMENTS)
    tools_idx = order.index(PromptFragment.STATIC_TOOLS_HINT)
    kb_idx = order.index(PromptFragment.MARKETING_KB_HINT)
    light_idx = order.index(PromptFragment.LIGHTHOUSE)
    assert tools_idx < kb_idx < light_idx


def test_compose_renders_marketing_kb_hint_text() -> None:
    """``compose_system_prompt`` should include the F10 hint when slotted."""
    from src.modules.copilot.application.orchestrator.graph import (
        _build_marketing_kb_hint_fragment,
    )

    hint = _build_marketing_kb_hint_fragment()
    assert "knowledge_search" in hint
    assert "Hormozi" in hint
    assert "StoryBrand" in hint
    assert "cita el método" in hint.lower()

    composed = compose_system_prompt({PromptFragment.MARKETING_KB_HINT: hint})
    assert "knowledge_search" in composed
