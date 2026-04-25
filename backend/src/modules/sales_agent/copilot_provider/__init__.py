"""Sales agent module — copilot provider entry point. F1 shim."""

from __future__ import annotations

from src.modules.sales_agent.copilot_provider.provider import SalesAgentCopilotProvider

provider: SalesAgentCopilotProvider = SalesAgentCopilotProvider()

__all__ = ("SalesAgentCopilotProvider", "provider")
