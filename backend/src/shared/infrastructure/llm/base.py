from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.core.enums import ModelRole


class BaseLLMService(ABC):
    """
    Abstract Base Class for LLM Providers (Strategy Pattern).
    Defines the contract that all concrete LLM providers must follow.
    """

    @abstractmethod
    def generate_response(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None, model_type: str = "smart", **kwargs) -> str:
        """
        Generates a text response from the LLM.

        Args:
            messages: List of message dicts [{"role": "user", "content": "..."}, ...]
            system_prompt: Optional system instruction to prepend or set.
            model_type: ModelRole enum or legacy string ("smart"/"fast").
            **kwargs: Extra parameters like temperature, max_tokens, etc.

        Returns:
            str: The generated text response.
        """
        pass

    @abstractmethod
    def get_embedding_model(self) -> Any:
        """Returns a LangChain-compatible embedding model object."""
        pass

    @abstractmethod
    def get_client(self, role: ModelRole = ModelRole.REASONING) -> Any:
        """Returns the underlying chat model client for the given role."""
        pass
