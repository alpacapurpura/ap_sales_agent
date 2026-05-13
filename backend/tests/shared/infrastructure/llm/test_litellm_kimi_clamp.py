"""Regression tests — LiteLLMService kimi K2.6 temperature clamp.

PI-11 PR-1 § 7 D7 (2026-05-04): Production bug fix.
Kimi K2.6 via LiteLLM proxy only accepts temperature=0.6 (thinking disabled).
Without clamp the upstream returns HTTP 400 ``only 0.6 is allowed for this model``.

Contract: CONTRACT.md PR-1 § 7 — mirror of kimi.py:79-92 dead-code clamp.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from luana_core_platform.core.enums import ModelRole


@pytest.fixture()
def _settings_kimi_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch settings so AGENT role maps to kimi provider + kimi-k2.6 model."""
    from luana_core_platform.core.enums import AIProvider

    monkeypatch.setattr("luana_core_platform.core.config.settings.LITELLM_BASE_URL", "http://litellm:4000/v1")
    monkeypatch.setattr("luana_core_platform.core.config.settings.LITELLM_MASTER_KEY", "sk-test-master")
    monkeypatch.setattr("luana_core_platform.core.config.settings.AI_MODEL_AGENT", "kimi-k2.6")
    monkeypatch.setattr("luana_core_platform.core.config.settings.AI_PROVIDER_AGENT", AIProvider.KIMI)


@pytest.fixture()
def _settings_non_kimi(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch settings so NANO role maps to openai provider + gpt-4o-mini (non-kimi)."""
    from luana_core_platform.core.enums import AIProvider

    monkeypatch.setattr("luana_core_platform.core.config.settings.LITELLM_BASE_URL", "http://litellm:4000/v1")
    monkeypatch.setattr("luana_core_platform.core.config.settings.LITELLM_MASTER_KEY", "sk-test-master")
    monkeypatch.setattr("luana_core_platform.core.config.settings.AI_MODEL_NANO", "gpt-4o-mini")
    monkeypatch.setattr("luana_core_platform.core.config.settings.AI_PROVIDER_NANO", AIProvider.OPENAI)


def test_kimi_k2_temp_explicit_clamped_to_0_6(_settings_kimi_agent: None) -> None:
    """When AGENT role resolves to kimi/kimi-k2.6 + explicit temp=1.0 → clamped to 0.6.

    Kimi K2.6 server-enforced constraint: thinking disabled requires temperature=0.6 exactly.
    PR-1 PI-11 regression: litellm.py dispatch was passing caller temperature unclamped
    → HTTP 400 ``only 0.6 is allowed for this model`` (production silent fail).
    """
    from luana_core_llm.providers.litellm import (
        LiteLLMService,
        _K2_REQUIRED_TEMPERATURE,
    )

    svc = LiteLLMService()

    with patch("luana_core_llm.providers.litellm._build_chat_from_spec") as mock_build:
        mock_build.return_value = MagicMock()
        svc._get_chat_model(ModelRole.AGENT, temperature=1.0)
        ctx_arg = mock_build.call_args[0][1]  # ChatBuildContext
        assert ctx_arg.temperature == _K2_REQUIRED_TEMPERATURE, (
            f"Expected temperature clamped to {_K2_REQUIRED_TEMPERATURE}, got {ctx_arg.temperature}"
        )


def test_kimi_k2_temp_already_0_6_no_clamp_log(_settings_kimi_agent: None) -> None:
    """When temp=0.6 (already correct) → no warning logged, passthrough unchanged."""
    from luana_core_llm.providers.litellm import (
        LiteLLMService,
        _K2_REQUIRED_TEMPERATURE,
    )

    svc = LiteLLMService()

    with (
        patch("luana_core_llm.providers.litellm._build_chat_from_spec") as mock_build,
        patch("luana_core_llm.providers.litellm.logger") as mock_logger,
    ):
        mock_build.return_value = MagicMock()
        svc._get_chat_model(ModelRole.AGENT, temperature=_K2_REQUIRED_TEMPERATURE)
        # Warning should NOT have been emitted (already correct temp)
        mock_logger.warning.assert_not_called()
        ctx_arg = mock_build.call_args[0][1]
        assert ctx_arg.temperature == _K2_REQUIRED_TEMPERATURE


def test_non_kimi_model_temp_passthrough(_settings_non_kimi: None) -> None:
    """Non-kimi model (NANO/openai/gpt-4o-mini) with temp=1.0 → passthrough unchanged.

    Clamp ONLY applies when model alias contains 'kimi/kimi-k2'.
    """
    from luana_core_llm.providers.litellm import LiteLLMService

    svc = LiteLLMService()

    with patch("luana_core_llm.providers.litellm._build_chat_from_spec") as mock_build:
        mock_build.return_value = MagicMock()
        svc._get_chat_model(ModelRole.NANO, temperature=1.0)
        ctx_arg = mock_build.call_args[0][1]
        assert ctx_arg.temperature == 1.0, (
            f"Non-kimi model temperature should not be clamped, got {ctx_arg.temperature}"
        )


def test_kimi_k2_temp_none_uses_default_no_clamp(_settings_kimi_agent: None) -> None:
    """When temperature=None → uses _DEFAULT_TEMPERATURE (0.7).

    Clamp guard: None case → effective_temp = DEFAULT (0.7) != 0.6 → would clamp.
    But clamp only triggers when temperature is NOT None AND != _K2_REQUIRED_TEMPERATURE.
    Verify: None case results in _DEFAULT_TEMPERATURE being clamped to 0.6 (correct behavior
    since 0.7 != 0.6 for kimi/kimi-k2.6).
    """
    from luana_core_llm.providers.litellm import (
        LiteLLMService,
        _K2_REQUIRED_TEMPERATURE,
    )

    svc = LiteLLMService()

    with patch("luana_core_llm.providers.litellm._build_chat_from_spec") as mock_build:
        mock_build.return_value = MagicMock()
        svc._get_chat_model(ModelRole.AGENT, temperature=None)
        ctx_arg = mock_build.call_args[0][1]
        # Default is 0.7, kimi clamp fires since 0.7 != 0.6 for kimi/kimi-k2.6
        assert ctx_arg.temperature == _K2_REQUIRED_TEMPERATURE, (
            f"Kimi K2.6 with default temp=0.7 should be clamped to {_K2_REQUIRED_TEMPERATURE}, "
            f"got {ctx_arg.temperature}"
        )
