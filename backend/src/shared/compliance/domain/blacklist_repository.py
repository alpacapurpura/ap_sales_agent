"""ChannelBlacklistRepository port (ABC) — compliance domain.

PR-2 / PI-1 S0.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from src.shared.compliance.domain.blacklist_entry import ChannelBlacklistEntry


class ChannelBlacklistRepository(ABC):
    """Port for channel_blacklist table access. All methods tenant-scoped."""

    @abstractmethod
    async def is_blacklisted(self, tenant_id: UUID, channel: str, identifier: str) -> bool:
        """Return True iff active blacklist entry exists for (tenant, channel, identifier).

        Filters: deleted_at IS NULL. tenant_id is mandatory.
        """
        ...

    @abstractmethod
    async def list_by_tenant(
        self,
        tenant_id: UUID,
        channel: str | None = None,
    ) -> list[ChannelBlacklistEntry]:
        """Return all active blacklist entries for a tenant.

        If channel is provided, filter to that channel only.
        """
        ...

    @abstractmethod
    async def upsert(self, entry: ChannelBlacklistEntry) -> ChannelBlacklistEntry:
        """Create or update a blacklist entry.

        ON CONFLICT (tenant_id, channel, identifier) DO UPDATE — idempotent.
        """
        ...

    @abstractmethod
    async def soft_delete(self, tenant_id: UUID, entry_id: UUID) -> None:
        """Soft-delete entry by setting deleted_at = now()."""
        ...
