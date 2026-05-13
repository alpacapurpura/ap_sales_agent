"""CRM module — copilot provider entry point. F1 shim."""

from __future__ import annotations

from luana_core_crm.copilot_provider.provider import CrmCopilotProvider

provider: CrmCopilotProvider = CrmCopilotProvider()

__all__ = ("CrmCopilotProvider", "provider")
