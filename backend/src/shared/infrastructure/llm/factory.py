"""LLM service factory — per-role multi-provider routing.

The factory still exposes a single ``get_service()`` entry point, but the
returned object is now a :class:`MultiRoleLLMRouter` that dispatches each
``get_client(role)`` call to the provider configured for that specific role
via ``AI_PROVIDER_<ROLE>`` env vars (with ``AI_PROVIDER`` as the global
fallback). Existing callsites do not change.

Tenant-scoped behaviour (``get_service_for_tenant``) preserves the legacy
single-provider semantics — the tenant supplies a key for the *global*
``AI_PROVIDER``. Per-role tenant overrides are deferred to a follow-up.
"""

from src.core.config import settings
from src.core.enums import AIProvider
from src.shared.infrastructure.llm.base import BaseLLMService
from src.shared.infrastructure.llm.router import (
    MultiRoleLLMRouter,
    build_provider_service,
)


class LLMFactory:
    """Factory class to instantiate the correct LLM service."""

    _instance: BaseLLMService | None = None

    @classmethod
    def get_service(cls) -> BaseLLMService:
        """Return the singleton router (per-role dispatch under the hood)."""
        if cls._instance is None:
            cls._instance = MultiRoleLLMRouter()
        return cls._instance

    @classmethod
    def get_service_for_tenant(cls, tenant: object) -> BaseLLMService:
        """Build a tenant-scoped service when the tenant supplies its own key.

        Falls back to the platform router when the tenant has no key but is
        allowed to use platform credentials. Per-role tenant overrides are
        not supported yet — the tenant key is bound to the *global*
        ``AI_PROVIDER``; if a role routes to a different provider via
        ``AI_PROVIDER_<ROLE>``, that role still uses the platform key.
        """
        provider = settings.AI_PROVIDER
        api_key = cls._extract_tenant_key(tenant, provider)

        # 1. User provided key → tenant-scoped instance for the global provider.
        if api_key:
            return build_provider_service(provider, api_key=api_key)

        # 2. No user key but allowed to use platform → router singleton.
        if getattr(tenant, "can_use_platform_keys", False):
            return cls.get_service()

        # 3. No permission → error.
        msg = "AI Configuration Error: No API Key provided and platform keys are disabled for this tenant."
        raise ValueError(msg)

    @staticmethod
    def _extract_tenant_key(tenant: object, provider: AIProvider) -> str | None:
        """Pull the tenant-scoped key for a given provider, or ``None``."""
        # ``getattr`` with default keeps this robust if the Tenant model is
        # missing a column for a freshly-added provider (e.g. before the
        # migration runs in a given env).
        return {
            AIProvider.OPENAI: getattr(tenant, "openai_api_key", None),
            AIProvider.GEMINI: getattr(tenant, "gemini_api_key", None),
            AIProvider.DEEPSEEK: getattr(tenant, "deepseek_api_key", None),
            AIProvider.KIMI: getattr(tenant, "kimi_api_key", None),
            AIProvider.QWEN: getattr(tenant, "dashscope_api_key", None),
        }.get(provider)

    # Deprecated: kept for internal compatibility.
    @classmethod
    def _create_service(cls) -> BaseLLMService:
        return cls.get_service()


# Global accessor — backwards compat.
llm_service = LLMFactory.get_service()
