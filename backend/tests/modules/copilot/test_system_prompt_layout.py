"""Tests for ``system_prompt_layout`` — F8 §5.2 cache-friendly fragment ordering.

# [COPILOT-CACHE-PREFIX-F8] -> docs/domains/copilot/redesign-2026-04/phases/F8-routing-cost-optim.md
"""

from __future__ import annotations

import pytest

from luana_core_copilot.application.orchestrator.system_prompt_layout import (
    CACHE_BOUNDARY_MARKER,
    CACHEABLE_FRAGMENTS,
    PROMPT_FRAGMENT_ORDER,
    VOLATILE_FRAGMENTS,
    PromptFragment,
    compose_system_prompt,
)


class TestFragmentOrderInvariants:
    def test_cacheable_fragments_match_f8_plan(self) -> None:
        # F8 §5.2 order extended in F10 + PI-5 PR-2 (D-PI5-009): static
        # instructions, tools schema, marketing_kb_hint (cite framework — F10),
        # telegram_channel_context (cross-tenant per-channel cacheable —
        # PI-5 PR-2), lighthouse, editable catalog, active providers list.
        assert CACHEABLE_FRAGMENTS == (
            PromptFragment.STATIC_IDENTITY,
            PromptFragment.STATIC_TOOLS_HINT,
            PromptFragment.MARKETING_KB_HINT,
            PromptFragment.TELEGRAM_CHANNEL_CONTEXT,
            PromptFragment.LIGHTHOUSE,
            PromptFragment.EDITABLE_CATALOG,
            PromptFragment.MODULES_LIST,
        )

    def test_volatile_fragments_match_f8_plan(self) -> None:
        # F8 §5.2 order tail: studio snapshot, workflow state, inspirations.
        assert VOLATILE_FRAGMENTS == (
            PromptFragment.STUDIO_SNAPSHOT,
            PromptFragment.WORKFLOW_STATE,
            PromptFragment.INSPIRATIONS,
        )

    def test_full_order_concatenates_cacheable_then_volatile(self) -> None:
        assert PROMPT_FRAGMENT_ORDER == CACHEABLE_FRAGMENTS + VOLATILE_FRAGMENTS

    def test_no_duplicate_slots(self) -> None:
        assert len(set(PROMPT_FRAGMENT_ORDER)) == len(PROMPT_FRAGMENT_ORDER)

    def test_every_enum_member_is_in_order(self) -> None:
        # Catches the case where someone adds a PromptFragment value but
        # forgets to slot it into the canonical order.
        assert set(PromptFragment) == set(PROMPT_FRAGMENT_ORDER)


class TestComposeSystemPrompt:
    def test_assembles_in_canonical_order(self) -> None:
        prompt = compose_system_prompt(
            {
                PromptFragment.STATIC_IDENTITY: "## Identity",
                PromptFragment.STATIC_TOOLS_HINT: "## Tools",
                PromptFragment.LIGHTHOUSE: "## Lighthouse",
                PromptFragment.EDITABLE_CATALOG: "## Editable",
                PromptFragment.MODULES_LIST: "## Modules",
                PromptFragment.STUDIO_SNAPSHOT: "## Snapshot",
                PromptFragment.WORKFLOW_STATE: "## Workflow",
                PromptFragment.INSPIRATIONS: "## Inspirations",
            },
        )

        positions = {
            label: prompt.find(label)
            for label in (
                "## Identity",
                "## Tools",
                "## Lighthouse",
                "## Editable",
                "## Modules",
                "## Snapshot",
                "## Workflow",
                "## Inspirations",
            )
        }
        for label, pos in positions.items():
            assert pos != -1, f"missing fragment {label}"

        ordered = sorted(positions.items(), key=lambda kv: kv[1])
        assert [label for label, _ in ordered] == [
            "## Identity",
            "## Tools",
            "## Lighthouse",
            "## Editable",
            "## Modules",
            "## Snapshot",
            "## Workflow",
            "## Inspirations",
        ]

    def test_inserts_cache_boundary_when_both_sides_present(self) -> None:
        prompt = compose_system_prompt(
            {
                PromptFragment.STATIC_IDENTITY: "ID",
                PromptFragment.STUDIO_SNAPSHOT: "SNAP",
            },
        )

        assert CACHE_BOUNDARY_MARKER in prompt
        assert prompt.index("ID") < prompt.index(CACHE_BOUNDARY_MARKER)
        assert prompt.index(CACHE_BOUNDARY_MARKER) < prompt.index("SNAP")

    def test_skips_boundary_when_only_cacheable(self) -> None:
        prompt = compose_system_prompt({PromptFragment.STATIC_IDENTITY: "only"})

        assert CACHE_BOUNDARY_MARKER not in prompt
        assert prompt == "only"

    def test_skips_boundary_when_only_volatile(self) -> None:
        prompt = compose_system_prompt({PromptFragment.STUDIO_SNAPSHOT: "only"})

        assert CACHE_BOUNDARY_MARKER not in prompt
        assert prompt == "only"

    def test_skips_empty_or_missing_fragments(self) -> None:
        prompt = compose_system_prompt(
            {
                PromptFragment.STATIC_IDENTITY: "ID",
                PromptFragment.LIGHTHOUSE: "",
                PromptFragment.MODULES_LIST: "MODS",
            },
        )

        assert "ID" in prompt
        assert "MODS" in prompt
        assert prompt.index("ID") < prompt.index("MODS")

    def test_returns_empty_for_no_fragments(self) -> None:
        assert compose_system_prompt({}) == ""

    def test_strips_whitespace_around_each_fragment(self) -> None:
        prompt = compose_system_prompt(
            {
                PromptFragment.STATIC_IDENTITY: "  ID with edges  \n",
                PromptFragment.MODULES_LIST: "\n\nMODS\n\n",
            },
        )

        # Each fragment is stripped, then joined with double-newline.
        assert prompt == "ID with edges\n\nMODS"


class TestPromptFragmentEnum:
    def test_str_values_are_snake_case(self) -> None:
        for frag in PromptFragment:
            assert frag.value.islower()
            assert " " not in frag.value
            assert "-" not in frag.value

    @pytest.mark.parametrize("frag", list(PromptFragment))
    def test_each_fragment_value_is_used_as_key(self, frag: PromptFragment) -> None:
        prompt = compose_system_prompt({frag: f"<<{frag.value}>>"})
        assert f"<<{frag.value}>>" in prompt
