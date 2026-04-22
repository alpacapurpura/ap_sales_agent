"""MutationJournalEntry domain dataclass — pure Python, no ORM."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class MutationJournalEntry:
    """Represents a single field mutation journaled by the copilot."""

    id: UUID
    tenant_id: UUID
    conversation_id: UUID
    message_id: UUID
    domain: str
    entity_id: UUID | None
    field_path: str
    old_value: Any | None
    new_value: Any | None
    applied_at: datetime
    reverted_at: datetime | None


@dataclass(frozen=True, slots=True)
class RevertResult:
    """Result of a revert operation on a single journal entry."""

    entry_id: UUID
    success: bool
    error: str | None = None
