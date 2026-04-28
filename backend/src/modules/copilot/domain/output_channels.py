"""Channel formatter registry — F7 (back-compat shim → S5 shared SSoT).

Post-S5 (2026-04-28) la implementación canónica vive en
``src/shared/agent_observability/channels/format.py`` para que sales_agent +
copilot + agentes futuros la consuman desde el mismo registry. Este módulo
mantiene los símbolos públicos como re-exports finos para no romper consumers
de copilot. NO agregar lógica nueva acá; modificar el SSoT shared.

# [COPILOT-CHANNEL-FORMATTER-F7] -> docs/domains/copilot/redesign-2026-04/phases/F7-channel-formatter.md
# [SALES-AGENT-CHANNEL-REGISTRY-S5] -> docs/domains/sales-agent/redesign-2026-04/phases/S5-channel-registry.md
"""

from __future__ import annotations

from src.shared.agent_observability.channels.format import (
    CHANNEL_FORMATS,
    SUPPORTED_CHANNELS,
    ChannelFormat,
    get_channel_format,
    register_channel,
    reset_registry_for_tests,
)

__all__ = (
    "CHANNEL_FORMATS",
    "SUPPORTED_CHANNELS",
    "ChannelFormat",
    "get_channel_format",
    "register_channel",
    "reset_registry_for_tests",
)
