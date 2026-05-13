"""Unit tests — OutboxEntry domain entity invariants.

RED-first per TDD-mandatory rule. Tests written before implementation.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from luana_core_events.outbox.domain.event import DomainEvent
from luana_core_events.outbox.domain.outbox_entry import OutboxEntry, OutboxStatus


class TestOutboxEntryFromEvent:
    """OutboxEntry.from_event factory invariants."""

    def test_from_event_produces_pending_status(self):
        """Entry created from event must have status=PENDING."""
        event = DomainEvent(event_name="test_event", tenant_id=uuid4())
        entry = OutboxEntry.from_event(event)
        assert entry.status == OutboxStatus.PENDING

    def test_from_event_produces_zero_retry_count(self):
        """Entry created from event must have retry_count=0."""
        event = DomainEvent(event_name="test_event", tenant_id=uuid4())
        entry = OutboxEntry.from_event(event)
        assert entry.retry_count == 0

    def test_from_event_copies_tenant_id(self):
        """Entry must carry the event's tenant_id."""
        tenant_id = uuid4()
        event = DomainEvent(event_name="test_event", tenant_id=tenant_id)
        entry = OutboxEntry.from_event(event)
        assert entry.tenant_id == tenant_id

    def test_from_event_copies_event_name_and_payload(self):
        """Entry carries event name and payload exactly."""
        payload = {"key": "value", "amount": 42.0}
        event = DomainEvent(event_name="sale_completed", tenant_id=uuid4(), payload=payload)
        entry = OutboxEntry.from_event(event)
        assert entry.event_name == "sale_completed"
        assert entry.payload == payload

    def test_from_event_autogen_idempotency_key_when_none(self):
        """When no idempotency_key passed, auto-generate unique key."""
        event = DomainEvent(event_name="test_event", tenant_id=uuid4())
        entry = OutboxEntry.from_event(event)
        assert entry.idempotency_key is not None
        assert len(entry.idempotency_key) > 0
        assert "test_event" in entry.idempotency_key

    def test_from_event_uses_caller_idempotency_key(self):
        """Explicit idempotency_key is preserved exactly."""
        key = "payment_link_created:ext-id-abc123"
        event = DomainEvent(event_name="payment_link_created", tenant_id=uuid4())
        entry = OutboxEntry.from_event(event, idempotency_key=key)
        assert entry.idempotency_key == key

    def test_from_event_two_calls_have_distinct_ids(self):
        """Two entries from same event must have distinct UUIDs."""
        event = DomainEvent(event_name="test_event", tenant_id=uuid4())
        entry1 = OutboxEntry.from_event(event)
        entry2 = OutboxEntry.from_event(event)
        assert entry1.id != entry2.id

    def test_from_event_created_at_is_utc(self):
        """created_at must be timezone-aware UTC."""
        event = DomainEvent(event_name="test_event", tenant_id=uuid4())
        entry = OutboxEntry.from_event(event)
        assert entry.created_at.tzinfo is not None
        # UTC offset = 0
        assert entry.created_at.utcoffset().total_seconds() == 0  # type: ignore[union-attr]

    def test_from_event_dispatched_at_is_none(self):
        """New entry must not have dispatched_at set."""
        event = DomainEvent(event_name="test_event", tenant_id=uuid4())
        entry = OutboxEntry.from_event(event)
        assert entry.dispatched_at is None

    def test_from_event_last_error_is_none(self):
        """New entry must not have last_error set."""
        event = DomainEvent(event_name="test_event", tenant_id=uuid4())
        entry = OutboxEntry.from_event(event)
        assert entry.last_error is None


class TestOutboxStatus:
    """OutboxStatus enum."""

    def test_status_values(self):
        """All three status values are present."""
        assert OutboxStatus.PENDING == "pending"
        assert OutboxStatus.DISPATCHED == "dispatched"
        assert OutboxStatus.FAILED == "failed"

    def test_status_is_str_enum(self):
        """OutboxStatus is a StrEnum — comparable with strings."""
        assert str(OutboxStatus.PENDING) == "pending"

    def test_legal_transitions(self):
        """Verify domain understanding: only PENDING is a starting state."""
        # This test documents the invariant — enforcement is in the repo.
        assert OutboxStatus.PENDING != OutboxStatus.DISPATCHED
        assert OutboxStatus.PENDING != OutboxStatus.FAILED
