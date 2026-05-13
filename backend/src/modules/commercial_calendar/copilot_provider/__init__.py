"""Commercial calendar module — copilot provider entry point. F1 shim."""

from __future__ import annotations

from luana_core_commercial_calendar.copilot_provider.provider import (
    CommercialCalendarCopilotProvider,
)

provider: CommercialCalendarCopilotProvider = CommercialCalendarCopilotProvider()

__all__ = ("CommercialCalendarCopilotProvider", "provider")
