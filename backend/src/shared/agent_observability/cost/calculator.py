"""Cost calculator — pure function over tokens + pricing snapshot.

The result lands in ``copilot_llm_call.cost_usd`` (NUMERIC(16,10)), so we
keep everything in ``Decimal`` and never touch ``float``. The handler
adds 10 fractional zeros when persisting; here we expose the raw
arithmetic and let the schema decide truncation.

Token semantics (LangChain ``usage_metadata`` normalised across
providers):

* ``input_tokens``        — total input tokens reported by the provider,
  *including* any cached portion. ``input_token_details.cache_read``
  carries the cached subset.
* ``cached_read_tokens``  — subset of ``input_tokens`` served from prefix
  cache (OpenAI) or prompt cache (Anthropic). Priced at
  ``cache_read_cost_per_token``, not ``input_cost_per_token``.
* ``cached_write_tokens`` — Anthropic-only ``cache_creation`` bucket.
  Anthropic charges a markup over input_cost when the write happens.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Protocol


class _PricingLike(Protocol):
    """Minimal interface — both ``ModelPricingSnapshotModel`` and ``_EstimatedSnapshot``."""

    input_cost_per_token: Decimal
    output_cost_per_token: Decimal
    cache_read_cost_per_token: Decimal | None
    cache_write_cost_per_token: Decimal | None


def calculate_cost(
    *,
    input_tokens: int,
    output_tokens: int,
    cached_read_tokens: int,
    cached_write_tokens: int,
    pricing: _PricingLike,
) -> Decimal:
    """Return the total USD cost for one LLM call as a ``Decimal``."""
    cache_read_rate = pricing.cache_read_cost_per_token or Decimal(0)
    cache_write_rate = pricing.cache_write_cost_per_token or Decimal(0)

    # Cached reads are billed at the discount rate; the rest of the input
    # bucket pays the full rate.
    uncached_input = max(input_tokens - cached_read_tokens, 0)

    input_cost = uncached_input * pricing.input_cost_per_token
    cache_read_cost = cached_read_tokens * cache_read_rate
    cache_write_cost = cached_write_tokens * cache_write_rate
    output_cost = output_tokens * pricing.output_cost_per_token

    return input_cost + cache_read_cost + cache_write_cost + output_cost


__all__ = ["calculate_cost"]
