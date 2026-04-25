"""F8 — cache-token instrumentation in ``UsageAccumulator``.

OpenAI prefix cache reports ``cache_read`` tokens via LangChain's
``AIMessage.usage_metadata.input_token_details``. This is the *only* signal
we have for whether the prompt prefix was reused.

# [COPILOT-CACHE-PREFIX-F8] -> docs/domains/copilot/redesign-2026-04/phases/F8-routing-cost-optim.md
"""

from __future__ import annotations

import pytest
from langchain_core.messages import AIMessage

from src.modules.copilot.application.orchestrator.usage_tracking import (
    UsageAccumulator,
)


def _event(input_tokens: int, output_tokens: int, cache_read: int | None = None) -> dict:
    msg = AIMessage(content="hi")
    usage_metadata: dict[str, object] = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
    }
    if cache_read is not None:
        usage_metadata["input_token_details"] = {"cache_read": cache_read}
    msg.usage_metadata = usage_metadata
    msg.response_metadata = {"model_name": "gpt-4o-mini"}
    return {"event": "on_chat_model_end", "data": {"output": msg}}


class TestCacheTokenAccumulation:
    def test_cached_input_tokens_starts_at_zero(self) -> None:
        acc = UsageAccumulator()
        assert acc.cached_input_tokens == 0

    def test_extracts_cache_read_from_event(self) -> None:
        acc = UsageAccumulator()
        acc.update_from_event(_event(input_tokens=1500, output_tokens=200, cache_read=1024))

        assert acc.prompt_tokens == 1500
        assert acc.cached_input_tokens == 1024

    def test_handles_missing_input_token_details(self) -> None:
        acc = UsageAccumulator()
        acc.update_from_event(_event(input_tokens=500, output_tokens=100))

        assert acc.prompt_tokens == 500
        assert acc.cached_input_tokens == 0

    def test_accumulates_across_multiple_events(self) -> None:
        acc = UsageAccumulator()
        acc.update_from_event(_event(input_tokens=1500, output_tokens=200, cache_read=1000))
        acc.update_from_event(_event(input_tokens=1500, output_tokens=180, cache_read=1450))

        assert acc.prompt_tokens == 3000
        assert acc.cached_input_tokens == 2450

    @pytest.mark.parametrize(
        ("cached", "total", "expected_rate"),
        [
            (0, 1000, 0.0),
            (500, 1000, 0.5),
            (900, 1000, 0.9),
            (1024, 1024, 1.0),
            # Edge: zero prompt tokens (early stream events) → 0.0, no DivisionByZero.
            (0, 0, 0.0),
        ],
    )
    def test_cache_hit_rate_computation(
        self,
        cached: int,
        total: int,
        expected_rate: float,
    ) -> None:
        acc = UsageAccumulator()
        if total > 0:
            acc.update_from_event(
                _event(input_tokens=total, output_tokens=10, cache_read=cached),
            )
        assert acc.cache_hit_rate == pytest.approx(expected_rate)

    def test_log_dict_includes_cache_metrics(self) -> None:
        acc = UsageAccumulator()
        acc.update_from_event(_event(input_tokens=1500, output_tokens=200, cache_read=1024))

        log = acc.as_log_dict()
        assert log["cached_input_tokens"] == 1024
        # Log dict rounds the rate to 4 decimals — assert the rounded form.
        assert log["cache_hit_rate"] == pytest.approx(round(1024 / 1500, 4))
