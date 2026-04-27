"""Tests for the parent-agent tool-call dedup guard.

Background — 2026-04-27 incident (conversation fbc79125-…):
    Kimi K2.6 emitted the same ``get_module_data(module='offer', section='X')``
    tool call repeatedly with rotating section names. Nothing capped it; the
    deep-agent graph hit ``GraphRecursionError`` after 25 nodes, the SSE
    stream broke, and the conversation persisted as empty. Tokens burned,
    user lost work, traces lied (``status='ok'`` for an error path).

The dedup guard lives BELOW LangGraph (we do not depend on its config):
    - Tracker observes every ``on_tool_end`` event in a turn.
    - WARN at ``threshold`` hits — augment ToolMessage content with a strong
      anti-loop directive so the LLM sees "stop repeating".
    - ABORT at ``hard_limit`` hits — raise ``ToolCallLoopError`` so the
      orchestrator ends the turn gracefully instead of running until the
      recursion limit.

Both knobs are env-configurable so ops can dial them without redeploy.
"""

from __future__ import annotations

import pytest

from src.modules.copilot.application.orchestrator.tool_call_dedup import (
    DedupVerdict,
    ToolCallDedupTracker,
    ToolCallLoopError,
    augment_tool_message_for_warn,
    hash_tool_args,
)

# ── Argument hashing ─────────────────────────────────────────────────


class TestHashToolArgs:
    """Hashing must be stable, dict-order independent, and tolerant of
    LangChain's variant payload shapes."""

    def test_same_dict_hashes_identically(self) -> None:
        a = {"module": "offer", "section": "psychology"}
        b = {"section": "psychology", "module": "offer"}
        assert hash_tool_args(a) == hash_tool_args(b)

    def test_different_dicts_hash_differently(self) -> None:
        a = {"module": "offer", "section": "psychology"}
        b = {"module": "offer", "section": "identity"}
        assert hash_tool_args(a) != hash_tool_args(b)

    def test_string_payload_hashes(self) -> None:
        assert hash_tool_args("{'asset_id': 'abc'}") == hash_tool_args(
            "{'asset_id': 'abc'}",
        )

    def test_none_payload_normalises(self) -> None:
        # Two missing-arg calls must collapse into the same bucket so the
        # tracker counts them as one repeated tool call.
        assert hash_tool_args(None) == hash_tool_args(None)
        assert hash_tool_args(None) == hash_tool_args({})


# ── Tracker verdicts ─────────────────────────────────────────────────


class TestToolCallDedupTracker:
    def test_first_three_calls_with_different_args_all_ok(self) -> None:
        """Different args = different work — must never warn."""
        t = ToolCallDedupTracker(threshold=3, hard_limit=5)
        v1 = t.observe("get_module_data", {"module": "brand"})
        v2 = t.observe("get_module_data", {"module": "offer"})
        v3 = t.observe("get_module_data", {"module": "offer", "section": "psychology"})
        assert v1 is DedupVerdict.OK
        assert v2 is DedupVerdict.OK
        assert v3 is DedupVerdict.OK

    def test_warn_fires_at_threshold(self) -> None:
        t = ToolCallDedupTracker(threshold=3, hard_limit=5)
        args = {"module": "offer", "section": "psychology"}
        assert t.observe("get_module_data", args) is DedupVerdict.OK
        assert t.observe("get_module_data", args) is DedupVerdict.OK
        # 3rd identical call → warn so the LLM gets a course-correction
        # injected into the next ToolMessage.
        assert t.observe("get_module_data", args) is DedupVerdict.WARN

    def test_abort_raises_at_hard_limit(self) -> None:
        t = ToolCallDedupTracker(threshold=3, hard_limit=5)
        args = {"module": "offer", "section": "psychology"}
        verdicts: list[DedupVerdict] = []
        for _ in range(4):
            verdicts.append(t.observe("get_module_data", args))
        # 5th identical call → must raise so the orchestrator can end the
        # turn cleanly. Burning more tokens is unacceptable past this point.
        with pytest.raises(ToolCallLoopError) as exc:
            t.observe("get_module_data", args)
        # Exception payload must carry the offending call so traces are
        # actionable without re-deriving from the tracker state.
        assert exc.value.tool_name == "get_module_data"
        assert exc.value.repeat_count == 5

    def test_dedup_keys_segregate_by_tool_name(self) -> None:
        t = ToolCallDedupTracker(threshold=2, hard_limit=4)
        # Same args on two different tools must NOT collapse — they are
        # legitimately different calls.
        assert t.observe("get_module_data", {"x": 1}) is DedupVerdict.OK
        assert t.observe("propose_field_updates", {"x": 1}) is DedupVerdict.OK

    def test_threshold_one_means_warn_immediately(self) -> None:
        """A threshold of 1 effectively disables the WARN tier (every call
        warns) — used by tests but not realistic in prod. Smoke test only.
        """
        t = ToolCallDedupTracker(threshold=1, hard_limit=99)
        assert t.observe("foo", {}) is DedupVerdict.WARN

    def test_default_thresholds_match_settings(self) -> None:
        """Defaults must match the documented production values so an
        operator reading code without env vars sees the actual behaviour.
        """
        t = ToolCallDedupTracker()
        assert t.threshold == 3
        assert t.hard_limit == 5


# ── ToolMessage augmentation ─────────────────────────────────────────


class TestAugmentToolMessageForWarn:
    def test_directive_includes_tool_name_and_args(self) -> None:
        augmented = augment_tool_message_for_warn(
            tool_name="get_module_data",
            tool_args={"module": "offer", "section": "psychology"},
            original_content="content_X",
        )
        # Directive must mention the tool + count so the LLM cannot ignore.
        assert "get_module_data" in augmented
        assert "module" in augmented or "args" in augmented
        # The original content must remain available — the LLM still needs
        # the data; we just add a guard rail above it.
        assert "content_X" in augmented

    def test_directive_in_spanish_neutro_tuteo(self) -> None:
        """User-facing surfaces must follow the Spanish-text rule (no voseo,
        tuteo). The directive sits in the agent's context, not the user's
        screen, but reaching the LLM in neutral Spanish keeps the agent's
        own outputs aligned with the brand's voice rule.
        """
        augmented = augment_tool_message_for_warn(
            tool_name="get_module_data",
            tool_args={},
            original_content="x",
        )
        lower = augmented.lower()
        # No voseo verb forms anywhere.
        assert "podés" not in lower
        assert "tenés" not in lower
        assert "mirá" not in lower
        # Imperative tuteo is fine, e.g. "responde", "deja", "usa".

    def test_handles_none_content(self) -> None:
        # Some tool envelopes carry empty content (Command shape). The
        # augmenter must not blow up.
        out = augment_tool_message_for_warn(
            tool_name="x",
            tool_args=None,
            original_content=None,
        )
        assert isinstance(out, str)
        assert "x" in out
