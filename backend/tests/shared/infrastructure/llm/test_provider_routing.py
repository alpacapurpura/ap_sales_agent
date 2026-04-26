"""Sprint 0 — multi-role provider routing through the factory.

Per-role override (``AI_PROVIDER_<ROLE>``) wins; falls back to global
``AI_PROVIDER``. Tests use ``monkeypatch`` to flip settings without
touching ``.env``, then assert the router resolves each role to the
correct concrete service class.
"""

from __future__ import annotations

import pytest

from src.core.enums import AIProvider, ModelRole
from src.shared.infrastructure.llm.factory import LLMFactory
from src.shared.infrastructure.llm.providers.deepseek import DeepSeekService
from src.shared.infrastructure.llm.providers.kimi import KimiService
from src.shared.infrastructure.llm.providers.openai import OpenAIService
from src.shared.infrastructure.llm.providers.qwen import QwenService
from src.shared.infrastructure.llm.router import (
    MultiRoleLLMRouter,
    build_provider_service,
)


@pytest.fixture(autouse=True)
def _stub_provider_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    """Provide dummy API keys so concrete providers instantiate without env."""
    from src.core.config import settings

    monkeypatch.setattr(settings, "DEEPSEEK_API_KEY", "sk-test-deepseek")
    monkeypatch.setattr(settings, "KIMI_API_KEY", "sk-test-kimi")
    monkeypatch.setattr(settings, "DASHSCOPE_API_KEY", "sk-test-dashscope")


@pytest.fixture
def fresh_router() -> MultiRoleLLMRouter:
    """Brand-new router each test — avoids leaking the singleton cache."""
    return MultiRoleLLMRouter()


class TestBuildProviderService:
    @pytest.mark.parametrize(
        ("provider", "expected_cls"),
        [
            (AIProvider.OPENAI, OpenAIService),
            (AIProvider.DEEPSEEK, DeepSeekService),
            (AIProvider.KIMI, KimiService),
            (AIProvider.QWEN, QwenService),
        ],
    )
    def test_builds_concrete_service(
        self,
        provider: AIProvider,
        expected_cls: type,
    ) -> None:
        svc = build_provider_service(provider)
        assert isinstance(svc, expected_cls)

    def test_rejects_unknown_provider(self) -> None:
        with pytest.raises(ValueError, match="Unsupported AI Provider"):
            build_provider_service("bogus")  # type: ignore[arg-type]


class TestRouterPerRoleDispatch:
    def test_global_provider_used_when_no_override(
        self,
        fresh_router: MultiRoleLLMRouter,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from src.core.config import settings

        monkeypatch.setattr(settings, "AI_PROVIDER", AIProvider.OPENAI)
        for role in (
            "AI_PROVIDER_NANO",
            "AI_PROVIDER_REASONING",
            "AI_PROVIDER_FAST",
            "AI_PROVIDER_AGENT",
            "AI_PROVIDER_VISION",
            "AI_PROVIDER_EMBEDDING",
        ):
            monkeypatch.setattr(settings, role, None)

        svc = fresh_router._resolve(ModelRole.REASONING)
        assert isinstance(svc, OpenAIService)

    def test_per_role_override_wins(
        self,
        fresh_router: MultiRoleLLMRouter,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from src.core.config import settings

        monkeypatch.setattr(settings, "AI_PROVIDER", AIProvider.OPENAI)
        monkeypatch.setattr(settings, "AI_PROVIDER_REASONING", AIProvider.DEEPSEEK)
        monkeypatch.setattr(settings, "AI_PROVIDER_AGENT", AIProvider.KIMI)
        monkeypatch.setattr(settings, "AI_PROVIDER_NANO", None)

        assert isinstance(fresh_router._resolve(ModelRole.NANO), OpenAIService)
        assert isinstance(fresh_router._resolve(ModelRole.REASONING), DeepSeekService)
        assert isinstance(fresh_router._resolve(ModelRole.AGENT), KimiService)

    def test_provider_service_is_cached(
        self,
        fresh_router: MultiRoleLLMRouter,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from src.core.config import settings

        monkeypatch.setattr(settings, "AI_PROVIDER_REASONING", AIProvider.DEEPSEEK)
        a = fresh_router._resolve(ModelRole.REASONING)
        b = fresh_router._resolve(ModelRole.REASONING)
        assert a is b


class TestFactoryReturnsRouter:
    def test_get_service_returns_router(self) -> None:
        # Reset the singleton so the assertion is stable across the suite.
        LLMFactory._instance = None
        svc = LLMFactory.get_service()
        assert isinstance(svc, MultiRoleLLMRouter)

    def test_router_get_provider_for_role_helper(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from src.core.config import settings

        monkeypatch.setattr(settings, "AI_PROVIDER_AGENT", AIProvider.KIMI)
        router = MultiRoleLLMRouter()
        assert router.get_provider_for_role(ModelRole.AGENT) == AIProvider.KIMI


class TestTenantOverride:
    def test_tenant_key_extracts_per_provider(self) -> None:
        class _DummyTenant:
            openai_api_key = "sk-openai-tenant"
            gemini_api_key = None
            deepseek_api_key = "sk-deepseek-tenant"
            kimi_api_key = None
            dashscope_api_key = "sk-dashscope-tenant"
            can_use_platform_keys = False

        tenant = _DummyTenant()
        assert LLMFactory._extract_tenant_key(tenant, AIProvider.OPENAI) == "sk-openai-tenant"
        assert LLMFactory._extract_tenant_key(tenant, AIProvider.DEEPSEEK) == "sk-deepseek-tenant"
        assert LLMFactory._extract_tenant_key(tenant, AIProvider.QWEN) == "sk-dashscope-tenant"
        assert LLMFactory._extract_tenant_key(tenant, AIProvider.KIMI) is None

    def test_get_service_for_tenant_uses_tenant_key(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from src.core.config import settings

        monkeypatch.setattr(settings, "AI_PROVIDER", AIProvider.DEEPSEEK)

        class _DummyTenant:
            openai_api_key = None
            gemini_api_key = None
            deepseek_api_key = "sk-deepseek-tenant-direct"
            kimi_api_key = None
            dashscope_api_key = None
            can_use_platform_keys = False

        svc = LLMFactory.get_service_for_tenant(_DummyTenant())
        assert isinstance(svc, DeepSeekService)
        assert svc.api_key == "sk-deepseek-tenant-direct"

    def test_get_service_for_tenant_falls_back_to_platform(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from src.core.config import settings

        monkeypatch.setattr(settings, "AI_PROVIDER", AIProvider.DEEPSEEK)

        class _DummyTenant:
            openai_api_key = None
            gemini_api_key = None
            deepseek_api_key = None
            kimi_api_key = None
            dashscope_api_key = None
            can_use_platform_keys = True

        LLMFactory._instance = None
        svc = LLMFactory.get_service_for_tenant(_DummyTenant())
        assert isinstance(svc, MultiRoleLLMRouter)

    def test_get_service_for_tenant_no_perm_raises(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from src.core.config import settings

        monkeypatch.setattr(settings, "AI_PROVIDER", AIProvider.DEEPSEEK)

        class _DummyTenant:
            openai_api_key = None
            gemini_api_key = None
            deepseek_api_key = None
            kimi_api_key = None
            dashscope_api_key = None
            can_use_platform_keys = False

        with pytest.raises(ValueError, match="No API Key"):
            LLMFactory.get_service_for_tenant(_DummyTenant())
