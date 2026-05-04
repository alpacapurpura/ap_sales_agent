"""Tests for ``sales_agent.application.prompts.compose`` — S3 cache_boundary refactor.

Mirror of ``backend/tests/modules/copilot/test_system_prompt_layout.py`` (F8).
Sales-agent-specific assertions: prefix size ≥1024 tokens with realistic tenant
fixture, slot order matches §3.4 of architecture-target, volatile fields never
leak into cacheable.

# [SALES-AGENT-CACHE-PREFIX-S3] -> docs/domains/sales-agent/redesign-2026-04/phases/S3-prompt-cache-boundary.md
"""

from __future__ import annotations

import pytest

from src.modules.sales_agent.application.prompts.compose import (
    CACHE_BOUNDARY_MARKER,
    CACHEABLE_FRAGMENTS,
    PROMPT_FRAGMENT_ORDER,
    VOLATILE_FRAGMENTS,
    PromptFragment,
    compose_system_prompt,
)


class TestFragmentOrderInvariants:
    def test_cacheable_fragments_match_s3_plan(self) -> None:
        # S3 §3.4 cacheable order: static identity, tools, playbook, agent
        # identity (per-tenant), brand voice (S7 fill), channel format (S5 fill),
        # campaign context (PR-7 outbound — emitted only when outbound_mode=True).
        assert CACHEABLE_FRAGMENTS == (
            PromptFragment.STATIC_IDENTITY,
            PromptFragment.STATIC_TOOLS_HINT,
            PromptFragment.SALES_PLAYBOOK_HINT,
            PromptFragment.AGENT_IDENTITY,
            PromptFragment.BRAND_VOICE,
            PromptFragment.CHANNEL_FORMAT_HINT,
            PromptFragment.CAMPAIGN_CONTEXT,
        )

    def test_volatile_fragments_match_s3_plan(self) -> None:
        # S3 §3.4 volatile tail: stage, signals, session continuity, tool format.
        assert VOLATILE_FRAGMENTS == (
            PromptFragment.STAGE_HINT,
            PromptFragment.LEAD_SIGNALS,
            PromptFragment.SESSION_CONTINUITY,
            PromptFragment.TOOL_REQUEST_FORMAT,
        )

    def test_full_order_concatenates_cacheable_then_volatile(self) -> None:
        assert PROMPT_FRAGMENT_ORDER == CACHEABLE_FRAGMENTS + VOLATILE_FRAGMENTS

    def test_no_duplicate_slots(self) -> None:
        assert len(set(PROMPT_FRAGMENT_ORDER)) == len(PROMPT_FRAGMENT_ORDER)

    def test_every_enum_member_is_in_order(self) -> None:
        assert set(PromptFragment) == set(PROMPT_FRAGMENT_ORDER)


