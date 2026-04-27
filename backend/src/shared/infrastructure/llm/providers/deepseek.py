"""DeepSeek LLM provider — native ``langchain-deepseek`` package.

Used for ``ModelRole.REASONING`` / ``HEAVY`` by default — ~9x cheaper input
and ~35x cheaper output vs GPT-4o, with automatic 90% cache discount on
repeated prefixes (lighthouse, brand_summary, sticky system prompts).

Migrated 2026-04-27 from raw ``ChatOpenAI`` + base_url override to the
official ``langchain_deepseek.ChatDeepSeek`` package. Wins:

* DeepSeek-V4 ``reasoning_content`` round-trip (was lost via ChatOpenAI).
* Tool calling on the official ``/beta/chat/completions`` endpoint when
  ``strict=True`` is requested via ``with_structured_output(strict=True)``.
* DeepSeek-specific streaming chunk shape parsed by the partner package
  rather than guessed by the OpenAI parser.
* Future LangChain version bumps for the partner package land aligned
  with DeepSeek API releases.

The base class still drives caching, kwargs normalisation, and the
``CHAT_MODEL_SPEC`` resolver — only the spec changed. To revert to raw
``ChatOpenAI`` would mean swapping ``DEEPSEEK_NATIVE_SPEC`` back to
``DEFAULT_OPENAI_SPEC``.

Refs:
- https://api-docs.deepseek.com/guides/tool_calls
- https://api-docs.deepseek.com/quick_start/pricing
- https://python.langchain.com/api_reference/deepseek/chat_models/langchain_deepseek.chat_models.ChatDeepSeek.html
"""

from langchain_deepseek import ChatDeepSeek

from src.core.config import settings
from src.shared.infrastructure.llm.providers._chat_model_resolver import (
    ChatModelSpec,
    build_with_chat_class,
)
from src.shared.infrastructure.llm.providers._kwargs import (
    normalize_openai_protocol_kwargs,
)
from src.shared.infrastructure.llm.providers._openai_compat import (
    OpenAICompatibleService,
)

DEEPSEEK_NATIVE_SPEC: ChatModelSpec = ChatModelSpec(
    chat_class=ChatDeepSeek,
    builder=build_with_chat_class(ChatDeepSeek),
    kwargs_normalizer=normalize_openai_protocol_kwargs,
    library_name="langchain_deepseek",
)


class DeepSeekService(OpenAICompatibleService):
    """DeepSeek adapter via the official ``langchain-deepseek`` package."""

    CHAT_MODEL_SPEC: ChatModelSpec = DEEPSEEK_NATIVE_SPEC

    def __init__(self, api_key: str | None = None) -> None:
        """Bind the DeepSeek API key.

        ``base_url`` is kept for the spec contract but the native
        package owns its own endpoint resolution.
        """
        super().__init__(
            api_key=api_key or settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            provider_name="deepseek",
        )
