"""Blacklist Policy — check channel_blacklist for (tenant, channel, identifier).

FAIL: active blacklist entry found (deleted_at IS NULL).
PASS: no entry or soft-deleted entry.

PR-2 / PI-1 S0.
"""

from __future__ import annotations

from uuid import UUID

import structlog
from luana_core_compliance.domain.blacklist_repository import ChannelBlacklistRepository
from luana_core_compliance.domain.check_result import CheckResult

logger = structlog.get_logger(__name__)


class BlacklistPolicy:
    """All channels: verify identifier not in channel_blacklist.

    Identifier normalization is caller's responsibility.
    """

    name: str = "blacklist"

    def __init__(self, blacklist_repo: ChannelBlacklistRepository) -> None:
        """Bind to ChannelBlacklistRepository implementation."""
        self._blacklist_repo = blacklist_repo

    async def evaluate(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        channel: str,
        identifier: str,
        campaign_id: UUID | None = None,
    ) -> CheckResult:
        """Evaluate blacklist policy."""
        is_blacklisted = await self._blacklist_repo.is_blacklisted(
            tenant_id=tenant_id, channel=channel, identifier=identifier
        )

        if is_blacklisted:
            # Get entry detail for evidence
            entries = await self._blacklist_repo.list_by_tenant(tenant_id=tenant_id, channel=channel)
            matched = next((e for e in entries if e.identifier == identifier), None)
            return CheckResult(
                allowed=False,
                failed_policy=self.name,
                reason="El contacto está en lista de exclusión para este canal",
                evidence={
                    "channel": channel,
                    "identifier": identifier[:4] + "***",  # partial mask for PII
                    "blacklist_entry_id": str(matched.id) if matched else None,
                    "reason": matched.reason if matched else None,
                },
            )

        return CheckResult(allowed=True)
