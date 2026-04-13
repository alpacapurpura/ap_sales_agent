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

    def generate_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        model_type: str | ModelRole = "smart",
        **kwargs,
    ) -> str:
        """
        Adapts the generic message format to LangChain's format and invokes the model.
        Args:
            model_type: ModelRole enum or legacy string ("smart"/"fast")
        """
        # Init vars for logging in finally block
        response_text = ""
        tokens_in = 0
        tokens_out = 0
        selected_model = None
        meta_log = {}

        try:
            # --- ROBUSTNESS CHECK ---
            if isinstance(messages, str):
                messages = [{"role": "user", "content": messages}]

            lc_messages = []

            if system_prompt:
                lc_messages.append(SystemMessage(content=system_prompt))

            for msg in messages:
                role = msg.get("role")
                content = msg.get("content")
                if role == "user":
                    lc_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    lc_messages.append(AIMessage(content=content))
                elif role == "system":
                    lc_messages.append(SystemMessage(content=content))

            # Select Model based on Role
            resolved_role = self._resolve_role(model_type)
            selected_model = self._get_chat_model(resolved_role)

            # --- PARAMETER OVERRIDE ---
            # Allow overriding generation parameters per call
            # Note: LangChain 'invoke' might not accept all params directly as kwargs depending on version/method.
            # For ChatOpenAI, we usually pass them to the constructor OR bind them.
            # But 'invoke' often propagates extra args to the underlying API call (e.g. temperature, max_tokens).

            # Explicitly extract known OpenAI params
            # temperature, max_tokens, top_p, presence_penalty, frequency_penalty

            call_params = {}
            if "temperature" in kwargs:
                call_params["temperature"] = kwargs.pop("temperature")
            if "max_tokens" in kwargs:
                call_params["max_tokens"] = kwargs.pop("max_tokens")
            if "max_output_tokens" in kwargs:
                call_params["max_tokens"] = kwargs.pop("max_output_tokens")  # Alias
            if "top_p" in kwargs:
                call_params["top_p"] = kwargs.pop("top_p")
            if "presence_penalty" in kwargs:
                call_params["presence_penalty"] = kwargs.pop("presence_penalty")
            if "frequency_penalty" in kwargs:
                call_params["frequency_penalty"] = kwargs.pop("frequency_penalty")

            # Extract metadata passed in kwargs (e.g. RAG context) BEFORE invoke
            # to avoid collision with LangChain internals
            if "metadata" in kwargs:
                meta_log = kwargs.pop("metadata")

            # If we have params, we might need to bind them or pass to invoke.
            # LangChain's invoke(..., **kwargs) usually passes extra params to the model run.
            # Let's merge them back into kwargs for invoke.
            kwargs.update(call_params)

            # --- LLM CALL ---
            response = selected_model.invoke(lc_messages, **kwargs)
            response_text = response.content

            # Extract Usage Metadata
            usage = response.response_metadata.get("token_usage", {})
            tokens_in = usage.get("prompt_tokens", 0)
            tokens_out = usage.get("completion_tokens", 0)

        except Exception as e:
            # We still want to log the error if possible
            response_text = f"ERROR: {e!s}"
            raise e
        finally:
            # --- TRACING LOGIC ---
            trace_id = current_trace_id.get()
            if trace_id:
                try:
                    db = SessionLocal()
                    repo = AuditRepository(db)
                    # Reconstruct prompt for logging
                    full_prompt_str = f"System: {system_prompt}\nMessages: {messages}"

                    # Ensure model name is captured even if selection failed
                    model_name = (
                        selected_model.model_name if selected_model else "unknown"
                    )

                    # Extract metadata passed in kwargs (e.g. RAG context)
                    meta_log = kwargs.get("metadata", {})

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
                except Exception as log_err:
                    logger.warning("llm_call_logging_failed", error=str(log_err))

        return response_text

    def get_embedding_model(self) -> Any:
        return self.embeddings

    def get_client(self, role: ModelRole = ModelRole.REASONING) -> ChatOpenAI:
        return self._get_chat_model(role)
