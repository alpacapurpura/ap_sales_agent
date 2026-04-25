"""Social proof module — copilot provider entry point. F1 shim."""

from __future__ import annotations

from src.modules.social_proof.copilot_provider.provider import SocialProofCopilotProvider

provider: SocialProofCopilotProvider = SocialProofCopilotProvider()

__all__ = ("SocialProofCopilotProvider", "provider")
