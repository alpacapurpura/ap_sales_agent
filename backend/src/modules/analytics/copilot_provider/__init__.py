"""Analytics module — copilot provider entry point. F1 shim."""

from __future__ import annotations

from src.modules.analytics.copilot_provider.provider import AnalyticsCopilotProvider

provider: AnalyticsCopilotProvider = AnalyticsCopilotProvider()

__all__ = ("AnalyticsCopilotProvider", "provider")
