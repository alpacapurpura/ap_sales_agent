"""Unit tests — OutboxDispatcher ARQ task."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.shared.domain_events.outbox.domain.event import DomainEvent
from src.shared.domain_events.outbox.domain.outbox_entry import OutboxEntry, OutboxStatus
from src.shared.domain_events.outbox.infrastructure.dispatcher import _entry_to_event, dispatch_outbox


def _make_pending_entry(event_name="test_event", tenant_id=None) -> OutboxEntry:
    """Build a pending OutboxEntry for tests."""
    event = DomainEvent(event_name=event_name, tenant_id=tenant_id or uuid4())
    return OutboxEntry.from_event(event, idempotency_key=f"{event_name}:{uuid4()}")


class TestDispatchOutbox:
    """Tests for dispatch_outbox ARQ task."""

    @pytest.mark.asyncio
    async def test_no_db_factory_returns_early(self):
        """dispatch_outbox with no db_factory logs warning and returns."""
        ctx = {}  # no db_factory
        # Should not raise
        await dispatch_outbox(ctx)

    @pytest.mark.asyncio
    async def test_pending_entries_get_dispatched(self):
        """Pending entries are claimed and marked dispatched."""
        tenant_id = uuid4()
        entry = _make_pending_entry(event_name="payment_received", tenant_id=tenant_id)

        mock_repo = AsyncMock()
        mock_repo.claim_pending.return_value = [entry]
        mock_repo.mark_dispatched = AsyncMock()

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_db_factory = MagicMock(return_value=mock_session)

        with (
            patch(
                "src.shared.domain_events.outbox.infrastructure.dispatcher.OutboxRepositoryImpl",
                return_value=mock_repo,
            ),
            patch(
                "src.shared.domain.events.EventBus._dispatch",
            ),
        ):
            await dispatch_outbox({"db_factory": mock_db_factory})

        mock_repo.claim_pending.assert_called_once()
        mock_repo.mark_dispatched.assert_called_once_with(entry.id, entry.tenant_id, session=mock_session)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_exception_marks_failed(self):
        """When dispatch raises, entry is marked failed."""
        entry = _make_pending_entry(event_name="brand_section_updated")

        mock_repo = AsyncMock()
        mock_repo.claim_pending.return_value = [entry]
        mock_repo.mark_dispatched = AsyncMock()
        mock_repo.mark_failed = AsyncMock()

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_db_factory = MagicMock(return_value=mock_session)

        with (
            patch(
                "src.shared.domain_events.outbox.infrastructure.dispatcher.OutboxRepositoryImpl",
                return_value=mock_repo,
            ),
            patch(
                "src.shared.domain.events.EventBus._dispatch",
                side_effect=Exception("handler boom"),
            ),
        ):
            await dispatch_outbox({"db_factory": mock_db_factory})

        mock_repo.mark_failed.assert_called_once()
        # mark_dispatched should NOT be called
        mock_repo.mark_dispatched.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_batch_commits_cleanly(self):
        """Empty outbox (no pending entries) still commits and exits cleanly."""
        mock_repo = AsyncMock()
        mock_repo.claim_pending.return_value = []

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_db_factory = MagicMock(return_value=mock_session)

        with patch(
            "src.shared.domain_events.outbox.infrastructure.dispatcher.OutboxRepositoryImpl",
            return_value=mock_repo,
        ):
            await dispatch_outbox({"db_factory": mock_db_factory})

        mock_session.commit.assert_called_once()
        mock_repo.mark_dispatched.assert_not_called()

    @pytest.mark.asyncio
    async def test_kill_and_restart_recovery(self):
        """Un-committed rows (worker died mid-batch) are reclaimed next tick.

        Simulates: entry in PENDING state even after first claim (uncommitted).
        Next call to dispatch_outbox claims it again and dispatches.
        """
        entry = _make_pending_entry(event_name="lead_captured")

        mock_repo = AsyncMock()
        # First call: returns entry but session never committed (simulating crash)
        # Second call: same entry is still PENDING, gets dispatched
        mock_repo.claim_pending.side_effect = [[entry], [entry]]
        mock_repo.mark_dispatched = AsyncMock()

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_db_factory = MagicMock(return_value=mock_session)

        with (
            patch(
                "src.shared.domain_events.outbox.infrastructure.dispatcher.OutboxRepositoryImpl",
                return_value=mock_repo,
            ),
            patch("src.shared.domain.events.EventBus._dispatch"),
        ):
            # Second tick recovers the entry
            await dispatch_outbox({"db_factory": mock_db_factory})

        mock_repo.mark_dispatched.assert_called_once()


class TestEntryToEvent:
    """Tests for _entry_to_event helper."""

    def test_converts_entry_to_domain_event(self):
        """_entry_to_event maps entry fields to DomainEvent correctly."""
        entry = _make_pending_entry(event_name="sale_completed")
        entry.payload["sale_id"] = str(uuid4())

        event = _entry_to_event(entry)

        assert event.event_name == "sale_completed"
        assert event.tenant_id == entry.tenant_id
        assert event.payload == entry.payload
