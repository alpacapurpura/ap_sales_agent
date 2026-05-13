"""LiteLLM Proxy provider adapter.

Single adapter that talks to ALL providers via the LiteLLM Proxy
OpenAI-compatible endpoint. Replaces per-provider adapters that
each duplicated ChatOpenAI(base_url=...) plumbing.

Flow::

  consumer
    ↓ LLMFactory.get_service().get_client(role)
  MultiRoleLLMRouter._resolve(role) → LiteLLMService
    ↓ resolves model = settings.get_model(role)
    ↓ resolves provider = settings.get_provider_for_role(role)
    ↓ LiteLLM model_name = f"{provider}/{model}"
       (e.g. "deepseek/deepseek-v4-flash", "openai/gpt-4o-mini")
  ChatOpenAI(api_key=LITELLM_MASTER_KEY,
             base_url=LITELLM_BASE_URL,
             model=litellm_model_name)
    ↓ POST /v1/chat/completions
  LiteLLM Proxy (Docker svc visionarias_litellm:4000)
    ↓ routes to provider per litellm_config.yaml
  OpenAI / DeepSeek / Kimi / Qwen / Gemini / future Anthropic etc.

S3 PR-2 PI-2. Replaces: openai.py, _openai_compat.py, deepseek.py,
kimi.py, qwen.py, gemini.py (6 adapters → 1). Adapters deleted in
PI-12 S1 T-4; emergency rollback toggle ``LITELLM_PROXY_ENABLED``
removed in T-5 — the LiteLLM Proxy is the only runtime dispatch path.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import OpenAIEmbeddings

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

from luana_core_llm.base import BaseLLMService
from luana_core_llm.providers._chat_model_resolver import (
    DEFAULT_OPENAI_SPEC,
    ChatBuildContext,
    ChatModelSpec,
    _build_chat_from_spec,
)
from luana_core_llm.providers._response_validation import (
    detect_reasoning_budget_exhaustion,
)
from luana_core_platform.core.config import settings
from luana_core_platform.core.enums import ModelRole

logger = structlog.get_logger()

_LEGACY_MODEL_TYPE_MAP: dict[str, ModelRole] = {
    "smart": ModelRole.REASONING,
    "fast": ModelRole.FAST,
    "nano": ModelRole.NANO,
    "vision": ModelRole.VISION,
    "agent": ModelRole.AGENT,
}


_K2_REQUIRED_TEMPERATURE = 0.6
"""Kimi K2.6 (thinking disabled) only accepts temperature=0.6 server-side
(TP4-B4 + TP5-B8). Without coercion, the upstream returns HTTP 400
``only 0.6 is allowed for this model``. Mirror of the constant in the
deprecated legacy adapter ``providers/kimi.py``; both must agree."""


class LiteLLMService(BaseLLMService):
    """Single LangChain client targeting LiteLLM Proxy OpenAI-compat endpoint.

    Uses ChatOpenAI (OpenAI protocol) pointed at LITELLM_BASE_URL.  The
    model alias follows LiteLLM convention: ``<provider>/<model>``
    (e.g. ``deepseek/deepseek-v4-flash``, ``openai/gpt-4o-mini``).  The
    proxy resolves routing, fallback chains, and cost tracking internally.

    Singleton behaviour: MultiRoleLLMRouter creates one instance and
    returns it for every role.  Per-role model resolution happens inside
    ``_litellm_model_name`` at call time — the proxy dispatches to the
    correct underlying provider using the model alias in the request body.
    """

    _DEFAULT_TEMPERATURE = 0.7
    CHAT_MODEL_SPEC: ChatModelSpec = DEFAULT_OPENAI_SPEC

    def __init__(self) -> None:
        """Initialise LiteLLMService — defers actual model build to first call."""
        self.api_key = settings.LITELLM_MASTER_KEY
        self.base_url = settings.LITELLM_BASE_URL
        # Cache key: (litellm_model_name, temperature).
        self._models: dict[tuple[str, float], BaseChatModel] = {}

    @staticmethod
    def _litellm_model_name(role: ModelRole) -> str:
        """Build LiteLLM model alias = '<provider>/<model>'.

        LiteLLM convention: ``deepseek/deepseek-v4-flash``,
        ``openai/gpt-4o-mini``, ``kimi/kimi-k2.6``.
        """
        provider = settings.get_provider_for_role(role).value  # AIProvider str value
        model = settings.get_model(role)
        return f"{provider}/{model}"

    def _get_chat_model(
        self,
        role: ModelRole,
        temperature: float | None = None,
    ) -> BaseChatModel:
        """Build (or reuse cached) ChatOpenAI instance targeting LiteLLM Proxy."""
        spec = self.CHAT_MODEL_SPEC
        litellm_model = self._litellm_model_name(role)
        effective_temp = self._DEFAULT_TEMPERATURE if temperature is None else temperature
        if "kimi/kimi-k2" in litellm_model.lower() and effective_temp != _K2_REQUIRED_TEMPERATURE:
            logger.warning(
                "kimi_k2_temperature_clamped",
                model=litellm_model,
                requested=effective_temp,
                effective=_K2_REQUIRED_TEMPERATURE,
                role=role.value,
            )
            effective_temp = _K2_REQUIRED_TEMPERATURE
        cache_key = (litellm_model, effective_temp)
        if cache_key not in self._models:
            ctx = ChatBuildContext(
                api_key=self.api_key,
                base_url=self.base_url,
                model=litellm_model,
                temperature=effective_temp,
            )
            self._models[cache_key] = _build_chat_from_spec(spec, ctx)
        return self._models[cache_key]

    @staticmethod
    def _resolve_role(model_type: str | ModelRole) -> ModelRole:
        """Resolve legacy string or ModelRole to a canonical ModelRole."""
        if isinstance(model_type, ModelRole):
            return model_type
        return _LEGACY_MODEL_TYPE_MAP.get(model_type, ModelRole.REASONING)

    @staticmethod
    def _convert_to_lc_messages(
        messages: list[dict[str, str]],
        system_prompt: str | None,
    ) -> list:
        """Convert generic message dicts to LangChain message objects."""
        role_map = {
            "user": HumanMessage,
            "assistant": AIMessage,
            "system": SystemMessage,
        }
        lc_messages = []
        if system_prompt:
            lc_messages.append(SystemMessage(content=system_prompt))
        for msg in messages:
            msg_cls = role_map.get(msg.get("role", ""))
            if msg_cls:
                lc_messages.append(msg_cls(content=msg.get("content", "")))
        return lc_messages

    def generate_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        model_type: str | ModelRole = "smart",
        **kwargs: Any,  # noqa: ANN401 — abstract LLM interface
    ) -> str:
        """Generate a text response via LiteLLM Proxy.

        Mirrors OpenAICompatibleService.generate_response semantics:
        logs failures via structlog, propagates exceptions to callers.
        """
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        lc_messages = self._convert_to_lc_messages(messages, system_prompt)
        resolved_role = self._resolve_role(model_type)
        selected_model = self._get_chat_model(resolved_role)
        # Single source of truth for kwarg normalisation.
        self.CHAT_MODEL_SPEC.kwargs_normalizer(kwargs, spec=self.CHAT_MODEL_SPEC)
        try:
            response = selected_model.invoke(lc_messages, **kwargs)
        except Exception as e:
            logger.warning(
                "litellm_dispatch_failed",
                litellm_model=self._litellm_model_name(resolved_role),
                error=str(e),
            )
            raise
        detect_reasoning_budget_exhaustion(
            response,
            model_name=settings.get_model(resolved_role),
        )
        return response.content

    def get_embedding_model(self) -> Any:  # noqa: ANN401 — abstract LLM interface
        """Return OpenAIEmbeddings targeting LiteLLM Proxy /v1/embeddings.

        LiteLLM Proxy forwards /v1/embeddings to the configured embedding
        provider (text-embedding-3-large via openai).
        """
        return OpenAIEmbeddings(
            model=settings.get_model(ModelRole.EMBEDDING),
            api_key=self.api_key,
            base_url=self.base_url,
        )

    def get_client(
        self,
        role: ModelRole = ModelRole.REASONING,
        *,
        temperature: float | None = None,
    ) -> BaseChatModel:
        """Return the chat client for the given role, targeting LiteLLM Proxy."""
        return self._get_chat_model(role, temperature=temperature)
