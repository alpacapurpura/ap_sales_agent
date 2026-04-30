"""Unit tests for MultiRoleLLMRouter toggle-based LiteLLM dispatch.

TDD RED-first — tests written before implementation per tdd-mandatory.md.

Contract: §16 of S3 PR-2 CONTRACT.md (3 tests).
"""

from __future__ import annotations

import pytest

from src.core.enums import ModelRole


def test_router_resolve_returns_litellm_when_toggle_on(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """LITELLM_PROXY_ENABLED=True → _resolve(role) returns LiteLLMService."""
    monkeypatch.setattr("src.core.config.settings.LITELLM_PROXY_ENABLED", True)
    monkeypatch.setattr("src.core.config.settings.LITELLM_MASTER_KEY", "sk-test")
    monkeypatch.setattr("src.core.config.settings.LITELLM_BASE_URL", "http://litellm:4000/v1")

    from src.shared.infrastructure.llm.providers.litellm import LiteLLMService
    from src.shared.infrastructure.llm.router import MultiRoleLLMRouter

    router = MultiRoleLLMRouter()
    svc = router._resolve(ModelRole.NANO)
    assert isinstance(svc, LiteLLMService)


def test_router_resolve_returns_legacy_when_toggle_off(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """LITELLM_PROXY_ENABLED=False → _resolve(role) returns per-provider legacy service."""
    from src.core.enums import AIProvider

    monkeypatch.setattr("src.core.config.settings.LITELLM_PROXY_ENABLED", False)
    monkeypatch.setattr("src.core.config.settings.AI_PROVIDER", AIProvider.OPENAI)
    monkeypatch.setattr("src.core.config.settings.AI_PROVIDER_NANO", None)
    monkeypatch.setattr("src.core.config.settings.OPENAI_API_KEY", "sk-test-openai")

    from src.shared.infrastructure.llm.providers.litellm import LiteLLMService
    from src.shared.infrastructure.llm.router import MultiRoleLLMRouter

    router = MultiRoleLLMRouter()
    svc = router._resolve(ModelRole.NANO)
    # Must NOT be LiteLLMService — must be a legacy provider
    assert not isinstance(svc, LiteLLMService)


def test_router_litellm_singleton_across_roles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Same LiteLLMService instance returned for NANO + REASONING + AGENT."""
    monkeypatch.setattr("src.core.config.settings.LITELLM_PROXY_ENABLED", True)
    monkeypatch.setattr("src.core.config.settings.LITELLM_MASTER_KEY", "sk-test")
    monkeypatch.setattr("src.core.config.settings.LITELLM_BASE_URL", "http://litellm:4000/v1")

    from src.shared.infrastructure.llm.router import MultiRoleLLMRouter

    router = MultiRoleLLMRouter()
    svc_nano = router._resolve(ModelRole.NANO)
    svc_reasoning = router._resolve(ModelRole.REASONING)
    svc_agent = router._resolve(ModelRole.AGENT)

    # All roles share a single LiteLLMService instance (singleton)
    assert svc_nano is svc_reasoning
    assert svc_nano is svc_agent
