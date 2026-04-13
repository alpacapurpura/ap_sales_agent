from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from src.core.config import settings
from src.core.enums import ModelRole
from src.shared.infrastructure.llm.base import BaseLLMService


class GeminiService(BaseLLMService):
    """
    Concrete implementation for Google Gemini (Adapter Pattern).
    """

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        # Gemini embedding model usually is "models/embedding-001"
        self.embedding_model_name = "models/embedding-001"

        if not self.api_key:
            pass

        # Initialize LangChain Chat Model
        self.chat_model = ChatGoogleGenerativeAI(
            model=self.model_name,
            api_key=self.api_key,
            temperature=0.7,
        )

        # Initialize Embeddings Model
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=self.embedding_model_name,
            api_key=self.api_key,
        )

    def generate_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        model_type: str = "smart",
        **kwargs: Any,  # noqa: ANN401 — Gemini SDK types
    ) -> str:
        """
        Adapts the generic message format to LangChain's format for Gemini.
        """
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

        try:
            response = self.chat_model.invoke(lc_messages, **kwargs)
            response_text = response.content

            # Usage metadata available but logging removed to decouple shared from sales_agent

        except Exception as e:
            response_text = f"ERROR: {e!s}"
            raise

        # Logging logic removed to decouple shared from sales_agent.

        return response_text

    def get_embedding_model(self) -> Any:  # noqa: ANN401 — Gemini SDK types
        return self.embeddings

    def get_client(self, role: ModelRole = ModelRole.REASONING) -> Any:  # noqa: ANN401 — Gemini SDK types
        return self.chat_model
