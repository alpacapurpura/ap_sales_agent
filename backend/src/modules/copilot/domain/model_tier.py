"""ModelTier enum and metadata — maps tiers to LLM model names and pricing."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ModelTier(StrEnum):
    """Routing tier for LLM selection.

    Ordered by cost/capability ascending: NANO < MINI < REASONING < HEAVY.
    """

    NANO = "nano"
    MINI = "mini"
    REASONING = "reasoning"
    HEAVY = "heavy"


@dataclass(frozen=True, slots=True)
class TierMetadata:
    """Static metadata for a model tier.

    All prices are USD per 1M tokens.
    """

    tier: ModelTier
    model_name: str
    price_input_per_1m: float
    price_output_per_1m: float
    price_cached_input_per_1m: float | None
    context_window_tokens: int
    supports_caching: bool
    is_reasoning: bool


TIER_METADATA: dict[ModelTier, TierMetadata] = {
    ModelTier.NANO: TierMetadata(
        tier=ModelTier.NANO,
        model_name="gpt-5.4-nano",
        price_input_per_1m=0.20,
        price_output_per_1m=1.25,
        price_cached_input_per_1m=0.02,
        context_window_tokens=1_000_000,
        supports_caching=True,
        is_reasoning=False,
    ),
    ModelTier.MINI: TierMetadata(
        tier=ModelTier.MINI,
        model_name="gpt-5.4-mini",
        price_input_per_1m=0.75,
        price_output_per_1m=4.50,
        price_cached_input_per_1m=0.075,
        context_window_tokens=1_000_000,
        supports_caching=True,
        is_reasoning=False,
    ),
    ModelTier.REASONING: TierMetadata(
        tier=ModelTier.REASONING,
        model_name="o4-mini",
        price_input_per_1m=1.10,
        price_output_per_1m=4.40,
        price_cached_input_per_1m=None,
        context_window_tokens=200_000,
        supports_caching=False,
        is_reasoning=True,
    ),
    ModelTier.HEAVY: TierMetadata(
        tier=ModelTier.HEAVY,
        model_name="o3",
        price_input_per_1m=2.00,
        price_output_per_1m=8.00,
        price_cached_input_per_1m=None,
        context_window_tokens=200_000,
        supports_caching=False,
        is_reasoning=True,
    ),
}
