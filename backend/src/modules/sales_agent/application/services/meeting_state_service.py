"""MeetingStateService — owner of ``scheduled_meetings`` JSONB.

Single source of truth for the ``agent_state_checkpoints.scheduled_meetings``
shape across tools, workers, and webhook handlers.

DRY: tools + workers + webhook endpoint must NEVER mutate the JSONB
list directly. They go through this service.

Cohesion: this is the only place where ``scheduled_meetings`` schema is
serialized / interpreted. Adding a field (e.g. ``recording_url``)
touches one file, not five.

Coupling: depends on ``AgentStateCheckpointModel`` only — no scheduler,
no LLM, no provider. Tenant isolation enforced at every read/write.
"""

# [SALES-AGENT-S8-PROVIDER]  # noqa: ERA001

from __future__ import annotations

import datetime as dt
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

    from src.modules.sales_agent.application.tools.scheduling.providers import (
        BookingLinkOutput,
    )

logger = structlog.get_logger()


class MeetingEntryStatus(StrEnum):
    """Lifecycle states of a scheduled_meetings entry."""

    LINK_CREATED = "link_created"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    MISSED = "missed"


@dataclass(frozen=True, slots=True)
class MeetingEntry:
    """Typed view over a ``scheduled_meetings`` JSONB element."""

    tracking_id: str
    event_slug: str
    expires_at: dt.datetime
    status: MeetingEntryStatus
    appointment_id: UUID | None
    scheduled_at: dt.datetime | None
    reminder_24h_sent_at: dt.datetime | None
    reminder_1h_sent_at: dt.datetime | None
    postcheck_sent_at: dt.datetime | None
    created_at: dt.datetime
    provider_id: str

    @classmethod
    def from_jsonb(cls, raw: dict[str, Any]) -> MeetingEntry:
        """Hydrate from the JSONB dict shape persisted on the checkpoint."""
        return cls(
            tracking_id=raw["tracking_id"],
            event_slug=raw.get("event_slug", ""),
            expires_at=_parse_iso(raw["expires_at"]),
            status=MeetingEntryStatus(raw.get("status", "link_created")),
            appointment_id=UUID(raw["appointment_id"]) if raw.get("appointment_id") else None,
            scheduled_at=_parse_iso(raw["scheduled_at"]) if raw.get("scheduled_at") else None,
            reminder_24h_sent_at=_parse_iso(raw["reminder_24h_sent_at"]) if raw.get("reminder_24h_sent_at") else None,
            reminder_1h_sent_at=_parse_iso(raw["reminder_1h_sent_at"]) if raw.get("reminder_1h_sent_at") else None,
            postcheck_sent_at=_parse_iso(raw["postcheck_sent_at"]) if raw.get("postcheck_sent_at") else None,
            created_at=_parse_iso(raw.get("created_at", raw["expires_at"])),
            provider_id=raw.get("provider_id", "internal"),
        )

    def to_jsonb(self) -> dict[str, Any]:
        """Serialize back into JSONB form."""
        return {
            "tracking_id": self.tracking_id,
            "event_slug": self.event_slug,
            "expires_at": self.expires_at.isoformat(),
            "status": self.status.value,
            "appointment_id": str(self.appointment_id) if self.appointment_id else None,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "reminder_24h_sent_at": self.reminder_24h_sent_at.isoformat() if self.reminder_24h_sent_at else None,
            "reminder_1h_sent_at": self.reminder_1h_sent_at.isoformat() if self.reminder_1h_sent_at else None,
            "postcheck_sent_at": self.postcheck_sent_at.isoformat() if self.postcheck_sent_at else None,
            "created_at": self.created_at.isoformat(),
            "provider_id": self.provider_id,
        }


