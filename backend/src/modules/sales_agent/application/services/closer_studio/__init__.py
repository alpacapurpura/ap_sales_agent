"""Closer Studio service split — S11B Strangler Fig step 5.

The legacy :class:`CloserStudioService` god class was split along the
Query / Command / Kpi axis (research: lightweight CQRS for FastAPI 2026
— same DB, separate read & write services with flat DTOs).

# [SALES-AGENT-CLOSER-STUDIO-SPLIT-S11B] -> docs/domains/sales-agent/redesign-2026-04/phases/
# S11-shared-lift-orchestrator-decomp.md
"""

from src.modules.sales_agent.application.services.closer_studio.command_service import (
    ConversationCommandService,
)
from src.modules.sales_agent.application.services.closer_studio.kpi_service import (
    KpiService,
)
from src.modules.sales_agent.application.services.closer_studio.query_service import (
    ConversationQueryService,
)

__all__ = [
    "ConversationCommandService",
    "ConversationQueryService",
    "KpiService",
]
