"""Copilot LLM provider factory — tier → LLMProvider with fallback chain.

D-6 (CONTRACT PR-3): Factory that reads COPILOT_TIER_*_PROVIDER env flags and
returns the appropriate LLMProvider implementation. Includes single-retry fallback
to OpenAI when DeepSeek raises.

Fallback chain (per D-6):
  1. Read ``COPILOT_TIER_{TIER}_PROVIDER`` env.
  2. If ``deepseek`` → return ``DeepSeekLLMProvider``.
  3. Else → return ``OpenAILLMProvider``.
  4. On provider failure at call time: single retry → if still fails → raise.

Usage::

    provider = get_llm_provider_for_tier(ModelTier.NANO)
    async for event in await provider.complete(tier=ModelTier.NANO, messages=[...]):
        ...
"""

# ruff: noqa: ANN401, TRY400
# ANN401: LLMProvider primary/fallback are duck-typed (Protocol) — Any is intentional for factory composition.
# TRY400: best-effort logging per copilot-resilience.
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from src.modules.copilot.domain.ports import LLMEvent, LLMMessage
from src.modules.copilot.infrastructure.llm.model_config import (
    get_provider_for_tier,
    get_tier_metadata,
    validate_deepseek_api_key,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from src.modules.copilot.domain.model_tier import ModelTier

logger = structlog.get_logger()


class _FallbackLLMProvider:
    """Wraps a primary provider with a single-retry fallback to a secondary.

    D-6: if DeepSeek raises on a call, we fall back to OpenAI for that
    one request (no recursive fallback).
    """

    def __init__(
        self,
        primary: Any,
        fallback: Any,
        *,
        tier: ModelTier,
    ) -> None:
        """Wire primary + fallback providers for ``tier``."""
        self._primary = primary
        self._fallback = fallback
        self._tier = tier

    async def complete(
        self,
        *,
        tier: ModelTier,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        stream: bool = True,
    ) -> AsyncIterator[LLMEvent]:
        """Attempt primary; on error yield events from fallback (single retry)."""
        # Collect primary events first; detect error events.
        collected: list[LLMEvent] = []
        has_error = False

        async for event in await self._primary.complete(
            tier=tier,
            messages=messages,
            tools=tools,
            stream=stream,
        ):
            if event.kind == "error":
                has_error = True
                logger.warning(
                    "copilot_provider_fallback_triggered",
                    tier=tier.value,
                    primary=type(self._primary).__name__,
                    fallback=type(self._fallback).__name__,
                    error=event.data.get("error"),
                )
                break
            collected.append(event)

        if not has_error:
            # Primary succeeded — yield all collected events.
            for event in collected:
                yield event
            return

        # Primary failed — delegate to fallback (no recursive fallback).
        logger.info(
            "copilot_provider_using_fallback",
            tier=tier.value,
            fallback=type(self._fallback).__name__,
        )
        async for event in await self._fallback.complete(
            tier=tier,
            messages=messages,
            tools=tools,
            stream=stream,
        ):
            yield event


class _OpenAILLMProvider:
    """Minimal copilot ``LLMProvider`` adapter for the OpenAI API.

    Wraps the shared ``LLMFactory`` so the copilot module does not import
    OpenAI SDK directly (factory handles that). Satisfies the copilot domain
    ``LLMProvider`` Protocol.
    """

    def __init__(self, model_name: str) -> None:
        """Bind to ``model_name``."""
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        """Return the configured model slug."""
        return self._model_name

    async def complete(
        self,
        *,
        tier: ModelTier,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        stream: bool = True,
    ) -> AsyncIterator[LLMEvent]:
        """Delegate to the shared OpenAI infrastructure via async wrapper."""
        # Use openai directly to match the LLMProvider protocol (async generator).
        # The shared LLMFactory uses synchronous LangChain clients; we call
        # openai async client for the copilot LLMProvider port to be truly async.
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            msg = "openai package not installed."
            raise ImportError(msg) from exc

        from src.core.config import settings

        api_key = settings.OPENAI_API_KEY
        client = AsyncOpenAI(api_key=api_key, timeout=30.0)
        api_messages = [{"role": m.role, "content": m.content} for m in messages]

        try:
            response: Any = await client.chat.completions.create(
                model=self._model_name,
                messages=api_messages,  # type: ignore[arg-type]
                stream=stream,
            )
            if not stream:
                content = ""
                if hasattr(response, "choices") and response.choices:
                    msg_obj = response.choices[0].message
                    content = (msg_obj.content or "") if msg_obj else ""
                yield LLMEvent(kind="text", data={"text": content})
            else:
                async for chunk in response:
                    choices = getattr(chunk, "choices", None)
                    if not choices:
                        continue
                    delta = getattr(choices[0], "delta", None)
                    text = getattr(delta, "content", "") or ""
                    if text:
                        yield LLMEvent(kind="text", data={"text": text})
            yield LLMEvent(kind="done", data={})
        except Exception as exc:  # noqa: BLE001
            logger.error("openai_llm_provider_failed", error=str(exc)[:300])
            yield LLMEvent(kind="error", data={"error": "provider_failed", "detail": str(exc)})


def get_llm_provider_for_tier(tier: ModelTier) -> Any:
    """Return the LLMProvider for ``tier`` per env-flag config.

    D-6 fallback chain:
      1. Read ``COPILOT_TIER_{TIER}_PROVIDER`` env.
      2. ``deepseek`` → ``DeepSeekLLMProvider`` (raises ``ValueError`` if key missing).
      3. Other / unset → ``_OpenAILLMProvider``.
      4. If provider is deepseek → wrap in ``_FallbackLLMProvider`` with OpenAI fallback.

    Returns an object satisfying the copilot ``LLMProvider`` Protocol.
    """
    provider_slug = get_provider_for_tier(tier)
    tier_meta = get_tier_metadata(tier)

    if provider_slug == "deepseek":
        api_key = validate_deepseek_api_key()
        from src.modules.copilot.infrastructure.llm.providers.deepseek import (
            DeepSeekLLMProvider,
        )

        primary = DeepSeekLLMProvider(
            api_key=api_key,
            model_name=tier_meta.model_name,
        )
        # Fallback to OpenAI with the static (non-overridden) model name.
        from src.modules.copilot.domain.model_tier import TIER_METADATA

        static_meta = TIER_METADATA[tier]
        fallback = _OpenAILLMProvider(model_name=static_meta.model_name)
        return _FallbackLLMProvider(primary=primary, fallback=fallback, tier=tier)

    # Default: OpenAI with the (potentially env-overridden) model name.
    return _OpenAILLMProvider(model_name=tier_meta.model_name)
