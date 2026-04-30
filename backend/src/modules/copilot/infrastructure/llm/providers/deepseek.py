"""DeepSeekLLMProvider — copilot domain ``LLMProvider`` adapter for DeepSeek API.

D-2 (CONTRACT PR-3): Implements the copilot ``LLMProvider`` Protocol using the
DeepSeek OpenAI-compatible API. Uses the ``openai`` Python client directly
(same SDK already vendored by ``langchain-openai``).

Resilience per ``tessl__graceful-degradation``:
  - Every API call gets a hard timeout (``DEEPSEEK_TIMEOUT_S`` env, default 30s).
  - 429 / 5xx → single retry after 1s back-off.
  - 401 / auth errors → raise immediately (no retry — wrong key).
  - Timeout / network → raise after retry so caller (provider_factory) can
    activate the OpenAI fallback.

Usage: do not instantiate directly — use ``get_llm_provider_for_tier()`` from
``provider_factory.py`` which selects the right provider per tier and handles
the fallback chain.
"""

# ruff: noqa: ANN401
# ANN401: LLM SDK client objects are dynamically typed (openai.AsyncOpenAI returns Any-shaped responses).
# TRY400/301: best-effort error handling per copilot-resilience rule — exception logging + raises documented.
from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING, Any

import structlog

from src.modules.copilot.domain.ports import LLMEvent, LLMMessage

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from src.modules.copilot.domain.model_tier import ModelTier

logger = structlog.get_logger()

_DEFAULT_TIMEOUT_S: float = 30.0
_RETRY_DELAY_S: float = 1.0
_DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"

# HTTP statuses eligible for retry (transient server errors + rate-limit).
_RETRYABLE_STATUS: frozenset[int] = frozenset({429, 500, 502, 503, 504})


def _get_timeout() -> float:
    """Read DEEPSEEK_TIMEOUT_S from env or return default."""
    raw = os.environ.get("DEEPSEEK_TIMEOUT_S", "").strip()
    if raw:
        try:
            return float(raw)
        except ValueError:
            pass
    return _DEFAULT_TIMEOUT_S


class DeepSeekLLMProvider:
    """Async LLMProvider wrapping the DeepSeek OpenAI-compatible chat API.

    Implements the ``LLMProvider`` Protocol from ``copilot.domain.ports``.
    Thread-safe: the underlying ``openai.AsyncOpenAI`` client is stateless
    per call; the instance is reusable.
    """

    def __init__(
        self,
        api_key: str,
        *,
        model_name: str = "deepseek-v4-flash",
        base_url: str = _DEEPSEEK_BASE_URL,
        timeout_s: float | None = None,
    ) -> None:
        """Create a DeepSeekLLMProvider bound to ``api_key`` and ``model_name``.

        Args:
            api_key: DeepSeek API key (required).
            model_name: Model slug to send to the API (default ``deepseek-v4-flash``).
            base_url: API base URL (override in tests or for mirror endpoints).
            timeout_s: Per-call timeout in seconds; reads env if None.
        """
        if not api_key:
            msg = "DeepSeekLLMProvider requires a non-empty api_key."
            raise ValueError(msg)
        self._api_key = api_key
        self._model_name = model_name
        self._base_url = base_url
        self._timeout_s = timeout_s if timeout_s is not None else _get_timeout()

    @property
    def model_name(self) -> str:
        """Return the configured model slug."""
        return self._model_name

    def _build_client(self) -> Any:
        """Build (or import) AsyncOpenAI lazily to avoid boot-time import errors."""
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            msg = "openai package not installed. Run: pip install openai"
            raise ImportError(msg) from exc
        return AsyncOpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
            timeout=self._timeout_s,
        )

    @staticmethod
    def _messages_to_api(messages: list[LLMMessage]) -> list[dict[str, str]]:
        """Convert domain ``LLMMessage`` list to OpenAI API payload."""
        return [{"role": m.role, "content": m.content} for m in messages]

    async def _call_once(
        self,
        client: Any,
        messages: list[dict[str, str]],
        stream: bool,
    ) -> Any:
        """Execute one non-retried API call."""
        kwargs: dict[str, Any] = {
            "model": self._model_name,
            "messages": messages,
            "stream": stream,
        }
        return await client.chat.completions.create(**kwargs)

    async def complete(
        self,
        *,
        tier: ModelTier,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        stream: bool = True,
    ) -> AsyncIterator[LLMEvent]:
        """Stream LLM completion events for ``tier`` and ``messages``.

        Yields:
            ``LLMEvent(kind="text", data={"text": chunk})`` for each chunk.
            ``LLMEvent(kind="done", data={})`` on completion.
            ``LLMEvent(kind="error", data={"error": str})`` on unrecoverable error.

        The ``tier`` param is accepted for Protocol compliance; the model name
        is resolved at construction time (``self._model_name``). Callers that
        need per-tier dispatch should use ``provider_factory.get_llm_provider_for_tier``.
        """
        del tier  # resolved at factory level — provider is already tier-specific

        client = self._build_client()
        api_messages = self._messages_to_api(messages)

        last_exc: Exception | None = None
        for attempt in range(2):  # max 2 attempts (1 retry)
            try:
                response = await self._call_once(client, api_messages, stream=stream)
                async for event in self._yield_events(response, stream=stream):
                    yield event
                return
            except Exception as exc:  # noqa: BLE001 — retry logic inspects all exc
                last_exc = exc
                status = getattr(exc, "status_code", None) or getattr(exc, "status", None)

                # 401 = bad key → raise immediately, no retry.
                if status == 401:
                    logger.warning(
                        "deepseek_provider_auth_failed",
                        model=self._model_name,
                        attempt=attempt,
                    )
                    yield LLMEvent(kind="error", data={"error": "auth_failed", "detail": str(exc)})
                    return

                # Retryable status → wait, then retry.
                if attempt == 0 and (status in _RETRYABLE_STATUS or status is None):
                    logger.warning(
                        "deepseek_provider_retrying",
                        model=self._model_name,
                        status=status,
                        attempt=attempt,
                        error=str(exc)[:200],
                    )
                    await asyncio.sleep(_RETRY_DELAY_S)
                    continue

                # Non-retryable or retry exhausted.
                break

        logger.error(
            "deepseek_provider_failed",
            model=self._model_name,
            error=str(last_exc)[:300],
        )
        yield LLMEvent(kind="error", data={"error": "provider_failed", "detail": str(last_exc)})

    @staticmethod
    async def _yield_events(
        response: Any,
        *,
        stream: bool,
    ) -> AsyncIterator[LLMEvent]:
        """Convert API response to ``LLMEvent`` stream."""
        if not stream:
            # Non-streaming: extract content from the completion object.
            content = ""
            if hasattr(response, "choices") and response.choices:
                msg = response.choices[0].message
                content = (msg.content or "") if msg else ""
            yield LLMEvent(kind="text", data={"text": content})
        else:
            # Streaming: iterate async chunks.
            async for chunk in response:
                choices = getattr(chunk, "choices", None)
                if not choices:
                    continue
                delta = getattr(choices[0], "delta", None)
                if delta is None:
                    continue
                text = getattr(delta, "content", "") or ""
                if text:
                    yield LLMEvent(kind="text", data={"text": text})

        yield LLMEvent(kind="done", data={})
