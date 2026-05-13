"""Analytics module — copilot provider entry point. F1 shim."""

from __future__ import annotations

from luana_core_analytics_engine.copilot_provider.provider import AnalyticsCopilotProvider

provider: AnalyticsCopilotProvider = AnalyticsCopilotProvider()

__all__ = ("AnalyticsCopilotProvider", "provider")
