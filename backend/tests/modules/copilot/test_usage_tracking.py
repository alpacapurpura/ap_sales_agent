"""Tests for copilot token usage tracking and cost calculation."""

from __future__ import annotations

from langchain_core.messages import AIMessage

from src.modules.copilot.application.orchestrator.usage_tracking import (
    UsageAccumulator,
    calculate_cost,
)

# ── calculate_cost ────────────────────────────────────────────────────


class TestCalculateCost:
    def test_gpt4o_cost(self) -> None:
        # 1000 prompt + 500 completion @ gpt-4o = 0.001 * 2.50 + 0.0005 * 10.00 = $0.0075
        cost = calculate_cost(prompt_tokens=1000, completion_tokens=500, model="gpt-4o")
        assert abs(cost - 0.007500) < 1e-8

    def test_gpt4o_mini_cost(self) -> None:
        # 1000 prompt + 500 completion @ gpt-4o-mini = 0.001 * 0.15 + 0.0005 * 0.60 = $0.000450
        cost = calculate_cost(prompt_tokens=1000, completion_tokens=500, model="gpt-4o-mini")
        assert abs(cost - 0.000450) < 1e-8

    def test_zero_tokens_is_zero(self) -> None:
        assert calculate_cost(0, 0, "gpt-4o") == 0.0

    def test_unknown_model_falls_back_to_gpt4o(self) -> None:
        known = calculate_cost(1000, 500, "gpt-4o")
        unknown = calculate_cost(1000, 500, "gpt-99-turbo-ultra")
        assert known == unknown

    def test_only_prompt_tokens(self) -> None:
        # 2000 prompt, 0 completion @ gpt-4o = 0.002 * 2.50 = $0.005
        cost = calculate_cost(prompt_tokens=2000, completion_tokens=0, model="gpt-4o")
        assert abs(cost - 0.005) < 1e-8

    def test_only_completion_tokens(self) -> None:
        # 0 prompt, 1000 completion @ gpt-4o = 0.001 * 10.00 = $0.010
        cost = calculate_cost(prompt_tokens=0, completion_tokens=1000, model="gpt-4o")
        assert abs(cost - 0.010) < 1e-8


# ── UsageAccumulator ──────────────────────────────────────────────────


def _make_ai_message(
    input_tokens: int,
    output_tokens: int,
    model_name: str | None = None,
) -> AIMessage:
    """Helper: AIMessage with usage_metadata and optional response_metadata model_name."""
    msg = AIMessage(content="test response")
    msg.usage_metadata = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }
    if model_name:
        msg.response_metadata = {"model_name": model_name}
    return msg


def _make_end_event(
    input_tokens: int,
    output_tokens: int,
    model_name: str | None = None,
) -> dict:
    """Helper: on_chat_model_end event dict."""
    return {
        "event": "on_chat_model_end",
        "data": {
            "output": _make_ai_message(input_tokens, output_tokens, model_name),
        },
    }


class TestUsageAccumulator:
    def test_initial_state_is_zero(self) -> None:
        acc = UsageAccumulator(model="gpt-4o")
        assert acc.prompt_tokens == 0
        assert acc.completion_tokens == 0
        assert acc.total_tokens == 0
        assert acc.cost_usd == 0.0

    def test_update_from_end_event(self) -> None:
        acc = UsageAccumulator(model="gpt-4o")
        acc.update_from_event(_make_end_event(100, 50))
        assert acc.prompt_tokens == 100
        assert acc.completion_tokens == 50

    def test_accumulates_multiple_end_events(self) -> None:
        """Multi-turn tool calling emits multiple on_chat_model_end events."""
        acc = UsageAccumulator(model="gpt-4o")
        acc.update_from_event(_make_end_event(100, 50))
        acc.update_from_event(_make_end_event(200, 75))
        assert acc.prompt_tokens == 300
        assert acc.completion_tokens == 125

    def test_total_tokens_is_sum(self) -> None:
        acc = UsageAccumulator(model="gpt-4o")
        acc.update_from_event(_make_end_event(300, 125))
        assert acc.total_tokens == 425

    def test_cost_usd_computed_from_totals(self) -> None:
        acc = UsageAccumulator(model="gpt-4o")
        acc.update_from_event(_make_end_event(1000, 500))
        expected = calculate_cost(1000, 500, "gpt-4o")
        assert acc.cost_usd == expected

    def test_model_updated_from_response_metadata(self) -> None:
        acc = UsageAccumulator(model="gpt-4o")
        acc.update_from_event(_make_end_event(10, 5, model_name="gpt-4o-mini"))
        assert acc.model == "gpt-4o-mini"

    def test_model_not_overwritten_if_missing(self) -> None:
        """If response_metadata lacks model_name, keep current model."""
        acc = UsageAccumulator(model="gpt-4o")
        acc.update_from_event(_make_end_event(10, 5, model_name=None))
        assert acc.model == "gpt-4o"

    def test_ignores_non_end_events(self) -> None:
        acc = UsageAccumulator(model="gpt-4o")
        acc.update_from_event({"event": "on_chat_model_stream", "data": {}})
        acc.update_from_event({"event": "on_tool_start", "data": {}})
        assert acc.prompt_tokens == 0
        assert acc.completion_tokens == 0

    def test_ignores_end_event_without_usage_metadata(self) -> None:
        msg = AIMessage(content="no usage")
        # Intentionally NOT setting usage_metadata
        acc = UsageAccumulator(model="gpt-4o")
        acc.update_from_event({"event": "on_chat_model_end", "data": {"output": msg}})
        assert acc.prompt_tokens == 0

    def test_ignores_end_event_with_non_aimessage_output(self) -> None:
        acc = UsageAccumulator(model="gpt-4o")
        acc.update_from_event({"event": "on_chat_model_end", "data": {"output": "plain string"}})
        assert acc.prompt_tokens == 0

    def test_as_log_dict(self) -> None:
        acc = UsageAccumulator(model="gpt-4o")
        acc.update_from_event(_make_end_event(1000, 500))
        d = acc.as_log_dict()
        assert d["model"] == "gpt-4o"
        assert d["prompt_tokens"] == 1000
        assert d["completion_tokens"] == 500
        assert d["total_tokens"] == 1500
        assert "cost_usd" in d

    def test_gpt4o_mini_cost_in_accumulator(self) -> None:
        acc = UsageAccumulator(model="gpt-4o-mini")
        acc.update_from_event(_make_end_event(1000, 500))
        expected = calculate_cost(1000, 500, "gpt-4o-mini")
        assert acc.cost_usd == expected
