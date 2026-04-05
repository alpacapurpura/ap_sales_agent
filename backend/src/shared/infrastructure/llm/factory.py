from src.core.config import settings
from src.core.enums import AIProvider
from src.shared.infrastructure.llm.base import BaseLLMService
from src.shared.infrastructure.llm.providers.openai import OpenAIService


class LLMFactory:
    """
    Factory Class to instantiate the correct LLM Service based on configuration.
    """

    _instance: BaseLLMService | None = None

    @classmethod
    def get_service(cls) -> BaseLLMService:
        """
        Returns the singleton instance of the LLM Service (Platform Default).
        Creates it if it doesn't exist.
        """
        if cls._instance is None:
            cls._instance = cls._create_service_instance(settings.AI_PROVIDER.lower())
        return cls._instance

    @classmethod
    def get_service_for_tenant(cls, tenant) -> BaseLLMService:
        """
        Creates a new service instance for the specific tenant configuration.
        """
        provider = settings.AI_PROVIDER.lower()

        # Check for Tenant-specific keys
        api_key = None
        if provider == AIProvider.OPENAI:
            api_key = tenant.openai_api_key
        elif provider == AIProvider.GEMINI:
            api_key = tenant.gemini_api_key

        # 1. User provided key -> Use it (Create new instance)
        if api_key:
            return cls._create_service_instance(provider, api_key)

        # 2. No user key, but allowed to use platform keys -> Use Singleton
        if tenant.can_use_platform_keys:
            return cls.get_service()

        # 3. No permission -> Error
        raise ValueError(
            "AI Configuration Error: No API Key provided and platform keys are disabled for this tenant."
        )

    @classmethod
    def _create_service_instance(
        cls, provider: str, api_key: str | None = None
    ) -> BaseLLMService:
        if provider == AIProvider.OPENAI:
            return OpenAIService(api_key=api_key)
        if provider == AIProvider.GEMINI:
            from src.shared.infrastructure.llm.providers.gemini import GeminiService

            return GeminiService(api_key=api_key)
        raise ValueError(f"Unsupported AI Provider: {provider}")

    # Deprecated: Kept for internal compatibility
    @classmethod
    def _create_service(cls) -> BaseLLMService:
        return cls._create_service_instance(settings.AI_PROVIDER.lower())


# Global accessor
llm_service = LLMFactory.get_service()
