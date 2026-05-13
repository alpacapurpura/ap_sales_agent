"""TelegramChannelRouter — Telegram Bot API outbound dispatch.

Implements the ``ChannelRouter`` Protocol from PR-3.

Pre-send pipeline (ORDER MATTERS — D18/D19/compliance/rate-limit invariants):
  1. ``select_channel`` → confirm "telegram" in priority AND lead.telegram_id present.
  2. ``ComplianceService.check`` → if denied → raise ``ChannelComplianceBlocked``.
  3. ``OutboundRateLimiter.check`` → if denied → raise ``ChannelTenantRateExceeded``.
  4. ``IdempotencyService.with_dedupe`` (key = ``telegram-send:{task_id}``, ttl 24h)
     → if cached → return early with stored result (no HTTP call).
  5. ``CircuitBreaker.call(post_to_telegram)`` — if OPEN → raise ``CircuitBreakerOpenError``.
  6. Map httpx response → ``ChannelDispatchResult`` / raise channel error class.

httpx config (tessl__graceful-degradation iron rule):
  - ``httpx.Timeout(10.0, connect=5.0)`` — env ``TELEGRAM_API_TIMEOUT_SECONDS``.
  - ``retries=0`` — CB + ARQ own retry semantics.
  - Connection pool: module-level singleton ``AsyncClient`` reused across calls.

PR-5 PI-1 S2.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

import httpx
import structlog
from luana_core_campaigns.domain.channel_router import ChannelRouter, ChannelSendResult
from luana_core_campaigns.infrastructure.channels.errors import (
    ChannelComplianceBlocked,
    ChannelFatalError,
    ChannelRateLimitedError,
    ChannelRetryableError,
    ChannelTenantRateExceeded,
)
from luana_core_campaigns.infrastructure.channels.shared import (
    ChannelDispatchResult,
    format_message_for_tenant_locale,
)
from luana_core_campaigns.infrastructure.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
)
from luana_core_platform.links.ports.crm_repos import get_lead_telegram_id_async

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from uuid import UUID

    from luana_core_billing.application.rate_limiter import OutboundRateLimiter
    from luana_core_compliance.application.compliance_service import ComplianceService
    from luana_core_idempotency.application.service import IdempotencyService
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

_TELEGRAM_API_BASE = "https://api.telegram.org"

# Module-level singleton AsyncClient (lazy-init, closed on shutdown)
_HTTPX_CLIENT: httpx.AsyncClient | None = None


def _get_httpx_client(*, api_base: str | None = None) -> httpx.AsyncClient:
    """Return (or create) module-level singleton AsyncClient."""
    global _HTTPX_CLIENT  # noqa: PLW0603
    if _HTTPX_CLIENT is None or _HTTPX_CLIENT.is_closed:
        timeout_seconds = float(os.environ.get("TELEGRAM_API_TIMEOUT_SECONDS", "10"))
        _HTTPX_CLIENT = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_seconds, connect=5.0),
            headers={"User-Agent": "Nicolify-Campaigns/1.0"},
            base_url=api_base or _TELEGRAM_API_BASE,
        )
    return _HTTPX_CLIENT


async def close_httpx_client() -> None:
    """Close module-level singleton. Call from WorkerSettings.on_shutdown."""
    global _HTTPX_CLIENT  # noqa: PLW0603
    if _HTTPX_CLIENT is not None and not _HTTPX_CLIENT.is_closed:
        await _HTTPX_CLIENT.aclose()
        _HTTPX_CLIENT = None


class TelegramChannelRouter(ChannelRouter):
    """Telegram Bot API outbound dispatch — implements ``ChannelRouter`` Protocol.

    DI: all dependencies optional at construction; call sites inject them.
    For tests: pass explicit ``httpx_client`` to avoid module-level singleton.
    For production: singleton client reused; dependencies resolved at startup wiring.
    """

    def __init__(
        self,
        *,
        token_provider: Callable[[UUID], Awaitable[str]],
        compliance_service: ComplianceService | None = None,
        outbound_rate_limiter: OutboundRateLimiter | None = None,
        idempotency_service: IdempotencyService | None = None,
        circuit_breaker_factory: Callable[[str, UUID], CircuitBreaker] | None = None,
        httpx_client: httpx.AsyncClient | None = None,
        api_base: str = _TELEGRAM_API_BASE,
        session: AsyncSession | None = None,
    ) -> None:
        """Initialize TelegramChannelRouter.

        Args:
            token_provider: Async callable resolving bot token per tenant.
            compliance_service: Optional ComplianceService for opt-out / blacklist checks.
            outbound_rate_limiter: Optional OutboundRateLimiter.
            idempotency_service: Optional IdempotencyService for D18 dedup.
            circuit_breaker_factory: ``(channel, tenant_id) -> CircuitBreaker``.
            httpx_client: Explicit client for tests.
            api_base: Telegram Bot API base URL. Override for tests.
            session: Optional AsyncSession for CRM lead lookup (Sub-E wire).
                When provided, ``_resolve_telegram_id`` performs a real DB lookup.
                When None (default), falls back to graceful None (channel skipped).
        """
        self._token_provider = token_provider
        self._compliance_service = compliance_service
        self._rate_limiter = outbound_rate_limiter
        self._idempotency_service = idempotency_service
        self._cb_factory = circuit_breaker_factory
        self._explicit_client = httpx_client
        self._api_base = api_base
        self._session = session

    # ── ChannelRouter Protocol impl ──────────────────────────────────────────

    async def select_channel(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        priority: list[str],
    ) -> str | None:
        """Return ``"telegram"`` if priority includes it AND lead has telegram_id.

        Returns None if "telegram" not in priority or lead has no telegram_id
        (caller marks task SKIPPED).
        """
        if "telegram" not in priority:
            return None

        telegram_id = await self._resolve_telegram_id(lead_id, tenant_id)
        if not telegram_id:
            logger.info(
                "telegram_channel_select_no_id",
                lead_id=str(lead_id),
                tenant_id=str(tenant_id),
            )
            return None

        return "telegram"

    async def send(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        channel: str,
        content: dict[str, Any],
        *,
        idempotency_key: str,
    ) -> ChannelSendResult:
        """Send a single Telegram message.

        ``content`` schema::

            {
                "chat_id": str,          # Telegram chat id (= lead.telegram_id)
                "text": str,             # message body — locale-formatted before send
                "parse_mode": str|None,  # "HTML" | "MarkdownV2" | None
                "disable_notification": bool,
            }

        Pre-send pipeline runs in strict ORDER (compliance → rate-limit → dedup → CB → HTTP).

        Raises:
            ChannelComplianceBlocked: ComplianceService denied send.
            ChannelTenantRateExceeded: OutboundRateLimiter cap reached.
            CircuitBreakerOpenError: CB is OPEN for (telegram, tenant_id).
            ChannelRateLimitedError: Telegram returned HTTP 429.
            ChannelFatalError: Telegram returned 4xx (non-429).
            ChannelRetryableError: Telegram returned 5xx or network error.
        """
        # 1. Apply tenant locale formatting to message text
        raw_text = content.get("text", "")
        formatted_text = await format_message_for_tenant_locale(
            tenant_id=tenant_id,
            template_text=raw_text,
            placeholders=content.get("placeholders"),
        )

        # 2. Compliance gate — MUST run before any send
        if self._compliance_service is not None:
            chat_id = str(content.get("chat_id", ""))
            compliance_result = await self._compliance_service.check(
                tenant_id=tenant_id,
                lead_id=lead_id,
                channel="telegram",
                identifier=chat_id,
                campaign_id=None,
            )
            if not compliance_result.allowed:
                logger.info(
                    "telegram_send_compliance_blocked",
                    tenant_id=str(tenant_id),
                    lead_id=str(lead_id),
                    failed_policy=compliance_result.failed_policy,
                    reason=compliance_result.reason,
                )
                msg = f"Compliance blocked: {compliance_result.failed_policy} — {compliance_result.reason}"
                raise ChannelComplianceBlocked(msg)

        # 3. Tenant rate limiter gate
        if self._rate_limiter is not None:
            allowed = await self._rate_limiter.check(tenant_id)
            if not allowed:
                logger.info(
                    "telegram_send_rate_exceeded",
                    tenant_id=str(tenant_id),
                    lead_id=str(lead_id),
                )
                msg = f"Tenant outbound rate exceeded for tenant={tenant_id}"
                raise ChannelTenantRateExceeded(msg)

        # 4 + 5 + 6. Idempotency dedup → CB-protected HTTP POST
        result = await self._dispatch_with_dedup(
            tenant_id=tenant_id,
            lead_id=lead_id,
            content=content,
            formatted_text=formatted_text,
            idempotency_key=idempotency_key,
        )

        return ChannelSendResult(
            success=result.success,
            channel="telegram",
            external_message_id=result.external_message_id,
            error_code=result.error_code,
            error_message=result.error_message,
        )

    # ── Internal helpers ─────────────────────────────────────────────────────

    async def _dispatch_with_dedup(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        content: dict[str, Any],
        formatted_text: str,
        idempotency_key: str,
    ) -> ChannelDispatchResult:
        """Wrap HTTP dispatch with idempotency dedup and circuit breaker."""
        if self._idempotency_service is not None:
            from luana_core_idempotency.domain.key import IdempotencyKey

            idem_key = IdempotencyKey(
                namespace="telegram:send",
                key=idempotency_key,
                ttl_seconds=86400,
            )

            # Capture dispatch result for idempotency cache
            dispatch_holder: list[ChannelDispatchResult] = []

            async def _do_send() -> dict[str, Any]:
                dispatch = await self._dispatch_with_cb(
                    tenant_id=tenant_id,
                    content=content,
                    formatted_text=formatted_text,
                )
                dispatch_holder.append(dispatch)
                return {
                    "id": idempotency_key,
                    "status": "sent" if dispatch.success else "fatal",
                    "external_id": dispatch.external_message_id or "",
                }

            cached_or_new = await self._idempotency_service.with_dedupe(idem_key, _do_send)

            # If we just executed (not cached), return the actual dispatch result
            if dispatch_holder:
                return dispatch_holder[0]

            # Reconstruct from cached projection
            return ChannelDispatchResult(
                success=cached_or_new.get("status") == "sent",
                channel="telegram",
                external_message_id=cached_or_new.get("external_id") or None,
                error_code=None if cached_or_new.get("status") == "sent" else "dedup_cached",
                error_message=None,
            )

        return await self._dispatch_with_cb(
            tenant_id=tenant_id,
            content=content,
            formatted_text=formatted_text,
        )

    async def _dispatch_with_cb(
        self,
        *,
        tenant_id: UUID,
        content: dict[str, Any],
        formatted_text: str,
    ) -> ChannelDispatchResult:
        """Execute HTTP POST under circuit breaker protection."""
        cb = self._get_circuit_breaker(tenant_id)

        async def _post() -> ChannelDispatchResult:
            return await self._post_to_telegram(
                tenant_id=tenant_id,
                content=content,
                formatted_text=formatted_text,
            )

        return await cb.call(_post)

    async def _post_to_telegram(
        self,
        *,
        tenant_id: UUID,
        content: dict[str, Any],
        formatted_text: str,
    ) -> ChannelDispatchResult:
        """Perform the actual HTTP POST to Telegram Bot API.

        Raises channel error classes based on HTTP status.
        Maps Telegram success response → ChannelDispatchResult.
        """
        bot_token = await self._token_provider(tenant_id)
        client = self._explicit_client or _get_httpx_client(api_base=self._api_base)

        payload: dict[str, Any] = {
            "chat_id": content.get("chat_id", ""),
            "text": formatted_text,
        }
        if content.get("parse_mode"):
            payload["parse_mode"] = content["parse_mode"]
        if content.get("disable_notification") is not None:
            payload["disable_notification"] = content["disable_notification"]

        url = f"/bot{bot_token}/sendMessage"

        try:
            response = await client.post(url, json=payload)
        except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as exc:
            logger.warning(
                "telegram_http_network_error",
                tenant_id=str(tenant_id),
                error=str(exc),
            )
            msg = f"Telegram network error: {exc}"
            raise ChannelRetryableError(msg) from exc

        status = response.status_code

        if status == 200:
            body = response.json()
            msg_id: str | None = None
            if body.get("ok") and "result" in body:
                msg_id = str(body["result"].get("message_id", ""))
            logger.info(
                "telegram_send_success",
                tenant_id=str(tenant_id),
                message_id=msg_id,
            )
            return ChannelDispatchResult(
                success=True,
                channel="telegram",
                external_message_id=msg_id,
            )

        if status == 429:
            retry_after: float | None = None
            try:
                body_429 = response.json()
                retry_after = float(body_429.get("parameters", {}).get("retry_after", 0) or 0) or None
            except Exception:  # noqa: BLE001 — best-effort parse
                pass
            logger.warning(
                "telegram_rate_limited",
                tenant_id=str(tenant_id),
                retry_after=retry_after,
            )
            msg_429 = f"Telegram 429 rate limited for tenant={tenant_id}"
            raise ChannelRateLimitedError(msg_429, retry_after_seconds=retry_after)

        if 400 <= status < 500:
            error_msg = f"Telegram HTTP {status}"
            try:
                body_4xx = response.json()
                error_msg = body_4xx.get("description", error_msg)
            except Exception:  # noqa: BLE001 — best-effort parse
                pass
            logger.warning(
                "telegram_send_fatal",
                tenant_id=str(tenant_id),
                status=status,
                error=error_msg,
            )
            msg_4xx = f"Telegram fatal {status}: {error_msg}"
            raise ChannelFatalError(msg_4xx)

        # 5xx and anything else → retryable
        logger.warning(
            "telegram_send_server_error",
            tenant_id=str(tenant_id),
            status=status,
        )
        msg_5xx = f"Telegram server error HTTP {status}"
        raise ChannelRetryableError(msg_5xx)

    def _get_circuit_breaker(self, tenant_id: UUID) -> CircuitBreaker:
        """Return CB for (telegram, tenant_id). Factory or default config."""
        if self._cb_factory is not None:
            return self._cb_factory("telegram", tenant_id)

        # Default: no Redis (soft-fail open) — production injects redis_client
        return CircuitBreaker(
            channel="telegram",
            tenant_id=tenant_id,
            redis_client=None,
            config=CircuitBreakerConfig(),
        )

    async def _resolve_telegram_id(self, lead_id: UUID, tenant_id: UUID) -> str | None:
        """Resolve telegram_id for a lead via CRM port.

        Sub-E wire (PR-7): performs real DB lookup when ``self._session`` is set.
        Callers that already have ``chat_id`` in ``content["chat_id"]`` bypass this
        and send directly without calling ``_resolve_telegram_id``.

        Returns:
            Telegram chat ID string on hit, None on miss or when session is absent.
        """
        if self._session is None:
            logger.debug(
                "telegram_resolve_no_session",
                lead_id=str(lead_id),
                tenant_id=str(tenant_id),
            )
            return None

        try:
            telegram_id = await get_lead_telegram_id_async(
                self._session,
                tenant_id,
                lead_id,
            )
            if telegram_id:
                logger.debug(
                    "telegram_resolve_hit",
                    lead_id=str(lead_id),
                    tenant_id=str(tenant_id),
                )
            else:
                logger.info(
                    "telegram_resolve_miss",
                    lead_id=str(lead_id),
                    tenant_id=str(tenant_id),
                )
            return telegram_id
        except Exception:  # noqa: BLE001 — graceful degradation: never abort channel
            logger.warning(
                "telegram_resolve_error",
                lead_id=str(lead_id),
                tenant_id=str(tenant_id),
            )
            return None
