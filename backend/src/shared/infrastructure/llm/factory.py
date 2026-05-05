"""LLM service factory — per-role multi-provider routing.

The factory exposes a single ``get_service()`` entry point that returns a
:class:`MultiRoleLLMRouter` dispatching each ``get_client(role)`` call to
the provider configured for that role via ``AI_PROVIDER_<ROLE>`` env vars
(with ``AI_PROVIDER`` as the global fallback). Existing callsites do not
change.

Tenant-scoped behaviour (``get_service_for_tenant``): post PI-12 S1 T-5,
all routing flows through the LiteLLM Proxy (master key only). Tenant
``*_api_key`` columns are deprecated (T-6a stubs ``_extract_tenant_key``,
T-6c drops the columns + helper). Until then the helper still exists but
the user-key branch is gone — tenants with their own key are treated the
same as platform-key tenants (LiteLLM Proxy resolves credentials from
``litellm_config.yaml``).
"""

from src.core.enums import AIProvider
from src.shared.infrastructure.llm.base import BaseLLMService
from src.shared.infrastructure.llm.router import MultiRoleLLMRouter


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
        """Return the platform router for any tenant allowed to use it.

        Post T-4 + T-5, per-provider adapters and the
        ``LITELLM_PROXY_ENABLED=False`` rollback path are gone. All
        dispatch flows through the LiteLLM Proxy regardless of whether the
        tenant supplies a key — credential resolution is the proxy's
        responsibility (``litellm_config.yaml``). Tenants without
        permission to use platform keys still error out so the access
        control invariant is preserved.
        """
        if getattr(tenant, "can_use_platform_keys", False):
            return cls.get_service()

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
