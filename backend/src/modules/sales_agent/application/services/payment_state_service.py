"""PaymentStateService — owner of ``payment_state`` JSONB — S9.

Mirrors MeetingStateService (S8). Single source of truth for the
``agent_state_checkpoints.payment_state`` shape across tools, workers, and
webhook handlers.

DRY: tools + workers + webhook endpoint NEVER mutate the JSONB directly.
Cohesion: only this file knows the schema of each entry.
Coupling: depends on ``AgentStateCheckpointModel`` only.
"""

from __future__ import annotations

import datetime as dt
import uuid as _uuid_mod
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from src.modules.sales_agent.infrastructure.models.agent_state_checkpoint_model import (
    AgentStateCheckpointModel,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from src.modules.sales_agent.application.tools.payment.providers import (
        PaymentLinkOutput,
    )

logger = structlog.get_logger()


class PaymentEntryStatus(StrEnum):
    """Lifecycle states of a payment_state entry."""

    LINK_CREATED = "link_created"
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


@dataclass(frozen=True, slots=True)
class PaymentEntry:
    """Typed view over a ``payment_state`` JSONB element."""

    payment_id: UUID
    external_id: str
    provider_id: str
    url: str
    amount: float
    currency: str
    status: PaymentEntryStatus
    created_at: dt.datetime
    reminder_sent_at: dt.datetime | None

    @classmethod
    def from_jsonb(cls, raw: dict[str, Any]) -> PaymentEntry:
        """Hydrate from JSONB dict."""
        return cls(
            payment_id=UUID(raw["payment_id"]),
            external_id=raw["external_id"],
            provider_id=raw.get("provider_id", ""),
            url=raw.get("url", ""),
            amount=float(raw.get("amount", 0.0)),
            currency=raw.get("currency", "USD"),
            status=PaymentEntryStatus(raw.get("status", "link_created")),
            created_at=_parse_iso(raw.get("created_at", dt.datetime.now(dt.UTC).isoformat())),
            reminder_sent_at=_parse_iso(raw["reminder_sent_at"]) if raw.get("reminder_sent_at") else None,
        )

    def to_jsonb(self) -> dict[str, Any]:
        """Serialize to JSONB form."""
        return {
            "payment_id": str(self.payment_id),
            "external_id": self.external_id,
            "provider_id": self.provider_id,
            "url": self.url,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "reminder_sent_at": self.reminder_sent_at.isoformat() if self.reminder_sent_at else None,
        }


class PaymentStateService:
    """Read/write helpers for ``payment_state`` JSONB."""

    def __init__(self, db: Session) -> None:
        """Initialize PaymentStateService."""
        self.db = db

    # ── reads ────────────────────────────────────────────────

    def list_for_lead(self, tenant_id: UUID, lead_id: UUID) -> list[PaymentEntry]:
        """Return all payment entries for the active checkpoint of a lead."""
        cp = self._active_checkpoint(tenant_id, lead_id)
        if cp is None:
            return []
        raw_list = cp.payment_state or []
        return [PaymentEntry.from_jsonb(r) for r in raw_list]

    def find_pending_link(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        filter_value: UUID | str | None = None,
    ) -> PaymentEntry | None:
        """Return existing LINK_CREATED / PENDING entry.

        ``filter_value`` can be:
        - A ``UUID`` → matched against the entry's external_id UUID (rare) or
          provider_id string representation.
        - A ``str`` → matched against provider_id.
        - ``None`` → first active entry is returned.

        Used by tools for idempotency and by workers for state lookup.
        """
        active = {PaymentEntryStatus.LINK_CREATED, PaymentEntryStatus.PENDING}
        for entry in self.list_for_lead(tenant_id, lead_id):
            if entry.status not in active:
                continue
            if filter_value is None:
                return entry
            filter_str = str(filter_value)
            if filter_str in {entry.provider_id, entry.external_id}:
                return entry
        return None

    # ── writes ───────────────────────────────────────────────

    def append_link(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        link_output: PaymentLinkOutput,
        *,
        payment_id: UUID | None = None,
    ) -> PaymentEntry:
        """Append a new LINK_CREATED entry.

        ``payment_id`` is the PaymentLinkModel PK. If not provided, a new
        UUID is generated (useful in unit tests that don't create DB rows).
        """
        cp = self._require_checkpoint(tenant_id, lead_id)
        entry = PaymentEntry(
            payment_id=payment_id or _uuid_mod.uuid4(),
            external_id=link_output.external_id,
            provider_id=link_output.provider_id,
            url=link_output.url,
            amount=link_output.amount or 0.0,
            currency=link_output.currency or "USD",
            status=PaymentEntryStatus.LINK_CREATED,
            created_at=dt.datetime.now(dt.UTC),
            reminder_sent_at=None,
        )
        state = list(cp.payment_state or [])
        state.append(entry.to_jsonb())
        cp.payment_state = state
        flag_modified(cp, "payment_state")
        return entry

    def update_status_by_external_id(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        external_id: str,
        *,
        status: PaymentEntryStatus,
    ) -> PaymentEntry | None:
        """Update an entry's status. Returns updated entry or None."""
        cp = self._active_checkpoint(tenant_id, lead_id)
        if cp is None or not cp.payment_state:
            return None
        state = list(cp.payment_state)
        for idx, raw in enumerate(state):
            if raw.get("external_id") != external_id:
                continue
            entry = PaymentEntry.from_jsonb(raw)
            new_raw = entry.to_jsonb()
            new_raw["status"] = status.value
            state[idx] = new_raw
            cp.payment_state = state
            flag_modified(cp, "payment_state")
            return PaymentEntry.from_jsonb(new_raw)
        return None

    def mark_reminder_sent(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        external_id: str,
    ) -> PaymentEntry | None:
        """Stamp reminder_sent_at for a payment entry."""
        cp = self._active_checkpoint(tenant_id, lead_id)
        if cp is None or not cp.payment_state:
            return None
        state = list(cp.payment_state)
        now = dt.datetime.now(dt.UTC)
        for idx, raw in enumerate(state):
            if raw.get("external_id") != external_id:
                continue
            updated = {**raw, "reminder_sent_at": now.isoformat()}
            state[idx] = updated
            cp.payment_state = state
            flag_modified(cp, "payment_state")
            return PaymentEntry.from_jsonb(updated)
        return None

    # ── internals ────────────────────────────────────────────

    def _active_checkpoint(
        self,
        tenant_id: UUID,
        lead_id: UUID,
    ) -> AgentStateCheckpointModel | None:
        stmt = select(AgentStateCheckpointModel).where(
            AgentStateCheckpointModel.tenant_id == tenant_id,
            AgentStateCheckpointModel.lead_id == lead_id,
            AgentStateCheckpointModel.is_active.is_(True),
            AgentStateCheckpointModel.deleted_at.is_(None),
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def _require_checkpoint(
        self,
        tenant_id: UUID,
        lead_id: UUID,
    ) -> AgentStateCheckpointModel:
        cp = self._active_checkpoint(tenant_id, lead_id)
        if cp is None:
            msg = f"No active checkpoint for tenant={tenant_id} lead={lead_id}"
            raise LookupError(msg)
        return cp


def _parse_iso(value: str | dt.datetime) -> dt.datetime:
    """Parse ISO 8601 → UTC-aware datetime."""
    if isinstance(value, dt.datetime):
        return value if value.tzinfo else value.replace(tzinfo=dt.UTC)
    parsed = dt.datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.UTC)
