"""OptInRepository port (ABC) — PM Q2 DB-backed.

No longer a stub. Reads lead_opt_ins table.
Every method requires tenant_id (tenant isolation invariant).
Soft-delete N/A — opt-out tracked via opted_out_at timestamp.

PR-2 / PI-1 S0.
"""

from __future__ import annotations

import datetime as dt
from abc import ABC, abstractmethod
from uuid import UUID

from src.shared.compliance.domain.lead_opt_in import LeadOptIn, OptInSource


class OptInRepository(ABC):
    """Port for lead_opt_ins table access.

    tenant_id is mandatory in all methods (architectural invariant).
    """

    @abstractmethod
    async def has_active_opt_in(self, tenant_id: UUID, lead_id: UUID, channel: str) -> bool:
        """Return True iff row exists with opted_in_at NOT NULL AND opted_out_at IS NULL."""
        ...

    @abstractmethod
    async def get(self, tenant_id: UUID, lead_id: UUID, channel: str) -> LeadOptIn | None:
        """Return opt-in record or None. tenant_id mandatory."""
        ...

    @abstractmethod
    async def upsert(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        channel: str,
        opted_in_at: dt.datetime | None,
        opted_out_at: dt.datetime | None,
        source: OptInSource,
        evidence: dict,
    ) -> LeadOptIn:
        """ON CONFLICT (tenant_id, lead_id, channel) DO UPDATE — idempotent."""
        ...

    @abstractmethod
    async def list_by_tenant(
        self,
        tenant_id: UUID,
        channel: str | None = None,
        active_only: bool = True,
    ) -> list[LeadOptIn]:
        """Return opt-in records for tenant.

        active_only=True: filter opted_in_at NOT NULL AND opted_out_at IS NULL.
        """
        ...
