"""Tests for ModelTier domain enum and metadata table."""

from __future__ import annotations

import pytest

from src.modules.copilot.domain.model_tier import (
    TIER_METADATA,
    ModelTier,
    TierMetadata,
)


class TestModelTierEnum:
    """ModelTier is a StrEnum with four values."""

    def test_four_tiers_defined(self) -> None:
        """ModelTier has exactly NANO, MINI, REASONING, HEAVY."""
        assert set(ModelTier) == {
            ModelTier.NANO,
            ModelTier.MINI,
            ModelTier.REASONING,
            ModelTier.HEAVY,
        }

    def test_tier_values_are_lowercase_strings(self) -> None:
        """Tier values are lowercase strings used as DB/log identifiers."""
        assert ModelTier.NANO == "nano"
        assert ModelTier.MINI == "mini"
        assert ModelTier.REASONING == "reasoning"
        assert ModelTier.HEAVY == "heavy"

    def test_tier_is_str_subclass(self) -> None:
        """ModelTier is a StrEnum — behaves like a string."""
        assert isinstance(ModelTier.NANO, str)


class TestTierMetadata:
    """TIER_METADATA covers every tier and has sensible values."""

    def test_all_tiers_in_metadata(self) -> None:
        """Every ModelTier has a metadata entry."""
        for tier in ModelTier:
            assert tier in TIER_METADATA, f"Missing metadata for {tier}"

    def test_metadata_tier_field_matches_key(self) -> None:
        """TierMetadata.tier must match its dict key."""
        for key, meta in TIER_METADATA.items():
            assert meta.tier == key, f"Mismatch: key={key} meta.tier={meta.tier}"

    def test_nano_pricing(self) -> None:
        """NANO input price is 0.20 USD/1M tokens per CONTRACT §2.1."""
        meta = TIER_METADATA[ModelTier.NANO]
        assert meta.price_input_per_1m == pytest.approx(0.20)
        assert meta.price_output_per_1m == pytest.approx(1.25)

    def test_mini_pricing(self) -> None:
        """MINI input price is 0.75 USD/1M tokens per CONTRACT §2.1."""
        meta = TIER_METADATA[ModelTier.MINI]
        assert meta.price_input_per_1m == pytest.approx(0.75)
        assert meta.price_output_per_1m == pytest.approx(4.50)

    def test_reasoning_and_heavy_no_cache(self) -> None:
        """REASONING and HEAVY have no cache tier (price_cached_input_per_1m is None)."""
        assert TIER_METADATA[ModelTier.REASONING].price_cached_input_per_1m is None
        assert TIER_METADATA[ModelTier.HEAVY].price_cached_input_per_1m is None

    def test_nano_mini_support_caching(self) -> None:
        """NANO and MINI support caching."""
        assert TIER_METADATA[ModelTier.NANO].supports_caching is True
        assert TIER_METADATA[ModelTier.MINI].supports_caching is True

    def test_reasoning_heavy_are_reasoning_models(self) -> None:
        """REASONING and HEAVY are reasoning models."""
        assert TIER_METADATA[ModelTier.REASONING].is_reasoning is True
        assert TIER_METADATA[ModelTier.HEAVY].is_reasoning is True

    def test_nano_mini_are_not_reasoning(self) -> None:
        """NANO and MINI are not reasoning models."""
        assert TIER_METADATA[ModelTier.NANO].is_reasoning is False
        assert TIER_METADATA[ModelTier.MINI].is_reasoning is False

    def test_metadata_is_frozen(self) -> None:
        """TierMetadata is a frozen dataclass — no mutation allowed."""
        meta = TIER_METADATA[ModelTier.NANO]
        with pytest.raises((AttributeError, TypeError)):
            meta.model_name = "hacked"  # type: ignore[misc]

    def test_model_names_are_strings(self) -> None:
        """All model_name fields are non-empty strings."""
        for meta in TIER_METADATA.values():
            assert isinstance(meta.model_name, str)
            assert len(meta.model_name) > 0

    def test_context_window_positive(self) -> None:
        """All tiers have a positive context_window_tokens."""
        for meta in TIER_METADATA.values():
            assert meta.context_window_tokens > 0
