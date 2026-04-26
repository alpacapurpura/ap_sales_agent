"""Qwen (Alibaba DashScope intl) LLM provider (OpenAI-compatible).

Available for ``ModelRole.VISION`` and ``ModelRole.EMBEDDING`` if a tenant
chooses to switch — Sprint 0 keeps OpenAI as default for those roles
because volume is low and latency / quality benchmarks are not yet validated
from LATAM. Activate by setting ``AI_PROVIDER_VISION=qwen`` or
``AI_PROVIDER_EMBEDDING=qwen`` in the environment.

DashScope intl endpoint exposes both chat completions and embeddings via
the same OpenAI-compatible base URL, so this adapter overrides
``get_embedding_model`` (unlike DeepSeek/Kimi which don't ship embeddings).

Refs:
- https://www.alibabacloud.com/help/en/model-studio/compatibility-of-openai-with-dashscope
- https://qwen.readthedocs.io/en/latest/framework/function_call.html
"""

from typing import Any

from langchain_openai import OpenAIEmbeddings

from src.core.config import settings
from src.shared.infrastructure.llm.providers._openai_compat import (
    OpenAICompatibleService,
)


class QwenService(OpenAICompatibleService):
    """Qwen adapter via Alibaba DashScope intl OpenAI-compatible endpoint."""

    def __init__(self, api_key: str | None = None) -> None:
        """Bind chat + embeddings to DashScope intl OpenAI-compatible endpoint."""
        super().__init__(
            api_key=api_key or settings.DASHSCOPE_API_KEY,
            base_url=settings.DASHSCOPE_BASE_URL,
            provider_name="qwen",
        )
        # DashScope intl supports OpenAI-compatible embeddings; expose them
        # so the router can satisfy ``ModelRole.EMBEDDING`` when configured.
        self._embeddings = OpenAIEmbeddings(
            model=settings.AI_MODEL_EMBEDDING,
            api_key=self.api_key,
            base_url=self.base_url,
        )

    def get_embedding_model(self) -> Any:  # noqa: ANN401 — abstract LLM interface
        """Return the OpenAI-compatible embeddings client pointed at DashScope."""
        return self._embeddings
