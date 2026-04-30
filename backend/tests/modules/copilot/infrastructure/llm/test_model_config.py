"""Smoke tests model_config — env override + fallback chain (D-1, D-6 CONTRACT PR-3)."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from src.modules.copilot.domain.model_tier import TIER_METADATA, ModelTier
from src.modules.copilot.infrastructure.llm.model_config import (
    get_provider_for_tier,
    get_tier_metadata,
    invalidate_tier_cache,
    validate_deepseek_api_key,
)


class TestModelConfig:
    """Smoke tests model_config env override layer."""

    def setup_method(self) -> None:
        """Clear cache between tests so env override changes take effect."""
        invalidate_tier_cache()

    def teardown_method(self) -> None:
        """Clear cache after tests so other modules see fresh defaults."""
        invalidate_tier_cache()

    def test_env_unset_returns_static_fallback(self) -> None:
        """Without env override → static TIER_METADATA fallback."""
        with patch.dict(os.environ, {}, clear=False):
            for key in (
                "COPILOT_TIER_NANO_MODEL_NAME",
                "COPILOT_TIER_NANO_PROVIDER",
                "COPILOT_TIER_NANO_PRICE_INPUT_PER_1M",
                "COPILOT_TIER_NANO_PRICE_OUTPUT_PER_1M",
            ):
                os.environ.pop(key, None)
            invalidate_tier_cache()
            metadata = get_tier_metadata(ModelTier.NANO)
            assert metadata.model_name == TIER_METADATA[ModelTier.NANO].model_name

    def test_env_override_returns_override(self) -> None:
        """COPILOT_TIER_NANO_MODEL_NAME set → override applied."""
        with patch.dict(
            os.environ,
            {
                "COPILOT_TIER_NANO_MODEL_NAME": "deepseek-v4-flash",
                "COPILOT_TIER_NANO_PRICE_INPUT_PER_1M": "0.14",
                "COPILOT_TIER_NANO_PRICE_OUTPUT_PER_1M": "0.28",
            },
        ):
            invalidate_tier_cache()
            metadata = get_tier_metadata(ModelTier.NANO)
            assert metadata.model_name == "deepseek-v4-flash"
            assert metadata.price_input_per_1m == 0.14
            assert metadata.price_output_per_1m == 0.28

    def test_get_provider_for_tier_default_openai(self) -> None:
        """COPILOT_TIER_NANO_PROVIDER unset → 'openai' default."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("COPILOT_TIER_NANO_PROVIDER", None)
            assert get_provider_for_tier(ModelTier.NANO) == "openai"

    def test_get_provider_for_tier_deepseek_override(self) -> None:
        """COPILOT_TIER_NANO_PROVIDER=deepseek → 'deepseek'."""
        with patch.dict(os.environ, {"COPILOT_TIER_NANO_PROVIDER": "deepseek"}):
            assert get_provider_for_tier(ModelTier.NANO) == "deepseek"

    def test_validate_deepseek_api_key_missing_raises(self) -> None:
        """validate_deepseek_api_key raises if any tier uses deepseek but no API key."""
        with patch.dict(
            os.environ,
            {"COPILOT_TIER_NANO_PROVIDER": "deepseek"},
            clear=False,
        ):
            os.environ.pop("DEEPSEEK_API_KEY", None)
            invalidate_tier_cache()
            with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
                validate_deepseek_api_key()
