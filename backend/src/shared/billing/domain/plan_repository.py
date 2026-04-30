"""PlanRepository port (ABC) — shared/billing domain.

Global catalog (no tenant_id). Implementations in infrastructure/.

PR-2 / PI-1 S0.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.shared.billing.domain.plan import PlanConfig


class PlanRepository(ABC):
    """Port for plan_config catalog access."""

    @abstractmethod
    async def get_by_id(self, plan_id: str) -> PlanConfig | None:
        """Return plan by plan_id, or None if not found."""
        ...

    @abstractmethod
    async def get_default(self) -> PlanConfig | None:
        """Return the plan with is_default=TRUE, or None.

        PM Q6: partial unique index guarantees at most one row returns.
        """
        ...

    @abstractmethod
    async def list_active(self) -> list[PlanConfig]:
        """Return all active plans (is_active=True)."""
        ...

    @abstractmethod
    async def upsert(self, plan: PlanConfig) -> PlanConfig:
        """Create or update a plan row. Returns the stored VO."""
        ...
