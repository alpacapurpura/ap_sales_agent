"""Copilot model config — env-flag override layer over TIER_METADATA.

D-1 (CONTRACT PR-3): Add env-flag config layer so tier→model mapping can be
overridden at runtime without touching ``TIER_METADATA`` enum SSoT.

Environment variables (all optional — fallback to TIER_METADATA static):
  COPILOT_TIER_NANO_MODEL_NAME         model name override for NANO tier
  COPILOT_TIER_NANO_PRICE_INPUT_PER_1M  input price per 1M tokens (float str)
  COPILOT_TIER_NANO_PRICE_OUTPUT_PER_1M output price per 1M tokens (float str)
  COPILOT_TIER_NANO_CONTEXT_WINDOW_TOKENS context window (int str)
  COPILOT_TIER_NANO_PROVIDER            provider slug: "openai" | "deepseek"

  COPILOT_TIER_MINI_MODEL_NAME         (same pattern for MINI tier)
  COPILOT_TIER_MINI_PRICE_INPUT_PER_1M
  COPILOT_TIER_MINI_PRICE_OUTPUT_PER_1M
  COPILOT_TIER_MINI_CONTEXT_WINDOW_TOKENS
  COPILOT_TIER_MINI_PROVIDER

  DEEPSEEK_API_KEY                     required if any COPILOT_TIER_*_PROVIDER=deepseek

Caching: computed overrides are cached in a module-level dict (lazy, idempotent).
Rollback: unset env vars → reverts to static TIER_METADATA defaults instantly.
"""

from __future__ import annotations

import os

import structlog

from src.modules.copilot.domain.model_tier import TIER_METADATA, ModelTier, TierMetadata

logger = structlog.get_logger()

# Module-level cache: populated lazily on first call per tier.
_OVERRIDE_CACHE: dict[ModelTier, TierMetadata] = {}

# Env var prefix format: COPILOT_TIER_{TIER}_{FIELD}
_ENV_PREFIX = "COPILOT_TIER"


def _tier_key(tier: ModelTier) -> str:
    """Return the uppercase tier name for env var construction."""
    return tier.value.upper()


def _env(tier: ModelTier, field: str) -> str | None:
    """Read a tier-specific env var (returns None if unset or empty)."""
    key = f"{_ENV_PREFIX}_{_tier_key(tier)}_{field}"
    val = os.environ.get(key, "").strip()
    return val or None


def _build_override(tier: ModelTier) -> TierMetadata:
    """Build a TierMetadata for ``tier`` blending env overrides with static fallback."""
    static = TIER_METADATA[tier]

    model_name = _env(tier, "MODEL_NAME") or static.model_name
    price_input = static.price_input_per_1m
    price_output = static.price_output_per_1m
    context_window = static.context_window_tokens

    raw_input = _env(tier, "PRICE_INPUT_PER_1M")
    if raw_input is not None:
        try:
            price_input = float(raw_input)
        except ValueError:
            logger.warning(
                "copilot_model_config_bad_price",
                tier=tier.value,
                field="PRICE_INPUT_PER_1M",
                value=raw_input,
            )

    raw_output = _env(tier, "PRICE_OUTPUT_PER_1M")
    if raw_output is not None:
        try:
            price_output = float(raw_output)
        except ValueError:
            logger.warning(
                "copilot_model_config_bad_price",
                tier=tier.value,
                field="PRICE_OUTPUT_PER_1M",
                value=raw_output,
            )

    raw_ctx = _env(tier, "CONTEXT_WINDOW_TOKENS")
    if raw_ctx is not None:
        try:
            context_window = int(raw_ctx)
        except ValueError:
            logger.warning(
                "copilot_model_config_bad_context",
                tier=tier.value,
                field="CONTEXT_WINDOW_TOKENS",
                value=raw_ctx,
            )

    return TierMetadata(
        tier=tier,
        model_name=model_name,
        price_input_per_1m=price_input,
        price_output_per_1m=price_output,
        price_cached_input_per_1m=static.price_cached_input_per_1m,
        context_window_tokens=context_window,
        supports_caching=static.supports_caching,
        is_reasoning=static.is_reasoning,
    )


def get_tier_metadata(tier: ModelTier) -> TierMetadata:
    """Return TierMetadata for ``tier``, blending env overrides with static fallback.

    Results are cached per-tier at module level (lazy init, idempotent).
    Env-var changes after first call require ``invalidate_tier_cache()`` to take
    effect — intended usage: set vars at process start, change only in tests.
    """
    if tier not in _OVERRIDE_CACHE:
        _OVERRIDE_CACHE[tier] = _build_override(tier)
    return _OVERRIDE_CACHE[tier]


def get_provider_for_tier(tier: ModelTier) -> str:
    """Return the provider slug for ``tier`` from env or default ``"openai"``."""
    override = _env(tier, "PROVIDER")
    if override:
        return override.lower()
    return "openai"


def invalidate_tier_cache() -> None:
    """Clear the module-level cache (used in tests to reload env changes)."""
    _OVERRIDE_CACHE.clear()


def validate_deepseek_api_key() -> str:
    """Return the DEEPSEEK_API_KEY or raise ``ValueError`` if missing.

    Called by the provider factory when ``COPILOT_TIER_*_PROVIDER=deepseek``
    is configured. Raises early so the error surfaces at request time, not
    boot — missing key for an unused tier is not an error.
    """
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        msg = (
            "DEEPSEEK_API_KEY is required when COPILOT_TIER_*_PROVIDER=deepseek "
            "but is missing or empty. Set the env var or unset COPILOT_TIER_*_PROVIDER."
        )
        raise ValueError(msg)
    return key
