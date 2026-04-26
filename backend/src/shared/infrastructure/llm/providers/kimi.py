"""Kimi (Moonshot AI) LLM provider (OpenAI-compatible).

Used for ``ModelRole.AGENT`` by default — Kimi K2.6 leads agentic
benchmarks (4000 tool calls per run, beats GPT-5.4 on SWE-Bench Pro).
Built specifically for long-horizon agentic workflows; pairs well with
the deepagents harness used by Nicolify's copilot.

LangChain integration is the OpenAI SDK with ``base_url`` override.
The intl endpoint is ``https://api.moonshot.ai/v1`` (not the .cn domain).

Refs:
- https://platform.kimi.ai/docs/guide/kimi-k2-6-quickstart
- https://www.kimi.com/blog/kimi-k2-6
"""

import structlog
from langchain_openai import ChatOpenAI

from src.core.config import settings
from src.core.enums import ModelRole
from src.shared.infrastructure.llm.providers._openai_compat import (
    OpenAICompatibleService,
)

logger = structlog.get_logger()


class KimiService(OpenAICompatibleService):
    """Kimi adapter — Moonshot AI's OpenAI-compatible endpoint.

    ``_DEFAULT_TEMPERATURE = 1.0`` because Kimi K2.6 (the agentic / thinking
    variant) only accepts ``temperature=1`` — sending any other value
    yields ``invalid_request_error: only 1 is allowed for this model``,
    same constraint pattern as OpenAI's o1/o3 reasoning models.

    Callers that pass an explicit override (e.g. the deep-agent harness
    hardcodes ``temperature=0.6`` for ``ModelRole.AGENT``) get **clamped**
    to ``1.0`` for K2.6 with a structlog warning so the rest of the stack
    keeps the override syntax intact at every provider (TP4-B4 regression).
    """

    _DEFAULT_TEMPERATURE = 1.0

    def __init__(self, api_key: str | None = None) -> None:
        """Bind the OpenAI-compat base to Moonshot's endpoint + key."""
        super().__init__(
            api_key=api_key or settings.KIMI_API_KEY,
            base_url=settings.KIMI_BASE_URL,
            provider_name="kimi",
        )

    def _get_chat_model(
        self,
        role: ModelRole,
        temperature: float | None = None,
    ) -> ChatOpenAI:
        model_name = settings.get_model(role)
        if "k2" in model_name.lower() and temperature is not None and temperature != 1.0:
            logger.warning(
                "kimi_k2_temperature_clamped",
                model=model_name,
                requested=temperature,
                effective=1.0,
                role=role.value,
            )
            temperature = 1.0
        return super()._get_chat_model(role, temperature=temperature)