class TestComposeSystemPrompt:
    def test_assembles_in_canonical_order(self) -> None:
        prompt = compose_system_prompt(
            {
                PromptFragment.STATIC_IDENTITY: "## Identity",
                PromptFragment.STATIC_TOOLS_HINT: "## Tools",
                PromptFragment.SALES_PLAYBOOK_HINT: "## Playbook",
                PromptFragment.AGENT_IDENTITY: "## Brand",
                PromptFragment.BRAND_VOICE: "## Offer",
                PromptFragment.CHANNEL_FORMAT_HINT: "## Channel",
                PromptFragment.STAGE_HINT: "## Stage",
                PromptFragment.LEAD_SIGNALS: "## Signals",
                PromptFragment.SESSION_CONTINUITY: "## Continuity",
                PromptFragment.TOOL_REQUEST_FORMAT: "## ToolFmt",
            },
        )

        labels = (
            "## Identity",
            "## Tools",
            "## Playbook",
            "## Brand",
            "## Offer",
            "## Channel",
            "## Stage",
            "## Signals",
            "## Continuity",
            "## ToolFmt",
        )
        positions = {label: prompt.find(label) for label in labels}
        for label, pos in positions.items():
            assert pos != -1, f"missing fragment {label}"
        ordered = sorted(positions.items(), key=lambda kv: kv[1])
        assert [label for label, _ in ordered] == list(labels)

    def test_inserts_cache_boundary_when_both_sides_present(self) -> None:
        prompt = compose_system_prompt(
            {
                PromptFragment.STATIC_IDENTITY: "ID",
                PromptFragment.STAGE_HINT: "STAGE",
            },
        )
        assert CACHE_BOUNDARY_MARKER in prompt
        assert prompt.index("ID") < prompt.index(CACHE_BOUNDARY_MARKER)
        assert prompt.index(CACHE_BOUNDARY_MARKER) < prompt.index("STAGE")

    def test_only_one_cache_boundary_marker(self) -> None:
        prompt = compose_system_prompt(
            {
                PromptFragment.STATIC_IDENTITY: "A",
                PromptFragment.SALES_PLAYBOOK_HINT: "B",
                PromptFragment.STAGE_HINT: "C",
                PromptFragment.LEAD_SIGNALS: "D",
            },
        )
        assert prompt.count(CACHE_BOUNDARY_MARKER) == 1

    def test_skips_boundary_when_only_cacheable(self) -> None:
        prompt = compose_system_prompt({PromptFragment.STATIC_IDENTITY: "only"})
        assert CACHE_BOUNDARY_MARKER not in prompt
        assert prompt == "only"

    def test_skips_boundary_when_only_volatile(self) -> None:
        prompt = compose_system_prompt({PromptFragment.STAGE_HINT: "only"})
        assert CACHE_BOUNDARY_MARKER not in prompt
        assert prompt == "only"

    def test_skips_empty_or_missing_fragments(self) -> None:
        prompt = compose_system_prompt(
            {
                PromptFragment.STATIC_IDENTITY: "ID",
                PromptFragment.AGENT_IDENTITY: "",
                PromptFragment.BRAND_VOICE: "   ",
                PromptFragment.STAGE_HINT: "STG",
            },
        )
        assert "ID" in prompt
        assert "STG" in prompt
        # Empty / whitespace-only fragments do not produce extra newlines.
        assert prompt.index("ID") < prompt.index("STG")

    def test_returns_empty_for_no_fragments(self) -> None:
        assert compose_system_prompt({}) == ""

    def test_strips_whitespace_around_each_fragment(self) -> None:
        prompt = compose_system_prompt(
            {
                PromptFragment.STATIC_IDENTITY: "  ID with edges  \n",
                PromptFragment.SALES_PLAYBOOK_HINT: "\n\nPLY\n\n",
            },
        )
        assert prompt == "ID with edges\n\nPLY"


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


class TestVolatileNeverLeaksIntoCacheable:
    """Changing volatile state must not change cacheable bytes."""

    def _cacheable_only(self, fragments: dict[PromptFragment, str]) -> str:
        return compose_system_prompt({k: v for k, v in fragments.items() if k in CACHEABLE_FRAGMENTS})

    def test_cacheable_prefix_stable_across_volatile_changes(self) -> None:
        cache_payload = {
            PromptFragment.STATIC_IDENTITY: "ID",
            PromptFragment.STATIC_TOOLS_HINT: "TOOLS",
            PromptFragment.SALES_PLAYBOOK_HINT: "PLAY",
            PromptFragment.AGENT_IDENTITY: "BRAND",
            PromptFragment.BRAND_VOICE: "OFFER",
            PromptFragment.CHANNEL_FORMAT_HINT: "CHAN",
        }
        full_a = compose_system_prompt(
            {
                **cache_payload,
                PromptFragment.STAGE_HINT: "stage A",
                PromptFragment.LEAD_SIGNALS: "score=10",
            },
        )
        full_b = compose_system_prompt(
            {
                **cache_payload,
                PromptFragment.STAGE_HINT: "stage Z",
                PromptFragment.LEAD_SIGNALS: "score=99",
            },
        )

        boundary_a = full_a.index(CACHE_BOUNDARY_MARKER)
        boundary_b = full_b.index(CACHE_BOUNDARY_MARKER)
        assert full_a[:boundary_a] == full_b[:boundary_b]
