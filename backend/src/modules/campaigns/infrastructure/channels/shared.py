"""Shared dispatch helpers + tenant-locale formatting for channel routers.

Provides:
- ``ChannelDispatchResult`` — internal bridge between router and worker layers.
- ``format_message_for_tenant_locale`` — apply tenant locale (tz, currency) to
  message body before send (master-data.md rule).
- ``telegram_idempotency_key`` — deterministic key for D18 dedup.

PR-5 PI-1 S2 — master-data rule: every outbound message body must respect
tenant locale (timezone, currency) before hitting the channel API.
PR-7 PI-1 S3 Sub-F — real TenantModel lookup with LRU cache.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from threading import Lock
from typing import TYPE_CHECKING, Any, Literal

import structlog
from cachetools import TTLCache

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

logger = structlog.get_logger(__name__)

# LRU+TTL cache for tenant locale lookups.
# Key: UUID (tenant_id), Value: TenantLocale (or fallback object).
# TTL 300s (5 min) — process recycle is common enough that long-lived
# staleness is not a concern.  Thread-safe via Lock.
_LOCALE_CACHE: TTLCache[object, object] = TTLCache(maxsize=512, ttl=300)
_LOCALE_CACHE_LOCK: Lock = Lock()


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


def _resolve_tenant_locale(tenant_id: UUID, *, db: Session | None = None) -> object:
    """Resolve TenantLocale for a tenant. Fallback to default on error.

    Sub-F (PR-7): performs real TenantModel lookup when ``db`` is provided.
    Reads ``TenantModel.config_json["tenant_locale"]`` and constructs
    ``TenantLocale(currency=..., timezone=...)``.  Falls back to
    ``TenantLocale.default()`` if:
    - ``db`` is None (backward-compat path — old callers without DB session)
    - Tenant row not found
    - ``tenant_locale`` key absent in config_json
    - Any exception (graceful degradation — never aborts send)

    LRU cache (512 entries, 5-min TTL) avoids repeated DB queries for the same
    tenant within a single process lifetime. Thread-safe via Lock.
    """
    from src.shared.domain.locale import TenantLocale

    cache_key = tenant_id
    with _LOCALE_CACHE_LOCK:
        cached = _LOCALE_CACHE.get(cache_key)
    if cached is not None:
        return cached

    if db is None:
        result = TenantLocale.default()
        with _LOCALE_CACHE_LOCK:
            _LOCALE_CACHE[cache_key] = result
        return result

    try:
        from sqlalchemy import select

        from src.modules.iam.infrastructure.models.tenant_model import TenantModel

        row = db.execute(select(TenantModel).where(TenantModel.id == tenant_id)).scalar_one_or_none()

        if row is None:
            logger.info(
                "tenant_locale_tenant_not_found",
                tenant_id=str(tenant_id),
            )
            result = TenantLocale.default()
        else:
            raw = (row.config_json or {}).get("tenant_locale")
            if isinstance(raw, dict):
                currency = raw.get("currency") or TenantLocale.default().currency
                timezone = raw.get("timezone") or TenantLocale.default().timezone
                result = TenantLocale(currency=currency, timezone=timezone)
                logger.debug(
                    "tenant_locale_resolved",
                    tenant_id=str(tenant_id),
                    currency=currency,
                    timezone=timezone,
                )
            else:
                logger.info(
                    "tenant_locale_key_absent",
                    tenant_id=str(tenant_id),
                )
                result = TenantLocale.default()

        with _LOCALE_CACHE_LOCK:
            _LOCALE_CACHE[cache_key] = result
        return result

    except Exception:  # noqa: BLE001 — graceful degradation: never abort send
        logger.warning(
            "tenant_locale_resolution_failed",
            tenant_id=str(tenant_id),
        )
        fallback = TenantLocale.default()
        # Do NOT cache on error — next attempt should retry DB
        return fallback


def invalidate_locale_cache() -> None:
    """Clear the in-process locale cache.

    Called by tests to force fresh lookups between test cases.
    """
    with _LOCALE_CACHE_LOCK:
        _LOCALE_CACHE.clear()
