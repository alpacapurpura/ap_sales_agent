from typing import Optional
from src.config import settings
from src.core.schema import AIProvider
from src.core.llm.base import BaseLLMService
from src.core.llm.providers.openai import OpenAIService

class LLMFactory:
    """
    Factory Class to instantiate the correct LLM Service based on configuration.
    """
    
    _instance: Optional[BaseLLMService] = None
    
    @classmethod
    def get_service(cls) -> BaseLLMService:
        """
        Returns the singleton instance of the LLM Service.
        Creates it if it doesn't exist.
        """
        if cls._instance is None:
            cls._instance = cls._create_service()
        return cls._instance
    
    @classmethod
    def _create_service(cls) -> BaseLLMService:
        provider = settings.AI_PROVIDER.lower()
        
        if provider == AIProvider.OPENAI:
            return OpenAIService()
        elif provider == AIProvider.GEMINI:
            from src.core.llm.providers.gemini import GeminiService
            return GeminiService()
        else:
            raise ValueError(f"Unsupported AI Provider: {provider}")

# Global accessor
llm_service = LLMFactory.get_service()
