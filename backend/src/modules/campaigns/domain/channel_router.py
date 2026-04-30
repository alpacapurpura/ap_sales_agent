"""ChannelRouter domain port and ChannelSendResult value object.

Pure interface — no impl in PR-3.
Implementations live in S2 (Telegram first, then WhatsApp + Email + IG DM PI-2/3).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from uuid import UUID


@dataclass(frozen=True, slots=True)
class ChannelSendResult:
    """Result of a single outbound channel send.

    Service consumers update CampaignTask based on this result.
    """

    success: bool
    channel: str
    external_message_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None


@runtime_checkable
class ChannelRouter(Protocol):
    """Domain port for outbound channel routing and sending.

    Pure interface — no impl in PR-3.
    Impl lives in S2 (Telegram first, then WhatsApp + Email + IG DM PI-2/3).
    Consumers: CampaignExecutionWorker (S2), OutboundOrchestrator (S3).

    Tenant isolation: all impls MUST validate tenant_id; the lead's tenant_id
    must match the campaign's tenant_id (service layer PR-4 enforces).

    Idempotency: idempotency_key MANDATORY — adapter dedupes external sends.
    """

    async def select_channel(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        priority: list[str],
    ) -> str | None:
        """Pick the first available channel from priority for this lead.

        Returns None if no priority channel available for the lead (skip/fail task).
        """
        ...

    async def send(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        channel: str,
        content: dict,
        *,
        idempotency_key: str,
    ) -> ChannelSendResult:
        """Send a single message via the selected channel.

        Adapter MUST:
        - Apply idempotency_key dedup (use shared/idempotency/ decorator if external HTTP).
        - Call ComplianceService.check before send (S2 wiring).
        - Call OutboundRateLimiter.check before send (S2 wiring).
        - Apply tenant locale formatting (master-data.md).
        """
        ...
