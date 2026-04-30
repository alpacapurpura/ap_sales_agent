"""Per-role LLM router.

Façade that implements ``BaseLLMService`` but dispatches each call to the
provider configured for that role.

S3 PR-2 (PI-2): dispatch is now unified via LiteLLM Proxy (single
``LiteLLMService`` instance) when ``LITELLM_PROXY_ENABLED=True`` (default).
Legacy per-provider dispatch is retained behind ``LITELLM_PROXY_ENABLED=False``
for emergency rollback only — deprecated in S3, removed in S4 PR-1.

Backward compatibility: callers keep using
``LLMFactory.get_service().get_client(role)`` — the factory returns this
router, so existing callsites get per-role routing transparently.

D-6: legacy adapters kept deprecated for emergency rollback toggle the
first sprint post-merge. Allowlist arch test extended accordingly;
shrinks to 0 in S4 PR-1 after 1-sprint prod verification.
"""

from typing import Any

from src.core.config import settings
from src.core.enums import AIProvider, ModelRole
from src.shared.infrastructure.llm.base import BaseLLMService

_LEGACY_MODEL_TYPE_MAP: dict[str, ModelRole] = {
    "smart": ModelRole.REASONING,
    "fast": ModelRole.FAST,
    "nano": ModelRole.NANO,
    "vision": ModelRole.VISION,
    "agent": ModelRole.AGENT,
}


def build_provider_service(
    provider: AIProvider,
    api_key: str | None = None,
) -> BaseLLMService:
    """Construct a concrete ``BaseLLMService`` for a single provider.

    Used by both the router (emergency rollback legacy path) and the factory
    (for tenant-scoped overrides where the tenant supplies its own key).

    Note: openai/deepseek/kimi/qwen adapters are DEPRECATED in S3 (D-6).
    They remain importable for ``LITELLM_PROXY_ENABLED=False`` rollback.
    Physical removal in S4 PR-1 post-verification.
    """
    if provider == AIProvider.OPENAI:
        from src.shared.infrastructure.llm.providers.openai import OpenAIService

        return OpenAIService(api_key=api_key)
    if provider == AIProvider.GEMINI:
        from src.shared.infrastructure.llm.providers.gemini import GeminiService

        return GeminiService(api_key=api_key)
    if provider == AIProvider.DEEPSEEK:
        from src.shared.infrastructure.llm.providers.deepseek import DeepSeekService

        return DeepSeekService(api_key=api_key)
    if provider == AIProvider.KIMI:
        from src.shared.infrastructure.llm.providers.kimi import KimiService

        return KimiService(api_key=api_key)
    if provider == AIProvider.QWEN:
        from src.shared.infrastructure.llm.providers.qwen import QwenService

        return QwenService(api_key=api_key)
    msg = f"Unsupported AI Provider: {provider}"
    raise ValueError(msg)


class MultiRoleLLMRouter(BaseLLMService):
    """Routes ``BaseLLMService`` calls to LiteLLM Proxy (single adapter post-S3).

    S3 PR-2: when ``LITELLM_PROXY_ENABLED=True`` (default), ALL roles
    dispatch via a single ``LiteLLMService`` instance — the proxy resolves
    per-provider routing, fallback chains, and retry semantics internally.

    Emergency rollback: set ``LITELLM_PROXY_ENABLED=False`` to fall back to
    per-provider legacy services without recompile or restart.
    """

    def __init__(self) -> None:
        """Lazily initialise service(s) on first use."""
        # S3 PR-2 singleton (toggle ON path)
        self._litellm: BaseLLMService | None = None
        # Emergency rollback path (toggle OFF) — same dispatch as pre-S3.
        self._legacy_providers: dict[AIProvider, BaseLLMService] = {}

    def _resolve(self, role: ModelRole) -> BaseLLMService:
        """Return the service that will handle ``role``.

        When ``LITELLM_PROXY_ENABLED=True`` (default): returns the singleton
        ``LiteLLMService`` — proxy picks provider from the model alias.
        When ``LITELLM_PROXY_ENABLED=False`` (rollback): returns the
        per-provider legacy service matching the role's configured provider.
        """
        if settings.LITELLM_PROXY_ENABLED:
            if self._litellm is None:
                from src.shared.infrastructure.llm.providers.litellm import LiteLLMService

                self._litellm = LiteLLMService()
            return self._litellm
        # Emergency rollback path — same dispatch as pre-S3.
        provider = settings.get_provider_for_role(role)
        if provider not in self._legacy_providers:
            self._legacy_providers[provider] = build_provider_service(provider)
        return self._legacy_providers[provider]

    @staticmethod
    def _resolve_role_compat(model_type: str | ModelRole) -> ModelRole:
        if isinstance(model_type, ModelRole):
            return model_type
        return _LEGACY_MODEL_TYPE_MAP.get(model_type, ModelRole.REASONING)

    def get_client(
        self,
        role: ModelRole = ModelRole.REASONING,
        *,
        temperature: float | None = None,
    ) -> Any:  # noqa: ANN401 — abstract LLM interface
        """Return the chat client of the provider configured for ``role``."""
        return self._resolve(role).get_client(role, temperature=temperature)

    def get_embedding_model(self) -> Any:  # noqa: ANN401 — abstract LLM interface
        """Return the embedding client of the provider configured for EMBEDDING."""
        return self._resolve(ModelRole.EMBEDDING).get_embedding_model()

    def generate_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        model_type: str | ModelRole = "smart",
        **kwargs: Any,  # noqa: ANN401 — abstract LLM interface
    ) -> str:
        """Dispatch to the provider that serves the resolved role."""
        role = self._resolve_role_compat(model_type)
        return self._resolve(role).generate_response(
            messages,
            system_prompt=system_prompt,
            model_type=model_type,
            **kwargs,
        )

    # Test/debug helpers — not part of the abstract interface but useful
    # for ratchet tests and ops dashboards.
    def get_provider_for_role(self, role: ModelRole) -> AIProvider:
        """Return which provider this router will dispatch ``role`` to."""
        return settings.get_provider_for_role(role)

    def reset_cache(self) -> None:
        """Clear the cached provider services (used in tests)."""
        self._providers.clear()
