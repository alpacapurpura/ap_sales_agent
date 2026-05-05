"""LLM service factory — per-role multi-provider routing.

The factory exposes a single ``get_service()`` entry point that returns a
:class:`MultiRoleLLMRouter` dispatching each ``get_client(role)`` call to
the provider configured for that role via ``AI_PROVIDER_<ROLE>`` env vars
(with ``AI_PROVIDER`` as the global fallback). Existing callsites do not
change.

T-5 (PI-12 S1) deleted the ``LITELLM_PROXY_ENABLED`` flag — all dispatch
flows through the LiteLLM Proxy unconditionally (master key resolved via
``litellm_config.yaml``).

T-6a (PI-12 S1, Phase 1 expand-contract):
    - The orphaned ``_extract_tenant_key`` helper has been DELETED. It
      had zero callers in ``src/`` or ``tests/`` post-T-5 (no path-toggle
      meant no consumer ever read the per-tenant key columns again).
    - The DB columns (``openai_api_key``, ``deepseek_api_key``,
      ``kimi_api_key``, ``dashscope_api_key``) have been NULLed in the
      same PR by ``alembic/versions/123_deprecate_tenant_provider_api_keys.py``.
    - The Pydantic ``Tenant``/``AISettings``/``TenantSettingsUpdate``
      domain models mark those 4 fields ``deprecated=True, exclude=True``
      so they no longer leak through API responses.

T-6b (operational gate, no code) verifies zero reads of the deprecated
columns in prod; T-6c will physically ``DROP COLUMN`` and remove the
SQLAlchemy mappings.

``gemini_api_key`` is **out of scope** per architect §2.4 (Q4
ratification): it remains active because landing extractors still call
Gemini directly outside the LiteLLM Proxy.
"""

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
        dispatch flows through the LiteLLM Proxy regardless of whether
        the tenant historically supplied a key — credential resolution
        is the proxy's responsibility (``litellm_config.yaml``). Tenants
        without permission to use platform keys still error out so the
        access control invariant is preserved.
        """
        if getattr(tenant, "can_use_platform_keys", False):
            return cls.get_service()

        msg = "AI Configuration Error: No API Key provided and platform keys are disabled for this tenant."
        raise ValueError(msg)

    # Deprecated: kept for internal compatibility.
    @classmethod
    def _create_service(cls) -> BaseLLMService:
        return cls.get_service()


# Global accessor — backwards compat.
llm_service = LLMFactory.get_service()
