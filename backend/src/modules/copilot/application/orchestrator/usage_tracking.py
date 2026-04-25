"""Token usage tracking and cost estimation for copilot LLM calls.

Collects prompt_tokens + completion_tokens from LangGraph on_chat_model_end
events and computes the estimated USD cost using OpenAI's published pricing.

Usage:
    acc = UsageAccumulator(model=settings.get_model(ModelRole.AGENT))
    async for event in copilot_graph.astream_events(...):
        acc.update_from_event(event)
    logger.info("copilot_turn_cost", **acc.as_log_dict(), conversation_id=conv_id)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import structlog
from langchain_core.messages import AIMessage

logger = structlog.get_logger()

# OpenAI pricing per 1 million tokens (USD), as of April 2026.
# Update when OpenAI changes pricing.
_PRICING: dict[str, dict[str, float]] = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o-2024-08-06": {"input": 2.50, "output": 10.00},
    "gpt-4o-2024-11-20": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini-2024-07-18": {"input": 0.15, "output": 0.60},
}

_FALLBACK_MODEL = "gpt-4o"


def calculate_cost(prompt_tokens: int, completion_tokens: int, model: str) -> float:
    """Return estimated cost in USD for the given token counts and model.

    Falls back to gpt-4o pricing for unknown models.
    """
    # Match exact model name first; then try prefix (e.g. "gpt-4o-2025-xx" → gpt-4o).
    prices = _PRICING.get(model)
    if prices is None:
        for key, val in _PRICING.items():
            if model.startswith(key):
                prices = val
                break
    if prices is None:
        prices = _PRICING[_FALLBACK_MODEL]

    return (prompt_tokens * prices["input"] + completion_tokens * prices["output"]) / 1_000_000


@dataclass
class UsageAccumulator:
    """Accumulate token usage across multiple LLM calls in a single copilot turn.

    A single user turn can trigger multiple LLM calls (agent → tools → agent…).
    Each produces an on_chat_model_end event; this class sums them all.

    F8 — also accumulates ``cached_input_tokens`` from
    ``usage_metadata["input_token_details"]["cache_read"]`` so we can track
    OpenAI prefix-cache hit rate and verify the F8 §5.2 reorder is paying
    off in production. Anchor: ``[COPILOT-CACHE-PREFIX-F8]``.
    """

    model: str = field(default=_FALLBACK_MODEL)
    prompt_tokens: int = field(default=0, init=False)
    completion_tokens: int = field(default=0, init=False)
    cached_input_tokens: int = field(default=0, init=False)

    @property
    def total_tokens(self) -> int:
        """Sum of prompt and completion tokens."""
        return self.prompt_tokens + self.completion_tokens

    @property
    def cost_usd(self) -> float:
        """Estimated cost in USD for all accumulated tokens."""
        return calculate_cost(self.prompt_tokens, self.completion_tokens, self.model)

    @property
    def cache_hit_rate(self) -> float:
        """Fraction of input tokens served from cache (0.0..1.0).

        Returns 0.0 when no prompt tokens have been accumulated yet to avoid
        ``DivisionByZero`` in early stream events. Useful for the F8 §5.5
        admin dashboard.
        """
        if self.prompt_tokens <= 0:
            return 0.0
        return self.cached_input_tokens / self.prompt_tokens

    def update_from_event(self, event: dict) -> None:
        """Extract usage data from a LangGraph stream event (no-op for non-usage events)."""
        if event.get("event") != "on_chat_model_end":
            return

        output = event.get("data", {}).get("output")
        if not isinstance(output, AIMessage):
            return

        usage = getattr(output, "usage_metadata", None)
        if not usage:
            return

        self.prompt_tokens += usage.get("input_tokens", 0)
        self.completion_tokens += usage.get("output_tokens", 0)

        # OpenAI prefix-cache reads land here in LangChain's normalized
        # usage_metadata. Anthropic uses ``cache_read`` too — same field
        # name, same semantics — so this works across both providers.
        details = usage.get("input_token_details") or {}
        self.cached_input_tokens += int(details.get("cache_read", 0) or 0)

        # Update model name from actual response (may differ from configured default)
        model_name = (getattr(output, "response_metadata", None) or {}).get("model_name")
        if model_name:
            self.model = model_name

    def as_log_dict(self) -> dict:
        """Return a structured dict suitable for structlog."""
        return {
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cached_input_tokens": self.cached_input_tokens,
            "cache_hit_rate": round(self.cache_hit_rate, 4),
            "cost_usd": round(self.cost_usd, 8),
        }

    def log(self, **extra: object) -> None:
        """Emit a single structured log line with usage + any extra fields."""
        logger.info("copilot_turn_usage", **self.as_log_dict(), **extra)
