"""OutboxEntry — domain entity for the transactional outbox pattern.

Pure Python. No framework dependencies. Persisted via OutboxRepository.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from src.shared.domain_events.outbox.domain.event import DomainEvent


class OutboxStatus(StrEnum):
    """Lifecycle states for an outbox entry."""

    PENDING = "pending"
    DISPATCHED = "dispatched"
    FAILED = "failed"  # max_retries exceeded — manual ops required


@dataclass(slots=True)
class OutboxEntry:
    """Domain entity. No framework deps. Persisted via OutboxRepository.

    Invariants:
    - ``tenant_id`` NEVER None (tenant_isolation rule applies to outbox).
    - ``idempotency_key`` unique with ``tenant_id`` (deduplication).
    - Status only transitions PENDING → DISPATCHED or PENDING → FAILED.
    - No soft-delete (operational table, retention via worker — S2).
    """

    id: UUID
    tenant_id: UUID
    event_name: str
    payload: dict[str, Any]
    idempotency_key: str  # NEVER None. Default = f"{event_name}:{uuid4()}"
    status: OutboxStatus
    retry_count: int
    last_error: str | None
    created_at: datetime
    dispatched_at: datetime | None

    @classmethod
    def from_event(
        cls,
        event: DomainEvent,
        idempotency_key: str | None = None,
    ) -> OutboxEntry:
        """Construct an OutboxEntry from a DomainEvent.

        Args:
            event: Domain event to persist. Must have ``tenant_id`` set.
            idempotency_key: Optional natural key for deduplication. If not
                provided, a unique key is auto-generated (no dedup protection).

        Returns:
            A new OutboxEntry with status=PENDING and retry_count=0.
        """
        return cls(
            id=uuid4(),
            tenant_id=event.tenant_id,
            event_name=event.event_name,
            payload=event.payload,
            idempotency_key=idempotency_key or f"{event.event_name}:{uuid4()}",
            status=OutboxStatus.PENDING,
            retry_count=0,
            last_error=None,
            created_at=datetime.now(UTC),
            dispatched_at=None,
        )
