"""Shared channel-format registry — cross-agent (S5).

Single source of truth para metadata de canales output (WhatsApp, Telegram,
Instagram DM, SMS, voice, email, chat). Migrado desde
``src/modules/copilot/domain/output_channels.py`` en S5 — copilot mantiene
shim back-compat hasta migración completa de consumers.

Subpaquetes:

* :mod:`format` — ``ChannelFormat`` dataclass + registry (mutable via
  ``register_channel``) + ``get_channel_format`` lookup with fallback +
  ``escape_markdown_v2`` Telegram helper.
* :mod:`format_for_channel` — pure post-processor + LangChain ``@tool``
  wrapper. Strip markdown / emoji / truncate per spec.
* :mod:`intent_detector` — regex-based ``detect_channel_intent`` for "mándame
  por WhatsApp" pre-detection.

Reference: `docs/domains/sales-agent/redesign-2026-04/phases/S5-channel-registry.md`.
"""

from luana_core_channels.format import (
    CHANNEL_FORMATS,
    SUPPORTED_CHANNELS,
    ChannelFormat,
    escape_markdown_v2,
    get_channel_format,
    register_channel,
    reset_registry_for_tests,
)
from luana_core_channels.format_for_channel import (
    format_for_channel_impl,
)
from luana_core_channels.intent_detector import (
    ChannelIntent,
    detect_channel_in_user_msg,
    detect_channel_intent,
)

__all__ = (
    "CHANNEL_FORMATS",
    "SUPPORTED_CHANNELS",
    "ChannelFormat",
    "ChannelIntent",
    "detect_channel_in_user_msg",
    "detect_channel_intent",
    "escape_markdown_v2",
    "format_for_channel_impl",
    "get_channel_format",
    "register_channel",
    "reset_registry_for_tests",
)
