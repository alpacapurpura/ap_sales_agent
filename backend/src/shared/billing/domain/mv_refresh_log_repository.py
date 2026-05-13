"""MVRefreshLogRepository port (ABC) — PM Q4.

Global table — NO tenant_id (operational infra).

PR-2 / PI-1 S0.
"""

from __future__ import annotations

import datetime as dt
from abc import ABC, abstractmethod

from luana_core_billing.domain.mv_refresh_log import MVRefreshLog, RefreshStatus


class MVRefreshLogRepository(ABC):
    """Port for mv_refresh_log table access. Global table, no tenant_id."""

    @abstractmethod
    async def record_refresh(
        self,
        mv_name: str,
        refresh_duration_ms: int | None,
        rows_affected: int | None,
        status: RefreshStatus,
    ) -> MVRefreshLog:
        """Insert a new refresh log row. Returns the stored VO."""
        ...

    @abstractmethod
    async def get_last_refresh(self, mv_name: str) -> MVRefreshLog | None:
        """Return most recent row for mv_name (ORDER BY refreshed_at DESC LIMIT 1).

        Used by BudgetGuard._is_mv_stale() freshness probe.
        Returns None if no refresh has ever been recorded.
        """
        ...

    @abstractmethod
    async def delete_older_than(self, cutoff: dt.datetime) -> int:
        """Delete rows older than cutoff. Returns count deleted.

        Called by retention worker (90-day TTL).
        """
        ...
