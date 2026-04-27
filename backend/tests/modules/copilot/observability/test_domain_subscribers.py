"""Tests for the domain-event subscribers.

Phase 1 ships only the subscribers + ``register_subscribers`` factory —
they're NOT registered yet (the publishers in ``copilot.domain.events``
land in Phase 2). The factory is opt-in: call it once at module-boot
to subscribe; tests do that explicitly.
"""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.orm import sessionmaker

from src.shared.domain.events import DomainEvent, EventBus


@pytest.fixture
def db(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(autouse=True)
def _isolated_event_bus():
    """Each test starts with an empty handler registry."""
    EventBus.clear()
    yield
    EventBus.clear()


class TestRegisterSubscribers:
    def test_register_is_idempotent(self, db) -> None:
        from src.modules.copilot.observability.recording.domain_subscribers import (
            register_subscribers,
        )

        repo_factory = MagicMock(return_value=MagicMock())
        register_subscribers(repo_factory=repo_factory)
        register_subscribers(repo_factory=repo_factory)

        # Same handler should be present once per event_name (no duplicate).
        for handlers in EventBus._handlers.values():
            names = {getattr(h, "__name__", h) for h in handlers}
            assert len(names) == len(handlers)

    def test_card_emitted_persists_trace_event(self, db) -> None:
        from src.modules.copilot.observability.persistence.trace_event_repository import (
            TraceEventRepository,
        )
        from src.modules.copilot.observability.recording.domain_subscribers import (
            register_subscribers,
        )

        register_subscribers(repo_factory=lambda: TraceEventRepository(db))
        tenant = uuid4()
        EventBus.publish(
            DomainEvent(
                event_name="copilot_card_emitted",
                tenant_id=tenant,
                payload={
                    "card_kind": "extraction_summary",
                    "source_tool": "extract_from_doc",
                    "turn_id": str(uuid4()),
                    "conversation_id": str(uuid4()),
                },
            ),
        )
        db.flush()
        from src.modules.copilot.infrastructure.models.trace_event_model import (
            CopilotTraceEventModel,
        )

        rows = db.query(CopilotTraceEventModel).filter_by(tenant_id=tenant, event_type="card_emitted").all()
        assert len(rows) == 1
        assert rows[0].name == "extraction_summary"

    def test_handler_failure_does_not_propagate(self, db) -> None:
        """EventBus already isolates handler exceptions; verify our factory plays nice."""
        from src.modules.copilot.observability.recording.domain_subscribers import (
            register_subscribers,
        )

        broken_repo = MagicMock()
        broken_repo.add.side_effect = RuntimeError("DB down")
        register_subscribers(repo_factory=lambda: broken_repo)

        # Must not raise — EventBus._dispatch wraps handler errors.
        EventBus.publish(
            DomainEvent(
                event_name="copilot_card_emitted",
                tenant_id=uuid4(),
                payload={"card_kind": "k", "turn_id": str(uuid4())},
            ),
        )
