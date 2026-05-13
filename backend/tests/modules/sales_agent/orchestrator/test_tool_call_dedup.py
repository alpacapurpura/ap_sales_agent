"""Sales-agent tool-call dedup mirror — same contract as copilot.

Threshold 3 → ``WARN`` (augment ToolMessage).
Hard limit 5 → ``ToolCallLoopError``.
Args distintos no cuentan como dedup.
"""

from __future__ import annotations

import os

import pytest


class TestObserveVerdicts:
    def test_first_two_calls_return_ok(self) -> None:
        from luana_core_sales_agent.application.orchestrator.tool_call_dedup import (
            DedupVerdict,
            ToolCallDedupTracker,
        )

        tracker = ToolCallDedupTracker()
        assert tracker.observe("create_payment_link", {"product_id": "abc"}) == DedupVerdict.OK
        assert tracker.observe("create_payment_link", {"product_id": "abc"}) == DedupVerdict.OK

    def test_third_call_returns_warn(self) -> None:
        from luana_core_sales_agent.application.orchestrator.tool_call_dedup import (
            DedupVerdict,
            ToolCallDedupTracker,
        )

        tracker = ToolCallDedupTracker()
        for _ in range(2):
            tracker.observe("send_summary", {"payload": "x"})
        assert tracker.observe("send_summary", {"payload": "x"}) == DedupVerdict.WARN

    def test_fifth_call_raises_loop_error(self) -> None:
        from luana_core_sales_agent.application.orchestrator.tool_call_dedup import (
            ToolCallDedupTracker,
            ToolCallLoopError,
        )

        tracker = ToolCallDedupTracker()
        for _ in range(4):
            tracker.observe("schedule_demo", {"slot": "11:00"})
        with pytest.raises(ToolCallLoopError) as exc_info:
            tracker.observe("schedule_demo", {"slot": "11:00"})
        assert exc_info.value.tool_name == "schedule_demo"
        assert exc_info.value.repeat_count == 5

    def test_different_args_do_not_dedup(self) -> None:
        from luana_core_sales_agent.application.orchestrator.tool_call_dedup import (
            DedupVerdict,
            ToolCallDedupTracker,
        )

        tracker = ToolCallDedupTracker()
        for slot in ("11:00", "12:00", "13:00", "14:00", "15:00", "16:00"):
            assert tracker.observe("schedule_demo", {"slot": slot}) == DedupVerdict.OK


class TestEnvVars:
    def test_threshold_overridable_via_env(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("SALES_AGENT_TOOL_CALL_DEDUP_THRESHOLD", "2")
        monkeypatch.setenv("SALES_AGENT_TOOL_CALL_DEDUP_HARD_LIMIT", "4")
        # Re-import to pick up the new env values.
        import importlib

        import src.modules.sales_agent.application.orchestrator.tool_call_dedup as mod

        importlib.reload(mod)
        assert mod.DEFAULT_DEDUP_THRESHOLD == 2
        assert mod.DEFAULT_DEDUP_HARD_LIMIT == 4
        # Restore defaults.
        monkeypatch.delenv("SALES_AGENT_TOOL_CALL_DEDUP_THRESHOLD", raising=False)
        monkeypatch.delenv("SALES_AGENT_TOOL_CALL_DEDUP_HARD_LIMIT", raising=False)
        importlib.reload(mod)


class TestAugmentToolMessage:
    def test_warn_augments_with_anti_loop_directive(self) -> None:
        from luana_core_sales_agent.application.orchestrator.tool_call_dedup import (
            augment_tool_message_for_warn,
        )

        out = augment_tool_message_for_warn(
            tool_name="create_payment_link",
            tool_args={"product_id": "abc"},
            original_content='{"link":"https://mpago.la/abc"}',
        )
        assert "GUARD ANTI-LOOP" in out
        assert "create_payment_link" in out
        assert '{"link":"https://mpago.la/abc"}' in out


class TestStableHash:
    def test_dict_key_order_does_not_matter(self) -> None:
        from luana_core_sales_agent.application.orchestrator.tool_call_dedup import hash_tool_args

        assert hash_tool_args({"a": 1, "b": 2}) == hash_tool_args({"b": 2, "a": 1})

    def test_none_and_empty_dict_collapse(self) -> None:
        from luana_core_sales_agent.application.orchestrator.tool_call_dedup import hash_tool_args

        assert hash_tool_args(None) == hash_tool_args({})


class TestEnvVarsAreSalesAgentScoped:
    def test_threshold_default_3(self) -> None:
        # Without env override the default mirrors copilot (3 / 5).
        os.environ.pop("SALES_AGENT_TOOL_CALL_DEDUP_THRESHOLD", None)
        os.environ.pop("SALES_AGENT_TOOL_CALL_DEDUP_HARD_LIMIT", None)
        import importlib

        import src.modules.sales_agent.application.orchestrator.tool_call_dedup as mod

        importlib.reload(mod)
        assert mod.DEFAULT_DEDUP_THRESHOLD == 3
        assert mod.DEFAULT_DEDUP_HARD_LIMIT == 5
