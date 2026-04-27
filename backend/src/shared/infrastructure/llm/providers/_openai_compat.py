"""Shared base for OpenAI-compatible providers (DeepSeek, Kimi, Qwen).

DeepSeek, Kimi (Moonshot), and Qwen (Alibaba DashScope intl) all expose
OpenAI-compatible chat-completions endpoints. Instead of duplicating the
adapter logic three times, we ship a single base class and three thin
subclasses that only differ in ``api_key`` + ``base_url`` + display name.

Embeddings: the base class raises ``NotImplementedError``. Qwen overrides
``get_embedding_model`` because DashScope exposes a compatible embeddings
endpoint; DeepSeek and Kimi do not.
"""

from typing import Any

import structlog
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.core.config import settings
from src.core.enums import ModelRole
from src.shared.infrastructure.llm.base import BaseLLMService
from src.shared.infrastructure.llm.providers._chat_model_resolver import (
    DEFAULT_OPENAI_SPEC,
    ChatBuildContext,
    ChatModelSpec,
    _build_chat_from_spec,
)
from src.shared.infrastructure.llm.providers._response_validation import (
    detect_reasoning_budget_exhaustion,
)

logger = structlog.get_logger()

_LEGACY_MODEL_TYPE_MAP: dict[str, ModelRole] = {
    "smart": ModelRole.REASONING,
    "fast": ModelRole.FAST,
    "nano": ModelRole.NANO,
    "vision": ModelRole.VISION,
    "agent": ModelRole.AGENT,
}


class OpenAICompatibleService(BaseLLMService):
    """Base adapter for any OpenAI-compatible chat completions API."""

    _DEFAULT_TEMPERATURE = 0.7

    # Subclasses override to swap LangChain client class without
    # touching ``_get_chat_model``. See ``_chat_model_resolver.py`` for
    # the pattern + how to migrate to native partner packages
    # (``langchain_deepseek``, ``langchain_qwq``, …).
    CHAT_MODEL_SPEC: ChatModelSpec = DEFAULT_OPENAI_SPEC

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        provider_name: str,
    ) -> None:
        if not api_key:
            msg = f"{provider_name} API key not configured. Set the corresponding env var or pass api_key explicitly."
            raise ValueError(msg)
        self.api_key = api_key
        self.base_url = base_url
        self.provider_name = provider_name
        # Cache key: ``(model_name, temperature)`` — same rationale as
        # OpenAIService: deepagents 0.5+ rejects RunnableBinding, so each
        # temperature override needs its own client instance.
        self._models: dict[tuple[str, float], BaseChatModel] = {}

    def _get_chat_model(
        self,
        role: ModelRole,
        temperature: float | None = None,
    ) -> BaseChatModel:
        spec = self.CHAT_MODEL_SPEC
        model_name = settings.get_model(role)
        effective_temp = self._DEFAULT_TEMPERATURE if temperature is None else temperature
        cache_key = (model_name, effective_temp)
        if cache_key not in self._models:
            ctx = ChatBuildContext(
                api_key=self.api_key,
                base_url=self.base_url,
                model=model_name,
                temperature=effective_temp,
            )
            self._models[cache_key] = _build_chat_from_spec(spec, ctx)
        return self._models[cache_key]

    @staticmethod
    def _resolve_role(model_type: str | ModelRole) -> ModelRole:
        if isinstance(model_type, ModelRole):
            return model_type
        return _LEGACY_MODEL_TYPE_MAP.get(model_type, ModelRole.REASONING)

    @staticmethod
    def _convert_to_lc_messages(
        messages: list[dict[str, str]],
        system_prompt: str | None,
    ) -> list:
        role_map = {
            "user": HumanMessage,
            "assistant": AIMessage,
            "system": SystemMessage,
        }
        lc_messages = []
        if system_prompt:
            lc_messages.append(SystemMessage(content=system_prompt))
        for msg in messages:
            msg_cls = role_map.get(msg.get("role"))
            if msg_cls:
                lc_messages.append(msg_cls(content=msg.get("content")))
        return lc_messages

    def generate_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        model_type: str | ModelRole = "smart",
        **kwargs: Any,  # noqa: ANN401 — abstract LLM interface
    ) -> str:
        """Synchronous text generation. Logs failures, propagates exceptions."""
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        lc_messages = self._convert_to_lc_messages(messages, system_prompt)
        resolved_role = self._resolve_role(model_type)
        selected_model = self._get_chat_model(resolved_role)
        # Single source of truth, declared per provider via
        # ``CHAT_MODEL_SPEC.kwargs_normalizer``. Spec is passed so
        # reasoning-budget reserve and ``reasoning_effort`` routing land
        # at the wire layer without per-caller plumbing. Subclasses
        # migrating to a non-OpenAI protocol (Gemini, native Anthropic)
        # override the normaliser in their spec.
        self.CHAT_MODEL_SPEC.kwargs_normalizer(kwargs, spec=self.CHAT_MODEL_SPEC)
        try:
            response = selected_model.invoke(lc_messages, **kwargs)
        except Exception as e:
            logger.warning(
                "openai_compat_generate_response_failed",
                provider=self.provider_name,
                error=str(e),
            )
            raise
        detect_reasoning_budget_exhaustion(
            response,
            model_name=settings.get_model(resolved_role),
        )
        return response.content

    def get_embedding_model(self) -> Any:  # noqa: ANN401 — abstract LLM interface
        """Default: not provided. Subclasses override when the provider exposes embeddings."""
        msg = (
            f"{self.provider_name} adapter does not provide embeddings. "
            f"Route ModelRole.EMBEDDING to a provider that does (e.g. OpenAI or Qwen)."
        )
        raise NotImplementedError(msg)

    def get_client(
        self,
        role: ModelRole = ModelRole.REASONING,
        *,
        temperature: float | None = None,
    ) -> BaseChatModel:
        """Return the chat client (concrete class declared by the spec)."""
        return self._get_chat_model(role, temperature=temperature)
