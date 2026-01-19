from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseLLMService(ABC):
    """
    Abstract Base Class for LLM Providers (Strategy Pattern).
    Defines the contract that all concrete LLM providers must follow.
    """

    @abstractmethod
    def generate_response(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None, **kwargs) -> str:
        """
        Generates a text response from the LLM.
        
        Args:
            messages: List of message dicts [{"role": "user", "content": "..."}, ...]
            system_prompt: Optional system instruction to prepend or set.
            **kwargs: Extra parameters like temperature, max_tokens, etc.
            
        Returns:
            str: The generated text response.
        """
        pass

    @abstractmethod
    def get_embedding_model(self) -> Any:
        """
        Returns a LangChain-compatible embedding model object.
        Useful for integration with Vector Stores like Qdrant.
        """
        pass
    
    @abstractmethod
    def get_client(self) -> Any:
        """
        Returns the underlying client (e.g. OpenAI client) if direct access is needed.
        """
        pass
