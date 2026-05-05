"""Per-role LLM router.

Façade that implements ``BaseLLMService`` but dispatches each call to the
provider configured for that role.

Post PI-12 S1 sales-agent-litellm-canonicalization (T-4 + T-5): dispatch is
unified via the LiteLLM Proxy (single ``LiteLLMService`` instance). Legacy
per-provider adapters (openai.py, deepseek.py, kimi.py, qwen.py, gemini.py,
_openai_compat.py) were deleted in T-4. The ``LITELLM_PROXY_ENABLED``
emergency-rollback toggle was deleted in T-5 — the LiteLLM Proxy is the
only runtime dispatch path.

Backward compatibility: callers keep using
``LLMFactory.get_service().get_client(role)`` — the factory returns this
router, so existing callsites get per-role routing transparently.
"""

from typing import Any

from src.core.enums import AIProvider, ModelRole
from src.shared.infrastructure.llm.base import BaseLLMService

_LEGACY_MODEL_TYPE_MAP: dict[str, ModelRole] = {
    "smart": ModelRole.REASONING,
    "fast": ModelRole.FAST,
    "nano": ModelRole.NANO,
    "vision": ModelRole.VISION,
    "agent": ModelRole.AGENT,
}


class MultiRoleLLMRouter(BaseLLMService):
    """Routes ``BaseLLMService`` calls to the LiteLLM Proxy (single adapter).

    All roles dispatch via a single ``LiteLLMService`` instance — the proxy
    resolves per-provider routing, fallback chains, and retry semantics
    internally via ``litellm_config.yaml``.
    """

    def __init__(self) -> None:
        """Lazily initialise the LiteLLMService singleton on first use."""
        self._litellm: BaseLLMService | None = None

    def _resolve(self, role: ModelRole) -> BaseLLMService:
        """Return the LiteLLMService singleton (proxy resolves provider per call).

        ``role`` is part of the contract (callers pass it for telemetry and
        future per-role overrides) but the LiteLLMService singleton resolves
        the actual model from ``settings.get_model(role)`` at call time.
        """
        del role  # consumed by LiteLLMService internals via settings lookup
        if self._litellm is None:
            from src.shared.infrastructure.llm.providers.litellm import LiteLLMService

            self._litellm = LiteLLMService()
        return self._litellm

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

    # Test/debug helper — surfaces the configured provider for ratchet tests
    # and ops dashboards. The proxy still does the real routing at call time.
    def get_provider_for_role(self, role: ModelRole) -> AIProvider:
        """Return which provider this router will dispatch ``role`` to."""
        from src.core.config import settings

        return settings.get_provider_for_role(role)
