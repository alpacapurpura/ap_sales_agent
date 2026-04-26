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


_K2_REQUIRED_TEMPERATURE = 0.6
"""Kimi K2.6 with ``thinking={"type": "disabled"}`` only accepts ``temperature=0.6``.

The thinking-enabled variant requires ``temperature=1.0`` instead. Until
LangChain round-trips ``reasoning_content`` we keep thinking disabled (TP5-B8),
so 0.6 is the live constraint."""


class KimiService(OpenAICompatibleService):
    """Kimi adapter — Moonshot AI's OpenAI-compatible endpoint.

    K2.6 has two coupled invariants:

    - ``thinking`` must be ``{"type": "disabled"}`` for every call. With
      thinking enabled, every assistant message that issued a tool call
      must carry ``reasoning_content`` on the wire — LangChain doesn't
      preserve that field across turns yet, so post-tool re-invocations 400
      with ``thinking is enabled but reasoning_content is missing in
      assistant tool call message at index N`` (TP5-B8).
    - With thinking disabled, K2.6 only accepts ``temperature=0.6``;
      enabling thinking would flip the requirement to ``temperature=1.0``
      (TP4-B4). Both constraints are server-enforced and surface as
      ``invalid_request_error: only X is allowed for this model``.

    The adapter clamps any explicit override (e.g. the deep-agent harness'
    ``temperature=0.6``) to ``_K2_REQUIRED_TEMPERATURE`` and forces
    ``extra_body={"thinking": {"type": "disabled"}}`` on every K2.6 client.
    Re-enable thinking + plumb ``reasoning_content`` once chain-of-thought
    visibility is on the roadmap; the constants here are the only knob to
    flip.
    """

    _DEFAULT_TEMPERATURE = _K2_REQUIRED_TEMPERATURE

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
        is_k2 = "k2" in model_name.lower()
        if is_k2 and temperature is not None and temperature != _K2_REQUIRED_TEMPERATURE:
            logger.warning(
                "kimi_k2_temperature_clamped",
                model=model_name,
                requested=temperature,
                effective=_K2_REQUIRED_TEMPERATURE,
                role=role.value,
            )
            temperature = _K2_REQUIRED_TEMPERATURE
        client = super()._get_chat_model(role, temperature=temperature)
        if is_k2:
            existing_extra = client.model_kwargs.get("extra_body") or {}
            client.model_kwargs["extra_body"] = {
                **existing_extra,
                "thinking": {"type": "disabled"},
            }
        return client
