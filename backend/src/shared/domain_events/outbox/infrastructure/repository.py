"""OutboxRepository — interface and implementation.

Two concrete paths:
- ``append_sync`` for synchronous Session callers (75%+ of the 38 sites).
- ``append_async`` for AsyncSession callers.

``claim_pending`` is cross-tenant (worker scope) and uses FOR UPDATE SKIP LOCKED.
All other methods require ``tenant_id`` per tenant-isolation rule.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog
from luana_core_events.outbox.domain.outbox_entry import (
    OutboxEntry,
    OutboxStatus,
)
from luana_core_events.outbox.infrastructure.models import DomainEventOutboxModel
from luana_core_observability.recording.sanitization import sanitize_payload
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

if TYPE_CHECKING:
    from collections.abc import Sequence
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import Session

logger = structlog.get_logger(__name__)

_MAX_RETRIES = 5


class OutboxRepository(ABC):
    """Abstract repository interface for the outbox.

    Async, tenant-scoped. Every operation filters tenant_id.
    Exception: ``claim_pending`` — cross-tenant read for worker scope.
    """

    @abstractmethod
    async def append(self, entry: OutboxEntry, *, session: AsyncSession) -> None:
        """Insert inside caller's async transaction. Caller commits."""

    @abstractmethod
    def append_sync(self, entry: OutboxEntry, *, session: Session) -> None:
        """Insert inside caller's sync transaction. Caller commits."""

    @abstractmethod
    async def claim_pending(
        self,
        *,
        batch_size: int,
        session: AsyncSession,
    ) -> Sequence[OutboxEntry]:
        """SELECT ... FOR UPDATE SKIP LOCKED. Cross-tenant (worker scope)."""

    @abstractmethod
    async def mark_dispatched(
        self,
        entry_id: UUID,
        tenant_id: UUID,
        *,
        session: AsyncSession,
    ) -> None:
        """Update status=dispatched + dispatched_at=now. Tenant-scoped."""

    @abstractmethod
    async def mark_failed(
        self,
        entry_id: UUID,
        tenant_id: UUID,
        *,
        error: str,
        session: AsyncSession,
    ) -> None:
        """Increment retry_count. If >= MAX_RETRIES → status=failed."""

    @abstractmethod
    async def get_by_id(
        self,
        entry_id: UUID,
        tenant_id: UUID,
        *,
        session: AsyncSession,
    ) -> OutboxEntry | None:
        """Lookup by PK. Tenant-scoped (required by tenant-isolation rule)."""


