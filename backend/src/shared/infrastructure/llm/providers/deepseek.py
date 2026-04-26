"""DeepSeek LLM provider (OpenAI-compatible).

Used for ``ModelRole.REASONING`` / ``HEAVY`` by default — ~9x cheaper input
and ~35x cheaper output vs GPT-4o, with automatic 90% cache discount on
repeated prefixes (lighthouse, brand_summary, sticky system prompts).

Tool calling and streaming are stable on deepseek-chat and deepseek-reasoner
(``DeepSeek-V3.2`` onward). LangChain integration goes through ``ChatOpenAI``
with ``base_url`` override — no extra package needed.

Refs:
- https://api-docs.deepseek.com/guides/tool_calls
- https://api-docs.deepseek.com/quick_start/pricing
"""

from src.core.config import settings
from src.shared.infrastructure.llm.providers._openai_compat import (
    OpenAICompatibleService,
)


class DeepSeekService(OpenAICompatibleService):
    """DeepSeek adapter — points the OpenAI SDK at DeepSeek's compatible endpoint."""

    def __init__(self, api_key: str | None = None) -> None:
        """Bind the OpenAI-compat base to DeepSeek's endpoint + key."""
        super().__init__(
            api_key=api_key or settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            provider_name="deepseek",
        )
