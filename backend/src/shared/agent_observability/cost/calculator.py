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

# [SALES-AGENT-COST-TIER-S12] -> docs/domains/sales-agent/redesign-2026-04/phases/S12-final-hardening-zero-debt.md

Tier pricing (S12): when LiteLLM declares
``input_cost_per_token_above_200k_tokens`` (or its output sibling), the
calculator splits the uncached input / output buckets at
``TIER_THRESHOLD = 200_000`` tokens. Tokens up to the threshold use the
base rate; tokens past the threshold use the tier rate. Cached reads /
writes always use their own rate — they are never split by tier (LiteLLM
exposes a separate ``cache_read_input_token_cost_above_200k_tokens`` for
cache tier; not yet adopted — out of scope until reconciliation surfaces
drift).

Tier rates are resolved opportunistically:

1. Direct attribute on the pricing object (typed snapshot extension).
2. ``raw_payload`` JSONB key (the LiteLLM JSON we sync verbatim).

If neither is declared, the calculator falls back to the legacy
non-tier path. Long LATAM conversations under 200k tokens are
unaffected.
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


TIER_THRESHOLD: int = 200_000
"""Token count at which LiteLLM tier pricing kicks in (S12)."""

_INPUT_TIER_KEY = "input_cost_per_token_above_200k_tokens"
_OUTPUT_TIER_KEY = "output_cost_per_token_above_200k_tokens"


def _coerce_decimal(value: object) -> Decimal | None:
    """Return ``value`` as ``Decimal`` if numeric / numeric-stringy, else ``None``.

    Defensive vs ``MagicMock`` test fixtures (their auto-attrs are not
    ``Decimal`` / ``int`` / ``str``) — the calculator silently skips tier
    resolution when the field is absent or unrecognised.
    """
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, int | float | str):
        try:
            return Decimal(str(value))
        except (ValueError, ArithmeticError):
            return None
    return None


def _resolve_tier_rate(pricing: object, key: str) -> Decimal | None:
    """Resolve a tier rate from a typed attribute or ``raw_payload`` JSONB."""
    direct = _coerce_decimal(getattr(pricing, key, None))
    if direct is not None:
        return direct
    raw = getattr(pricing, "raw_payload", None)
    if isinstance(raw, dict):
        return _coerce_decimal(raw.get(key))
    return None


def _split_at_tier(
    tokens: int,
    base_rate: Decimal,
    tier_rate: Decimal | None,
) -> Decimal:
    """Cost for ``tokens`` units split at ``TIER_THRESHOLD`` between base and tier rate."""
    if tier_rate is None or tokens <= TIER_THRESHOLD:
        return tokens * base_rate
    under = TIER_THRESHOLD * base_rate
    over = (tokens - TIER_THRESHOLD) * tier_rate
    return under + over


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
    # bucket pays the full rate (or tier rate for tokens above threshold).
    uncached_input = max(input_tokens - cached_read_tokens, 0)

    input_tier_rate = _resolve_tier_rate(pricing, _INPUT_TIER_KEY)
    output_tier_rate = _resolve_tier_rate(pricing, _OUTPUT_TIER_KEY)

    input_cost = _split_at_tier(uncached_input, pricing.input_cost_per_token, input_tier_rate)
    cache_read_cost = cached_read_tokens * cache_read_rate
    cache_write_cost = cached_write_tokens * cache_write_rate
    output_cost = _split_at_tier(output_tokens, pricing.output_cost_per_token, output_tier_rate)

    return input_cost + cache_read_cost + cache_write_cost + output_cost


__all__ = ["TIER_THRESHOLD", "calculate_cost"]
