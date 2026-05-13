"""Connections module — copilot provider entry point. F1 shim."""

from __future__ import annotations

from luana_core_connections.copilot_provider.provider import ConnectionsCopilotProvider

provider: ConnectionsCopilotProvider = ConnectionsCopilotProvider()

__all__ = ("ConnectionsCopilotProvider", "provider")
