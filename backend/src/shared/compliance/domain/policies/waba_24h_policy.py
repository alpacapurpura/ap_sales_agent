"""WABA 24h Policy — WhatsApp Business API 24-hour message window.

PASS: last inbound user message < 24h ago (within window).
FAIL: no inbound message within 24h or non-WhatsApp channel.

PR-2 / PI-1 S0.
"""

from __future__ import annotations

import datetime as dt
from typing import Any
from uuid import UUID

import structlog
from luana_core_compliance.domain.check_result import CheckResult

logger = structlog.get_logger(__name__)


class WABA24hPolicy:
    """WhatsApp-only: verify last inbound user message within 24h window.

    Only evaluates for channel == "whatsapp". Other channels pass immediately.
    Queries messages table: role='user' AND created_at > now() - 24h.
    """

    name: str = "waba_24h"

    def __init__(self, messages_reader: Any) -> None:
        """Bind to messages reader (duck-typed async callable).

        messages_reader.get_last_inbound_at(tenant_id, lead_id) -> dt.datetime | None
        """
        self._messages_reader = messages_reader

    async def evaluate(
        self,
        *,
        tenant_id: UUID,
        lead_id: UUID,
        channel: str,
        identifier: str,
        campaign_id: UUID | None = None,
    ) -> CheckResult:
        """Evaluate WABA 24h policy."""
        if channel != "whatsapp":
            # Non-WhatsApp channels are not subject to WABA 24h rule
            return CheckResult(allowed=True)

        last_inbound_at = await self._messages_reader.get_last_inbound_at(tenant_id=tenant_id, lead_id=lead_id)

        if last_inbound_at is None:
            # No inbound message ever → outside window
            return CheckResult(
                allowed=False,
                failed_policy=self.name,
                reason="No hay mensaje entrante del lead en los últimos 24 horas",
                evidence={
                    "last_inbound_at": None,
                    "hours_since_inbound": None,
                    "channel": channel,
                },
            )

        now_utc = dt.datetime.now(dt.timezone.utc)
        # Ensure timezone-aware comparison
        if last_inbound_at.tzinfo is None:
            last_inbound_at = last_inbound_at.replace(tzinfo=dt.timezone.utc)
        hours_since = (now_utc - last_inbound_at).total_seconds() / 3600

        if hours_since > 24:
            return CheckResult(
                allowed=False,
                failed_policy=self.name,
                reason=f"Último mensaje entrante hace {hours_since:.1f} horas (máximo 24h)",
                evidence={
                    "last_inbound_at": last_inbound_at.isoformat(),
                    "hours_since_inbound": round(hours_since, 2),
                    "channel": channel,
                },
            )

        return CheckResult(
            allowed=True,
            evidence={
                "last_inbound_at": last_inbound_at.isoformat(),
                "hours_since_inbound": round(hours_since, 2),
                "channel": channel,
            },
        )
