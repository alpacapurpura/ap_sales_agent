"""Campaign channel router infrastructure.

Re-exports public symbols for consumer convenience.

PR-5 PI-1 S2.
"""

from __future__ import annotations

from luana_core_campaigns.infrastructure.channels.errors import (
    ChannelComplianceBlocked,
    ChannelError,
    ChannelFatalError,
    ChannelRateLimitedError,
    ChannelRetryableError,
    ChannelTenantRateExceeded,
)
from luana_core_campaigns.infrastructure.channels.registry import (
    ChannelRouterRegistry,
    channel_router_registry,
    register_default_channels,
)
from luana_core_campaigns.infrastructure.channels.shared import (
    ChannelDispatchResult,
    format_message_for_tenant_locale,
    telegram_idempotency_key,
)
from luana_core_campaigns.infrastructure.channels.telegram import (
    TelegramChannelRouter,
    close_httpx_client,
)

__all__ = [
    "ChannelComplianceBlocked",
    "ChannelDispatchResult",
    "ChannelError",
    "ChannelFatalError",
    "ChannelRateLimitedError",
    "ChannelRetryableError",
    "ChannelRouterRegistry",
    "ChannelTenantRateExceeded",
    "TelegramChannelRouter",
    "channel_router_registry",
    "close_httpx_client",
    "format_message_for_tenant_locale",
    "register_default_channels",
    "telegram_idempotency_key",
]
