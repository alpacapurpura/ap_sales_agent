"""Per-role LLM router.

Façade that implements ``BaseLLMService`` but dispatches each call to the
provider configured for that role.

S3 PR-2 (PI-2): dispatch is now unified via LiteLLM Proxy (single
``LiteLLMService`` instance) when ``LITELLM_PROXY_ENABLED=True`` (default).
Legacy per-provider adapters (openai.py, deepseek.py, kimi.py, qwen.py,
gemini.py, _openai_compat.py) were deleted in PI-12 S1 T-4.

``LITELLM_PROXY_ENABLED`` flag is removed in T-5. Until then, only
``LITELLM_PROXY_ENABLED=True`` (default) is functional — the legacy
rollback path (``build_provider_service``) raises ``NotImplementedError``
since the per-provider adapters no longer exist.

Backward compatibility: callers keep using
``LLMFactory.get_service().get_client(role)`` — the factory returns this
router, so existing callsites get per-role routing transparently.
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
    """Stub: per-provider adapters deleted in PI-12 S1 T-4.

    This function previously constructed per-provider ``BaseLLMService``
    instances (OpenAIService, DeepSeekService, etc.) for the emergency
    rollback path (``LITELLM_PROXY_ENABLED=False``). Those adapters were
    deleted in T-4 as dead code — all runtime traffic routes via
    ``LiteLLMService`` (``LITELLM_PROXY_ENABLED=True`` is the only live path).

    T-5 removes ``LITELLM_PROXY_ENABLED`` flag and this function entirely.
    Until T-5 merges, this stub raises to make any accidental rollback-path
    invocation fail loudly rather than silently importing a missing module.
    """
    msg = (
        f"build_provider_service({provider!r}) called but per-provider adapters were "
        "deleted in PI-12 S1 T-4. Set LITELLM_PROXY_ENABLED=True (default) to use "
        "LiteLLMService. Full flag removal in T-5."
    )
    raise NotImplementedError(msg)


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
