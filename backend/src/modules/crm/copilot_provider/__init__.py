"""CRM module — copilot provider entry point. F1 shim."""

from __future__ import annotations

from src.modules.crm.copilot_provider.provider import CrmCopilotProvider

provider: CrmCopilotProvider = CrmCopilotProvider()

__all__ = ("CrmCopilotProvider", "provider")
