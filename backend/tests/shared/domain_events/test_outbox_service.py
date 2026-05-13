"""Unit tests — OutboxService application service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from luana_core_events.outbox.application.outbox_service import OutboxService
from luana_core_events.outbox.domain.event import DomainEvent


class TestOutboxServiceEnqueueSync:
    """Tests for OutboxService.enqueue_sync."""

    def test_requires_session_raises_value_error_when_none(self):
        """enqueue_sync must raise ValueError when session is None."""
        service = OutboxService()
        event = DomainEvent(event_name="test_event", tenant_id=uuid4())
        with pytest.raises(ValueError, match="requires a session"):
            service.enqueue_sync(event, session=None)  # type: ignore[arg-type]

    def test_calls_repo_append_sync(self):
        """enqueue_sync delegates to OutboxRepositoryImpl.append_sync."""
        mock_repo = MagicMock()
        service = OutboxService(repo=mock_repo)
        session = MagicMock()
        event = DomainEvent(event_name="payment_link_created", tenant_id=uuid4())

        service.enqueue_sync(event, session=session)

        mock_repo.append_sync.assert_called_once()
        # Verify the entry passed carries the correct event_name
        call_kwargs = mock_repo.append_sync.call_args
        entry_arg = call_kwargs[0][0]
        assert entry_arg.event_name == "payment_link_created"

    def test_does_not_commit_session(self):
        """enqueue_sync does NOT call session.commit (caller's responsibility)."""
        mock_repo = MagicMock()
        service = OutboxService(repo=mock_repo)
        session = MagicMock()
        event = DomainEvent(event_name="test_event", tenant_id=uuid4())

        service.enqueue_sync(event, session=session)

        session.commit.assert_not_called()

    def test_uses_caller_idempotency_key(self):
        """enqueue_sync passes caller's idempotency_key to repo."""
        mock_repo = MagicMock()
        service = OutboxService(repo=mock_repo)
        session = MagicMock()
        event = DomainEvent(event_name="test_event", tenant_id=uuid4())
        key = "payment_received:ext-abc"

        service.enqueue_sync(event, session=session, idempotency_key=key)

        call_kwargs = mock_repo.append_sync.call_args
        entry_arg = call_kwargs[0][0]
        assert entry_arg.idempotency_key == key

    def test_duplicate_key_does_not_raise(self):
        """Duplicate idempotency_key (dedupe) must NOT raise from service layer."""
        # Repo handles conflict silently; service should not wrap it in an exception
        mock_repo = MagicMock()
        mock_repo.append_sync.return_value = None  # no exception on conflict
        service = OutboxService(repo=mock_repo)
        session = MagicMock()
        event = DomainEvent(event_name="test_event", tenant_id=uuid4())
        key = "duplicate:key"

        service.enqueue_sync(event, session=session, idempotency_key=key)
        service.enqueue_sync(event, session=session, idempotency_key=key)

        # Both calls succeeded without exception
        assert mock_repo.append_sync.call_count == 2


class TestOutboxServiceEnqueueAsync:
    """Tests for OutboxService.enqueue_async_from_sync_caller."""

    @pytest.mark.asyncio
    async def test_requires_session_raises_value_error_when_none(self):
        """enqueue_async_from_sync_caller must raise ValueError when session is None."""
        service = OutboxService()
        event = DomainEvent(event_name="test_event", tenant_id=uuid4())
        with pytest.raises(ValueError, match="requires a session"):
            await service.enqueue_async_from_sync_caller(event, session=None)  # type: ignore[arg-type]

    @pytest.mark.asyncio
    async def test_calls_repo_append_async(self):
        """enqueue_async_from_sync_caller delegates to repo.append."""
        mock_repo = MagicMock()
        mock_repo.append = AsyncMock()
        service = OutboxService(repo=mock_repo)
        session = AsyncMock()
        event = DomainEvent(event_name="brand_section_updated", tenant_id=uuid4())

        await service.enqueue_async_from_sync_caller(event, session=session)

        mock_repo.append.assert_called_once()
        entry_arg = mock_repo.append.call_args[0][0]
        assert entry_arg.event_name == "brand_section_updated"

    @pytest.mark.asyncio
    async def test_does_not_commit_session(self):
        """enqueue_async_from_sync_caller does NOT call session.commit."""
        mock_repo = MagicMock()
        mock_repo.append = AsyncMock()
        service = OutboxService(repo=mock_repo)
        session = AsyncMock()
        event = DomainEvent(event_name="test_event", tenant_id=uuid4())

        await service.enqueue_async_from_sync_caller(event, session=session)

        session.commit.assert_not_called()
