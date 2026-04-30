"""SalesAgentObservabilityPort — read-only access for cross-module observability.

Used by ``copilot`` SuggestionProvider to compute pipeline heuristics
(leads, conversations, enrollments) WITHOUT taking a direct dependency
on ``sales_agent`` repositories.  Keeps the F1 ratchet
``copilot -> sales_agent`` at zero entries.

Tenant-scoped.  Sync (engine is sync).  Best-effort: implementations may
raise; callers (providers) catch and return ``[]``.

[COPILOT-SUGGESTIONS-ENGINE] -> docs/domains/copilot/suggestions-engine.md
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from datetime import datetime
    from uuid import UUID

    from sqlalchemy.orm import Session


class EnrollmentSummaryDTO(BaseModel):
    """Lightweight enrollment view for observability purposes (D-6).

    Mirror MINUS PII fields (no contact_id in clear, no payment_link_url).
    Only exposes internal IDs + status + timestamps.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str  # UUID stringified
    offer_id: str
    status: str  # EnrollmentStatus.value
    created_at_iso: str  # ISO 8601 UTC
    edition_id: str | None = None


class SalesAgentObservabilityPort(ABC):
    """Read-only sales pipeline observability for the suggestion engine."""

    @abstractmethod
    def count_leads_since(self, tenant_id: UUID, since: datetime) -> int:
        """Distinct contacts (user_id) with at least one message since ``since``."""
        ...

    @abstractmethod
    def count_active_conversations_since(self, tenant_id: UUID, since: datetime) -> int:
        """Distinct conversations with messages since ``since``."""
        ...

    @abstractmethod
    def list_enrollments_by_status(
        self,
        tenant_id: UUID,
        statuses: tuple[str, ...],
    ) -> list[EnrollmentSummaryDTO]:
        """Lightweight enrollments filtered by status values."""
        ...

    @abstractmethod
    def has_active_edition_for_offer(self, tenant_id: UUID, offer_id: UUID) -> bool:
        """True if the offer has at least one active (non-cancelled) edition."""
        ...


def create_sales_agent_observability_port(db: Session) -> SalesAgentObservabilityPort:
    """Create a SalesAgentObservabilityPort instance.

    Lazy-imports the concrete adapter from sales_agent module so callers
    (copilot suggestion providers) only depend on ``shared/links/ports``
    and the F1 ratchet ``copilot -> sales_agent`` stays at zero entries.
    """
    from src.modules.sales_agent.application.services.observability_adapter import (
        SalesAgentObservabilityAdapter,
    )

    return SalesAgentObservabilityAdapter(db)


__all__ = [
    "EnrollmentSummaryDTO",
    "SalesAgentObservabilityPort",
    "create_sales_agent_observability_port",
]
