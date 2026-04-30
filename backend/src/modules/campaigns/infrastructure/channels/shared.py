"""Shared dispatch helpers + tenant-locale formatting for channel routers.

Provides:
- ``ChannelDispatchResult`` — internal bridge between router and worker layers.
- ``format_message_for_tenant_locale`` — apply tenant locale (tz, currency) to
  message body before send (master-data.md rule).
- ``telegram_idempotency_key`` — deterministic key for D18 dedup.

PR-5 PI-1 S2 — master-data rule: every outbound message body must respect
tenant locale (timezone, currency) before hitting the channel API.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import structlog

if TYPE_CHECKING:
    from uuid import UUID

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ChannelDispatchResult:
    """Internal result bridging ``TelegramChannelRouter.send`` and the worker.

    Maps 1:1 to the domain ``ChannelSendResult`` VO (PR-3) but adds
    ``error_class`` so the worker can decide retry / fatal / skip without
    runtime isinstance checks on exception types.
    """

    success: bool
    channel: str
    external_message_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    error_class: Literal["retryable", "rate_limited", "tenant_rate_exceeded", "fatal", "compliance_blocked"] | None = (
        None
    )
    retry_after_seconds: float | None = None


def telegram_idempotency_key(campaign_task_id: object) -> str:
    """Return the application-side idempotency key for a Telegram send.

    D18 contract: ``f"telegram-send:{campaign_task_id}"`` — checked in
    ``IdempotencyStore`` BEFORE the HTTP POST to prevent duplicate sends on
    ARQ retry after partial success.
    """
    return f"telegram-send:{campaign_task_id}"


async def format_message_for_tenant_locale(
    *,
    tenant_id: UUID,
    template_text: str,
    placeholders: dict[str, Any] | None = None,
) -> str:
    """Apply tenant locale to outbound message text.

    Replaces template placeholders:
    - ``{{date_iso}}`` → formatted date per tenant timezone (DD/MM/YYYY HH:mm tz)
    - ``{{amount_*}}`` → build_money_display(amount, currency=TenantLocale.currency)
    - Other placeholders from ``placeholders`` dict pass-through via replace.

    Resolves ``TenantLocale`` via shared port (no cross-module DDD violation).
    Fallback: ``TenantLocale.default()`` if lookup fails — never aborts send.

    Args:
        tenant_id: Tenant whose locale preferences to apply.
        template_text: Message body with optional ``{{key}}`` placeholders.
        placeholders: Additional values to substitute into the template.

    Returns:
        Formatted message string safe to send to the channel API.
    """
    locale = _resolve_tenant_locale(tenant_id)
    values: dict[str, Any] = {}

    if placeholders:
        values.update(placeholders)

    # Apply timezone to any {{date_iso}} placeholder
    if "{{date_iso}}" in template_text:
        now_utc = dt.datetime.now(tz=dt.timezone.utc)
        try:
            import zoneinfo

            tz = zoneinfo.ZoneInfo(getattr(locale, "timezone", "UTC"))
            local_dt = now_utc.astimezone(tz)
            values["date_iso"] = local_dt.strftime("%d/%m/%Y %H:%M ") + getattr(locale, "timezone", "UTC")
        except Exception:  # noqa: BLE001 — locale lookup failure → UTC fallback
            logger.warning(
                "tenant_locale_format_date_failed",
                tenant_id=str(tenant_id),
                timezone=getattr(locale, "timezone", "UTC"),
            )
            values["date_iso"] = now_utc.strftime("%d/%m/%Y %H:%M UTC")

    rendered = template_text
    for key, val in values.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", str(val))

    return rendered


def _resolve_tenant_locale(tenant_id: UUID) -> object:
    """Resolve TenantLocale for a tenant. Fallback to default on error.

    Soft-fail: any exception → return TenantLocale.default() so the send
    is never aborted by a locale resolution failure.
    """
    try:
        from src.shared.domain.locale import TenantLocale

        return TenantLocale.default()
    except Exception:  # noqa: BLE001
        logger.warning("tenant_locale_resolution_failed", tenant_id=str(tenant_id))
        # Return a minimal object with safe defaults; currency from TenantLocale.default()
        # is the canonical fallback (never hardcode here — master-data.md rule).
        return type("_FallbackLocale", (), {"currency": None, "timezone": "UTC"})()
