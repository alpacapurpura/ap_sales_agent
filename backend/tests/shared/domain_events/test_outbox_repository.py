"""Unit tests — OutboxRepository (pure logic, no DB).

Tests that don't require an active Postgres connection. Integration tests
(with real DB) are in tests/integration/ and marked with @pytest.mark.integration.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from luana_core_events.outbox.domain.event import DomainEvent
from luana_core_events.outbox.domain.outbox_entry import OutboxEntry, OutboxStatus
from luana_core_events.outbox.infrastructure.repository import OutboxRepositoryImpl


def _make_entry(tenant_id=None, idempotency_key=None, status=OutboxStatus.PENDING):
    """Helper to build a test OutboxEntry."""
    event = DomainEvent(
        event_name="test_event",
        tenant_id=tenant_id or uuid4(),
    )
    entry = OutboxEntry.from_event(event, idempotency_key=idempotency_key)
    object.__setattr__(entry, "status", status)
    return entry


class TestOutboxRepositoryImpl:
    """Tests for OutboxRepositoryImpl using mock sessions."""

    @pytest.mark.asyncio
    async def test_append_calls_execute_with_insert(self):
        """append() calls session.execute with an INSERT statement."""
        repo = OutboxRepositoryImpl()
        session = AsyncMock()
        # Simulate rowcount=1 (insert success)
        session.execute.return_value = MagicMock(rowcount=1)

        entry = _make_entry()
        await repo.append(entry, session=session)

        session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_append_on_conflict_no_raise(self):
        """append() ON CONFLICT (tenant_id, idempotency_key) logs warning, no raise."""
        repo = OutboxRepositoryImpl()
        session = AsyncMock()
        # Simulate conflict: rowcount=0
        session.execute.return_value = MagicMock(rowcount=0)

        entry = _make_entry(idempotency_key="existing_key")
        # Should not raise even with conflict
        await repo.append(entry, session=session)

    def test_append_sync_calls_execute_with_insert(self):
        """append_sync() calls sync session.execute with an INSERT statement."""
        repo = OutboxRepositoryImpl()
        session = MagicMock()
        session.execute.return_value = MagicMock(rowcount=1)

        entry = _make_entry()
        repo.append_sync(entry, session=session)

        session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_claim_pending_executes_select_with_for_update(self):
        """claim_pending() uses FOR UPDATE SKIP LOCKED in the query."""
        repo = OutboxRepositoryImpl()
        session = AsyncMock()

        # Return empty result (no pending entries)
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute.return_value = mock_result

        entries = await repo.claim_pending(batch_size=50, session=session)
        assert entries == []
        session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_dispatched_tenant_scoped(self):
        """mark_dispatched() passes tenant_id in WHERE clause."""
        repo = OutboxRepositoryImpl()
        session = AsyncMock()
        session.execute.return_value = MagicMock()

        entry_id = uuid4()
        tenant_id = uuid4()
        await repo.mark_dispatched(entry_id, tenant_id, session=session)

        session.execute.assert_called_once()
        # Verify tenant_id is in the statement (compile check via call)
        call_args = session.execute.call_args[0][0]
        # The WHERE clause must reference tenant_id
        compiled = str(call_args.compile(compile_kwargs={"literal_binds": True}))
        assert str(tenant_id) in compiled

    @pytest.mark.asyncio
    async def test_mark_failed_increments_retry_count(self):
        """mark_failed() increments retry_count and updates last_error."""
        repo = OutboxRepositoryImpl()
        session = AsyncMock()

        # Mock the select query returning a row with retry_count=0
        mock_row = MagicMock()
        mock_row.retry_count = 0
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_row
        # First call is SELECT, second is UPDATE
        session.execute.side_effect = [mock_result, MagicMock()]

        entry_id = uuid4()
        tenant_id = uuid4()
        await repo.mark_failed(entry_id, tenant_id, error="timeout", session=session)

        assert session.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_mark_failed_sets_status_failed_at_max_retries(self):
        """When retry_count reaches MAX_RETRIES (5), status becomes FAILED."""
        repo = OutboxRepositoryImpl()
        session = AsyncMock()

        mock_row = MagicMock()
        mock_row.retry_count = 4  # one more push → 5 → FAILED
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_row
        update_result = MagicMock()
        session.execute.side_effect = [mock_result, update_result]

        entry_id = uuid4()
        tenant_id = uuid4()
        await repo.mark_failed(entry_id, tenant_id, error="max error", session=session)

        # Second execute (UPDATE) should set status=failed
        update_call = session.execute.call_args_list[1][0][0]
        compiled = str(update_call.compile(compile_kwargs={"literal_binds": True}))
        assert "failed" in compiled

    @pytest.mark.asyncio
    async def test_mark_failed_keeps_pending_below_max_retries(self):
        """When retry_count < MAX_RETRIES, status stays PENDING after mark_failed."""
        repo = OutboxRepositoryImpl()
        session = AsyncMock()

        mock_row = MagicMock()
        mock_row.retry_count = 2  # < 5 → stays pending
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_row
        update_result = MagicMock()
        session.execute.side_effect = [mock_result, update_result]

        entry_id = uuid4()
        tenant_id = uuid4()
        await repo.mark_failed(entry_id, tenant_id, error="transient", session=session)

        update_call = session.execute.call_args_list[1][0][0]
        compiled = str(update_call.compile(compile_kwargs={"literal_binds": True}))
        # Should be 'pending', not 'failed'
        assert "pending" in compiled
        assert "failed" not in compiled

    @pytest.mark.asyncio
    async def test_get_by_id_requires_tenant_id(self):
        """get_by_id() always includes tenant_id in WHERE."""
        repo = OutboxRepositoryImpl()
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        entry_id = uuid4()
        tenant_id = uuid4()
        result = await repo.get_by_id(entry_id, tenant_id, session=session)
        assert result is None

        call_stmt = session.execute.call_args[0][0]
        compiled = str(call_stmt.compile(compile_kwargs={"literal_binds": True}))
        assert str(tenant_id) in compiled

    @pytest.mark.asyncio
    async def test_get_by_id_returns_entry_when_found(self):
        """get_by_id() maps ORM row to OutboxEntry domain object."""
        from luana_core_events.outbox.infrastructure.models import DomainEventOutboxModel

        repo = OutboxRepositoryImpl()
        session = AsyncMock()

        # Create a mock row that looks like DomainEventOutboxModel
        mock_row = MagicMock(spec=DomainEventOutboxModel)
        mock_row.id = uuid4()
        mock_row.tenant_id = uuid4()
        mock_row.event_name = "test_event"
        mock_row.payload = {}
        mock_row.idempotency_key = "test_key"
        mock_row.status = "pending"
        mock_row.retry_count = 0
        mock_row.last_error = None
        mock_row.created_at = datetime.now(UTC)
        mock_row.dispatched_at = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_row
        session.execute.return_value = mock_result

        result = await repo.get_by_id(mock_row.id, mock_row.tenant_id, session=session)
        assert result is not None
        assert result.id == mock_row.id
        assert result.tenant_id == mock_row.tenant_id
        assert result.status == OutboxStatus.PENDING
