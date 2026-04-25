"""Landing module — copilot provider entry point. F1 shim."""

from __future__ import annotations

from src.modules.landing.copilot_provider.provider import LandingCopilotProvider

provider: LandingCopilotProvider = LandingCopilotProvider()

__all__ = ("LandingCopilotProvider", "provider")
