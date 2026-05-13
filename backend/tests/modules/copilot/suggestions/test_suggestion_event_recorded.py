"""TDD — suggestion events → copilot_trace_event subscriber.

Tests written RED first per ``tdd-mandatory.md``.
"""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from luana_core_platform.domain.events import DomainEvent, EventBus


@pytest.fixture(autouse=True)
def _isolated_event_bus():
    """Each test starts with an empty handler registry."""
    EventBus.clear()
    yield
    EventBus.clear()


class TestSuggestionShownSubscriber:
    def test_suggestion_shown_event_persists_trace_row(self, db_engine) -> None:
        """Publish SuggestionShown → row in copilot_trace_event."""
        from sqlalchemy.orm import sessionmaker

        from luana_core_copilot.domain.events import SuggestionShown
        from luana_core_copilot.observability.persistence.trace_event_repository import (
            TraceEventRepository,
        )
        from luana_core_copilot.observability.recording.domain_subscribers import (
            register_subscribers,
        )
        from luana_core_copilot.infrastructure.models.trace_event_model import (
            CopilotTraceEventModel,
        )

        conn = db_engine.connect()
        txn = conn.begin()
        session = sessionmaker(autocommit=False, autoflush=False, bind=conn)()

        try:
            register_subscribers(repo_factory=lambda: TraceEventRepository(session))

            tenant = uuid4()
            event = SuggestionShown.create(
                tenant_id=tenant,
                user_id=None,
                conversation_id=None,
                current_route="offer-studio",
                suggestion_ids=[uuid4(), uuid4()],
                provider_breakdown={"offer": 2},
                latency_ms=7,
            )
            EventBus.publish(event)
            session.flush()

            rows = (
                session.query(CopilotTraceEventModel).filter_by(tenant_id=tenant, event_type="suggestion_shown").all()
            )
            assert len(rows) >= 1
            row = rows[0]
            assert row.name == "offer-studio"
        finally:
            session.close()
            txn.rollback()
            conn.close()

    def test_suggestion_accepted_event_persists_trace_row(self, db_engine) -> None:
        """Publish SuggestionAccepted → row in copilot_trace_event."""
        from sqlalchemy.orm import sessionmaker

        from luana_core_copilot.domain.events import SuggestionAccepted
        from luana_core_copilot.observability.persistence.trace_event_repository import (
            TraceEventRepository,
        )
        from luana_core_copilot.observability.recording.domain_subscribers import (
            register_subscribers,
        )
        from luana_core_copilot.infrastructure.models.trace_event_model import (
            CopilotTraceEventModel,
        )

        conn = db_engine.connect()
        txn = conn.begin()
        session = sessionmaker(autocommit=False, autoflush=False, bind=conn)()

        try:
            register_subscribers(repo_factory=lambda: TraceEventRepository(session))

            tenant = uuid4()
            sid = uuid4()
            event = SuggestionAccepted.create(
                tenant_id=tenant,
                user_id=None,
                conversation_id=None,
                suggestion_id=sid,
                source_module="offer",
                category="action",
            )
            EventBus.publish(event)
            session.flush()

            rows = (
                session.query(CopilotTraceEventModel)
                .filter_by(tenant_id=tenant, event_type="suggestion_accepted")
                .all()
            )
            assert len(rows) >= 1
            row = rows[0]
            assert row.name == "offer"
        finally:
            session.close()
            txn.rollback()
            conn.close()

    def test_db_failure_does_not_propagate_exception(self) -> None:
        """Subscriber best-effort: DB write fails → no exception bubbles out."""
        from luana_core_copilot.domain.events import SuggestionShown
        from luana_core_copilot.observability.recording.domain_subscribers import (
            register_subscribers,
        )

        failing_repo = MagicMock()
        failing_repo.add.side_effect = RuntimeError("DB down")
        failing_repo.db = None

        register_subscribers(repo_factory=lambda: failing_repo)

        tenant = uuid4()
        event = SuggestionShown.create(
            tenant_id=tenant,
            user_id=None,
            conversation_id=None,
            current_route="offer-studio",
            suggestion_ids=[uuid4()],
            provider_breakdown={"offer": 1},
            latency_ms=3,
        )
        # Must not raise
        EventBus.publish(event)
