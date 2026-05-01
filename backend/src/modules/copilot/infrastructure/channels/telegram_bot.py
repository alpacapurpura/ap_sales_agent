"""Copilot Telegram bot adapter — global Nicolify, NOT per-tenant.

D-PI5-001 + D-PI5-005 + D-PI5-027 (rate limiting). Reuses
``escape_markdown_v2`` from shared (NO duplica).

NOTE: ``connections/.../telegram.py`` (sales_agent adapter) NO se
importa. Cero shared state. Distinto bot, distinto token, distinto
webhook.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Final

import httpx
import structlog

from src.core.config import settings
from src.shared.agent_observability.channels.format import escape_markdown_v2

_LOGGER = structlog.get_logger(__name__)

# Telegram Bot API limits (D-PI5-027)
# Reference: https://core.telegram.org/bots/faq#broadcasting-to-users
_GLOBAL_MAX_PER_SEC: Final[int] = 30
_TELEGRAM_API_BASE: Final[str] = "https://api.telegram.org/bot"
_HTTP_TIMEOUT_SECONDS: Final[float] = 10.0
_MAX_TEXT_CHARS: Final[int] = 4096
_MAX_RETRIES: Final[int] = 1


class CopilotTelegramBotError(RuntimeError):
    """Raised when bot fails to send after retry budget exhausted."""


class CopilotTelegramBot:
    """Outbound bot client. Singleton per process."""

    _global_semaphore: asyncio.Semaphore = asyncio.Semaphore(_GLOBAL_MAX_PER_SEC)
    _chat_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    def __init__(self, token: str | None = None) -> None:
        """Initialize bot with token from settings or override."""
        self._token = token or settings.COPILOT_TELEGRAM_BOT_TOKEN
        if not self._token:
            error_msg = "COPILOT_TELEGRAM_BOT_TOKEN not set in Settings"
            raise RuntimeError(error_msg)
        self._base_url = f"{_TELEGRAM_API_BASE}{self._token}"

    async def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "MarkdownV2",
        reply_markup: dict[str, Any] | None = None,
    ) -> None:
        """Send message with global + per-chat rate limiting + retry.

        Graceful degradation: log + skip on persistent failure (no
        infinite loop). Tessl ``graceful-degradation`` rule applied.
        """
        if parse_mode == "MarkdownV2":
            text = escape_markdown_v2(text)

        # Truncate if exceeds 4096 chars (Telegram limit)
        if len(text) > _MAX_TEXT_CHARS:
            text = text[: _MAX_TEXT_CHARS - 1] + "…"

        chat_lock = self._chat_locks[chat_id]
        async with self._global_semaphore, chat_lock:
            await self._send_with_retry(chat_id, text, parse_mode, reply_markup)
            # Sustain global rate (1/30 sec slot) — D-PI5-027
            await asyncio.sleep(1.0 / _GLOBAL_MAX_PER_SEC)

    async def _send_with_retry(
        self,
        chat_id: str,
        text: str,
        parse_mode: str,
        reply_markup: dict[str, Any] | None,
    ) -> None:
        """HTTP POST sendMessage with timeout + 1 retry on 429/5xx."""
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup

        url = f"{self._base_url}/sendMessage"

        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT_SECONDS) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        return
                    if resp.status_code in (429, 500, 502, 503, 504):
                        # Transient — retry once
                        _LOGGER.warning(
                            "copilot_telegram_send_message_transient_failure",
                            chat_id_prefix=_mask_chat_id(chat_id),
                            attempt=attempt,
                            status=resp.status_code,
                        )
                        await asyncio.sleep(0.5 * (2**attempt))
                        continue
                    # Non-retryable
                    _LOGGER.warning(
                        "copilot_telegram_send_message_failed",
                        chat_id_prefix=_mask_chat_id(chat_id),
                        attempt=attempt,
                        status=resp.status_code,
                        body=resp.text[:200],
                    )
                    return
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_exc = exc
                _LOGGER.warning(
                    "copilot_telegram_send_message_network_error",
                    chat_id_prefix=_mask_chat_id(chat_id),
                    attempt=attempt,
                    error=str(exc),
                )
                await asyncio.sleep(0.5 * (2**attempt))

        # Retry budget exhausted — graceful degradation: log only
        _LOGGER.error(
            "copilot_telegram_send_message_exhausted",
            chat_id_prefix=_mask_chat_id(chat_id),
            error=str(last_exc) if last_exc else "non-retryable",
        )


def _mask_chat_id(chat_id: str) -> str:
    """First 5 chars + '***' for log redaction."""
    if len(chat_id) <= 5:
        return "***"
    return f"{chat_id[:5]}***"
