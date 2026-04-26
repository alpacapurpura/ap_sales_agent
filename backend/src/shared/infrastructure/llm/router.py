"""Per-role LLM router.

Façade that implements ``BaseLLMService`` but dispatches each call to the
provider configured for that role. Lets us run e.g. NANO/FAST on OpenAI
(low TTFB) while routing REASONING to DeepSeek and AGENT to Kimi for cost.

Backward compatibility: callers keep using
``LLMFactory.get_service().get_client(role)`` — the factory now returns this
router instead of a single concrete provider, so existing callsites get
per-role routing transparently.

Concrete providers are built lazily — the router only instantiates a
provider service the first time a role mapped to that provider is
requested. That means missing API keys for unused providers do not break
boot; they only raise when the role that needs them is invoked.
"""

from typing import Any

from src.core.config import settings
from src.core.enums import AIProvider, ModelRole
from src.shared.infrastructure.llm.base import BaseLLMService
from src.shared.infrastructure.llm.providers.openai import OpenAIService

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

    Used by both the router (for global per-role dispatch) and the factory
    (for tenant-scoped overrides where the tenant supplies its own key).
    """
    if provider == AIProvider.OPENAI:
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
    """Routes ``BaseLLMService`` calls to the provider configured per-role."""

    def __init__(self) -> None:
        """Lazily build per-provider services on first use."""
        self._providers: dict[AIProvider, BaseLLMService] = {}

    def _resolve(self, role: ModelRole) -> BaseLLMService:
        provider = settings.get_provider_for_role(role)
        if provider not in self._providers:
            self._providers[provider] = build_provider_service(provider)
        return self._providers[provider]

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
