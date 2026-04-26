"""Regression: ``turn_end`` trace data must persist cache + cost metrics.

Bug: ``CopilotOrchestrator.stream_chat`` constructed the ``turn_end`` recorder
payload as a literal dict that only carried ``total_tokens`` and ``model`` —
``cached_input_tokens``, ``cache_hit_rate`` and ``cost_usd`` (already tracked
by ``UsageAccumulator``) never reached ``copilot_trace_event``. As a result
the F8 cache instrumentation looked broken in the admin dashboard even though
``copilot_turn_usage`` structlog showed avg cache hit rate ≥0.99.

Anchor: ``[COPILOT-CACHE-PREFIX-F8]``. TP1 anomaly B1.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage

from src.modules.copilot.application.orchestrator.chat import (
    _build_turn_end_data,
    _StreamAccumulator,
)
from src.modules.copilot.application.orchestrator.usage_tracking import (
    UsageAccumulator,
)


def _ai_event(input_tokens: int, output_tokens: int, cache_read: int) -> dict:
    msg = AIMessage(content="x")
    msg.usage_metadata = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "input_token_details": {"cache_read": cache_read},
    }
    msg.response_metadata = {"model_name": "gpt-4o-2024-08-06"}
    return {"event": "on_chat_model_end", "data": {"output": msg}}


class TestBuildTurnEndData:
    def test_includes_cache_metrics_from_usage(self) -> None:
        usage = UsageAccumulator()
        usage.update_from_event(_ai_event(input_tokens=1500, output_tokens=20, cache_read=1024))
        acc = _StreamAccumulator(full_response="hola mundo", messages=[1, 2], emitted_blocks=[{"x": 1}])

        data = _build_turn_end_data(usage=usage, acc=acc)

        assert data["cached_input_tokens"] == 1024
        assert data["cache_hit_rate"] == round(1024 / 1500, 4)
        assert data["cost_usd"] > 0
        assert data["model"] == "gpt-4o-2024-08-06"

    def test_includes_stream_shape_fields(self) -> None:
        usage = UsageAccumulator()
        usage.update_from_event(_ai_event(input_tokens=200, output_tokens=10, cache_read=0))
        acc = _StreamAccumulator(
            full_response="abcdef",
            messages=["m1", "m2", "m3"],
            emitted_blocks=[{"a": 1}, {"b": 2}],
        )

        data = _build_turn_end_data(usage=usage, acc=acc)

        assert data["response_length"] == len("abcdef")
        assert data["message_count"] == 3
        assert data["block_count"] == 2

    def test_zero_prompt_tokens_yields_zero_cache_rate(self) -> None:
        usage = UsageAccumulator()
        acc = _StreamAccumulator()

        data = _build_turn_end_data(usage=usage, acc=acc)

        assert data["cached_input_tokens"] == 0
        assert data["cache_hit_rate"] == 0.0
        assert data["total_tokens"] == 0
