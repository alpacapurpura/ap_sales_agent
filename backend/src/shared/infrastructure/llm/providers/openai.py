from typing import Any

import structlog
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from src.core.config import settings
from src.core.enums import ModelRole
from src.modules.sales_agent.infrastructure.db.database import SessionLocal
from src.modules.sales_agent.infrastructure.memory.audit_repository import (
    AuditRepository,
)
from src.modules.sales_agent.infrastructure.monitoring.tracing import current_trace_id
from src.shared.infrastructure.llm.base import BaseLLMService

logger = structlog.get_logger()

# Legacy string → ModelRole mapping (backwards-compat)
_LEGACY_MODEL_TYPE_MAP: dict[str, ModelRole] = {
    "smart": ModelRole.REASONING,
    "fast": ModelRole.FAST,
    "vision": ModelRole.VISION,
    "agent": ModelRole.AGENT,
}


class OpenAIService(BaseLLMService):
    """
    Concrete implementation for OpenAI (Adapter Pattern).
    Uses role-based model selection via ModelRole enum.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self._models: dict[str, ChatOpenAI] = {}  # cache by model name

        self.embeddings = OpenAIEmbeddings(
            model=settings.get_model(ModelRole.EMBEDDING),
            api_key=self.api_key,
        )

    def _get_chat_model(self, role: ModelRole) -> ChatOpenAI:
        """Get or create a ChatOpenAI instance for the given role."""
        model_name = settings.get_model(role)
        if model_name not in self._models:
            self._models[model_name] = ChatOpenAI(
                model=model_name,
                api_key=self.api_key,
                temperature=0.7,
            )
        return self._models[model_name]

    @staticmethod
    def _resolve_role(model_type: str | ModelRole) -> ModelRole:
        """Resolve a legacy string or ModelRole to a ModelRole."""
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
            msg_cls = role_map.get(msg.get("role"))
            if msg_cls:
                lc_messages.append(msg_cls(content=msg.get("content")))
        return lc_messages

    @staticmethod
    def _extract_call_params(kwargs: dict) -> tuple[dict, dict]:
        """Extract OpenAI call params and metadata from kwargs. Returns (call_params, meta_log)."""
        param_keys = (
            "temperature",
            "max_tokens",
            "top_p",
            "presence_penalty",
            "frequency_penalty",
        )
        call_params = {}
        for key in param_keys:
            if key in kwargs:
                call_params[key] = kwargs.pop(key)
        # max_output_tokens is an alias for max_tokens
        if "max_output_tokens" in kwargs:
            call_params["max_tokens"] = kwargs.pop("max_output_tokens")
        meta_log = kwargs.pop("metadata", {})
        return call_params, meta_log

    def _log_to_trace(
        self,
        system_prompt: str | None,
        messages: list,
        selected_model,
        response_text: str,
        tokens_in: int,
        tokens_out: int,
        meta_log: dict,
    ) -> None:
        """Log LLM call to the tracing audit repository if a trace is active."""
        trace_id = current_trace_id.get()
        if not trace_id:
            return
        try:
            db = SessionLocal()
            repo = AuditRepository(db)
            full_prompt_str = f"System: {system_prompt}\nMessages: {messages}"
            model_name = selected_model.model_name if selected_model else "unknown"
            repo.create_llm_log(
                trace_id=trace_id,
                model=model_name,
                prompt_template=meta_log.get("prompt_template", "unknown"),
                prompt_rendered=full_prompt_str,
                response_text=response_text,
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                metadata=meta_log,
            )
            repo.close()
        except Exception as log_err:  # noqa: BLE001 — provider resilience
            logger.warning("llm_call_logging_failed", error=str(log_err))

    def generate_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        model_type: str | ModelRole = "smart",
        **kwargs,
    ) -> str:
        """Adapts the generic message format to LangChain's format and invokes the model."""
        response_text = ""
        tokens_in = 0
        tokens_out = 0
        selected_model = None
        meta_log: dict = {}

        try:
            if isinstance(messages, str):
                messages = [{"role": "user", "content": messages}]

            lc_messages = self._convert_to_lc_messages(messages, system_prompt)
            resolved_role = self._resolve_role(model_type)
            selected_model = self._get_chat_model(resolved_role)

            call_params, meta_log = self._extract_call_params(kwargs)
            kwargs.update(call_params)

            response = selected_model.invoke(lc_messages, **kwargs)
            response_text = response.content

            usage = response.response_metadata.get("token_usage", {})
            tokens_in = usage.get("prompt_tokens", 0)
            tokens_out = usage.get("completion_tokens", 0)

        except Exception as e:
            response_text = f"ERROR: {e!s}"
            raise
        finally:
            self._log_to_trace(
                system_prompt,
                messages,
                selected_model,
                response_text,
                tokens_in,
                tokens_out,
                meta_log,
            )

        return response_text

    def get_embedding_model(self) -> Any:
        return self.embeddings

    def get_client(self, role: ModelRole = ModelRole.REASONING) -> ChatOpenAI:
        return self._get_chat_model(role)