class OutboxRepositoryImpl(OutboxRepository):
    """Concrete SQLAlchemy 2.0 implementation."""

    @staticmethod
    def _to_entry(row: DomainEventOutboxModel) -> OutboxEntry:
        return OutboxEntry(
            id=row.id,
            tenant_id=row.tenant_id,
            event_name=row.event_name,
            payload=row.payload,
            idempotency_key=row.idempotency_key,
            status=OutboxStatus(row.status),
            retry_count=row.retry_count,
            last_error=row.last_error,
            created_at=row.created_at,
            dispatched_at=row.dispatched_at,
        )

    async def append(self, entry: OutboxEntry, *, session: AsyncSession) -> None:
        """Insert outbox entry. ON CONFLICT (tenant_id, idempotency_key) → skip.

        PII sanitization (F-3, PI-1 S0 post-REVIEW):
        Payload is run through ``sanitize_payload`` before insert to redact
        emails, phones, national IDs, card numbers, and API tokens. Best-effort
        — sanitization failure falls back to the raw payload so the outbox
        insert is never blocked.
        """
        try:
            safe_payload = sanitize_payload(entry.payload)
        except Exception:  # noqa: BLE001 — best-effort, must not block insert
            logger.warning(
                "outbox_pii_sanitization_failed",
                event_name=entry.event_name,
                tenant_id=str(entry.tenant_id),
            )
            safe_payload = entry.payload

        stmt = (
            pg_insert(DomainEventOutboxModel)
            .values(
                id=entry.id,
                tenant_id=entry.tenant_id,
                event_name=entry.event_name,
                payload=safe_payload,
                idempotency_key=entry.idempotency_key,
                status=entry.status.value,
                retry_count=entry.retry_count,
                last_error=entry.last_error,
                created_at=entry.created_at,
                dispatched_at=entry.dispatched_at,
            )
            .on_conflict_do_nothing(
                index_elements=["tenant_id", "idempotency_key"],
            )
        )
        result = await session.execute(stmt)
        if result.rowcount == 0:
            logger.warning(
                "outbox_dedupe_skip",
                tenant_id=str(entry.tenant_id),
                idempotency_key=entry.idempotency_key,
                event_name=entry.event_name,
            )
        else:
            logger.info(
                "outbox_enqueued",
                tenant_id=str(entry.tenant_id),
                event_name=entry.event_name,
                idempotency_key=entry.idempotency_key,
                entry_id=str(entry.id),
            )

    def append_sync(self, entry: OutboxEntry, *, session: Session) -> None:
        """Insert outbox entry using synchronous Session (psycopg2).

        ON CONFLICT (tenant_id, idempotency_key) → skip.
        Caller responsible for session.commit().

        PII sanitization (F-3, PI-1 S0 post-REVIEW):
        Payload is run through ``sanitize_payload`` before insert to redact
        emails, phones, national IDs, card numbers, and API tokens. Best-effort
        — sanitization failure falls back to the raw payload so the outbox
        insert is never blocked.
        """
        from sqlalchemy.dialects.postgresql import insert as pg_insert_sync

        try:
            safe_payload = sanitize_payload(entry.payload)
        except Exception:  # noqa: BLE001 — best-effort, must not block insert
            logger.warning(
                "outbox_pii_sanitization_failed",
                event_name=entry.event_name,
                tenant_id=str(entry.tenant_id),
            )
            safe_payload = entry.payload

        stmt = (
            pg_insert_sync(DomainEventOutboxModel)
            .values(
                id=entry.id,
                tenant_id=entry.tenant_id,
                event_name=entry.event_name,
                payload=safe_payload,
                idempotency_key=entry.idempotency_key,
                status=entry.status.value,
                retry_count=entry.retry_count,
                last_error=entry.last_error,
                created_at=entry.created_at,
                dispatched_at=entry.dispatched_at,
            )
            .on_conflict_do_nothing(
                index_elements=["tenant_id", "idempotency_key"],
            )
        )
        result = session.execute(stmt)
        if result.rowcount == 0:
            logger.warning(
                "outbox_dedupe_skip",
                tenant_id=str(entry.tenant_id),
                idempotency_key=entry.idempotency_key,
                event_name=entry.event_name,
            )
        else:
            logger.info(
                "outbox_enqueued",
                tenant_id=str(entry.tenant_id),
                event_name=entry.event_name,
                idempotency_key=entry.idempotency_key,
                entry_id=str(entry.id),
            )

    async def claim_pending(
        self,
        *,
        batch_size: int = 50,
        session: AsyncSession,
    ) -> Sequence[OutboxEntry]:
        """SELECT ... FOR UPDATE SKIP LOCKED. Cross-tenant (worker scope).

        Returns entries with status='pending', ordered by created_at ASC.
        """
        stmt = (
            select(DomainEventOutboxModel)
            .where(DomainEventOutboxModel.status == OutboxStatus.PENDING.value)
            .order_by(DomainEventOutboxModel.created_at.asc())
            .limit(batch_size)
            .with_for_update(skip_locked=True)
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()
        return [self._to_entry(row) for row in rows]

    async def mark_dispatched(
        self,
        entry_id: UUID,
        tenant_id: UUID,
        *,
        session: AsyncSession,
    ) -> None:
        """Update status=dispatched + dispatched_at=now. Tenant-scoped."""
        stmt = (
            update(DomainEventOutboxModel)
            .where(
                DomainEventOutboxModel.id == entry_id,
                DomainEventOutboxModel.tenant_id == tenant_id,
            )
            .values(
                status=OutboxStatus.DISPATCHED.value,
                dispatched_at=datetime.now(UTC),
            )
        )
        await session.execute(stmt)

    async def mark_failed(
        self,
        entry_id: UUID,
        tenant_id: UUID,
        *,
        error: str,
        session: AsyncSession,
    ) -> None:
        """Increment retry_count. If >= MAX_RETRIES → status=failed (manual ops)."""
        # First read to check current retry_count
        stmt = select(DomainEventOutboxModel).where(
            DomainEventOutboxModel.id == entry_id,
            DomainEventOutboxModel.tenant_id == tenant_id,
        )
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            logger.warning(
                "outbox_mark_failed_not_found",
                entry_id=str(entry_id),
                tenant_id=str(tenant_id),
            )
            return

        new_count = row.retry_count + 1
        new_status = OutboxStatus.FAILED.value if new_count >= _MAX_RETRIES else OutboxStatus.PENDING.value

        update_stmt = (
            update(DomainEventOutboxModel)
            .where(
                DomainEventOutboxModel.id == entry_id,
                DomainEventOutboxModel.tenant_id == tenant_id,
            )
            .values(
                retry_count=new_count,
                last_error=error[:500],  # truncate to 500 chars
                status=new_status,
            )
        )
        await session.execute(update_stmt)

        if new_status == OutboxStatus.FAILED.value:
            logger.error(
                "outbox_dispatch_failed_max_retries",
                entry_id=str(entry_id),
                last_error=error[:200],
                retry_count=new_count,
            )
        else:
            logger.warning(
                "outbox_dispatch_retry",
                entry_id=str(entry_id),
                retry_count=new_count,
                error=error[:200],
            )

    async def get_by_id(
        self,
        entry_id: UUID,
        tenant_id: UUID,
        *,
        session: AsyncSession,
    ) -> OutboxEntry | None:
        """Lookup by PK. tenant_id is MANDATORY (tenant-isolation rule)."""
        stmt = select(DomainEventOutboxModel).where(
            DomainEventOutboxModel.id == entry_id,
            DomainEventOutboxModel.tenant_id == tenant_id,
        )
        result = await session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return self._to_entry(row)