class MeetingStateService:
    """Read/write helpers for ``scheduled_meetings`` JSONB."""

    def __init__(self, db: Session) -> None:
        """Initialize MeetingStateService."""
        self.db = db

    # ── reads ───────────────────────────────────────────────

    def list_for_lead(self, tenant_id: UUID, lead_id: UUID) -> list[MeetingEntry]:
        """Return all meeting entries for the active checkpoint of a lead."""
        cp = self._active_checkpoint(tenant_id, lead_id)
        if cp is None:
            return []
        raw_list = cp.scheduled_meetings or []
        return [MeetingEntry.from_jsonb(r) for r in raw_list]

    def find_active_link(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        event_slug: str,
    ) -> MeetingEntry | None:
        """Return existing non-expired LINK_CREATED entry for the same slug.

        Used by ``tool_create_booking_link`` for idempotency: re-invoking
        the tool inside the same window reuses the live link instead of
        spawning a duplicate.
        """
        now = dt.datetime.now(dt.UTC)
        for entry in self.list_for_lead(tenant_id, lead_id):
            if (
                entry.status == MeetingEntryStatus.LINK_CREATED
                and entry.event_slug == event_slug
                and entry.expires_at > now
            ):
                return entry
        return None

    # ── writes ──────────────────────────────────────────────

    def append_link(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        booking: BookingLinkOutput,
    ) -> MeetingEntry:
        """Append a new LINK_CREATED entry."""
        cp = self._require_checkpoint(tenant_id, lead_id)
        entry = MeetingEntry(
            tracking_id=booking.tracking_id,
            event_slug=booking.event_slug,
            expires_at=booking.expires_at,
            status=MeetingEntryStatus.LINK_CREATED,
            appointment_id=None,
            scheduled_at=None,
            reminder_24h_sent_at=None,
            reminder_1h_sent_at=None,
            postcheck_sent_at=None,
            created_at=dt.datetime.now(dt.UTC),
            provider_id=booking.provider_id,
        )
        meetings = list(cp.scheduled_meetings or [])
        meetings.append(entry.to_jsonb())
        cp.scheduled_meetings = meetings
        flag_modified(cp, "scheduled_meetings")
        return entry

    def update_status_by_tracking(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        tracking_id: str,
        *,
        status: MeetingEntryStatus,
        appointment_id: UUID | None = None,
        scheduled_at: dt.datetime | None = None,
    ) -> MeetingEntry | None:
        """Update an entry's lifecycle. Returns the updated entry or None."""
        cp = self._active_checkpoint(tenant_id, lead_id)
        if cp is None or not cp.scheduled_meetings:
            return None
        meetings = list(cp.scheduled_meetings)
        for idx, raw in enumerate(meetings):
            if raw.get("tracking_id") != tracking_id:
                continue
            entry = MeetingEntry.from_jsonb(raw)
            updated = MeetingEntry(
                tracking_id=entry.tracking_id,
                event_slug=entry.event_slug,
                expires_at=entry.expires_at,
                status=status,
                appointment_id=appointment_id or entry.appointment_id,
                scheduled_at=scheduled_at or entry.scheduled_at,
                reminder_24h_sent_at=entry.reminder_24h_sent_at,
                reminder_1h_sent_at=entry.reminder_1h_sent_at,
                postcheck_sent_at=entry.postcheck_sent_at,
                created_at=entry.created_at,
                provider_id=entry.provider_id,
            )
            meetings[idx] = updated.to_jsonb()
            cp.scheduled_meetings = meetings
            flag_modified(cp, "scheduled_meetings")
            return updated
        return None

    def mark_reminder_sent(
        self,
        tenant_id: UUID,
        lead_id: UUID,
        tracking_id: str,
        *,
        reminder_kind: str,
    ) -> MeetingEntry | None:
        """Stamp ``reminder_{24h,1h}_sent_at`` or ``postcheck_sent_at``.

        ``reminder_kind`` ∈ {``"24h"``, ``"1h"``, ``"postcheck"``}.
        """
        cp = self._active_checkpoint(tenant_id, lead_id)
        if cp is None or not cp.scheduled_meetings:
            return None
        meetings = list(cp.scheduled_meetings)
        now = dt.datetime.now(dt.UTC)
        for idx, raw in enumerate(meetings):
            if raw.get("tracking_id") != tracking_id:
                continue
            entry = MeetingEntry.from_jsonb(raw)
            stamps = {
                "24h": "reminder_24h_sent_at",
                "1h": "reminder_1h_sent_at",
                "postcheck": "postcheck_sent_at",
            }
            key = stamps.get(reminder_kind)
            if key is None:
                msg = f"Unknown reminder_kind: {reminder_kind!r}"
                raise ValueError(msg)
            new_raw = entry.to_jsonb()
            new_raw[key] = now.isoformat()
            meetings[idx] = new_raw
            cp.scheduled_meetings = meetings
            flag_modified(cp, "scheduled_meetings")
            return MeetingEntry.from_jsonb(new_raw)
        return None

    # ── internals ───────────────────────────────────────────

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
