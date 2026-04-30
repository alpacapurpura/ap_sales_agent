"""TDD — SalesAgentObservabilityAdapter: read-only port impl.

Tests written RED first per ``tdd-mandatory.md``.
Uses SQLite in-memory via conftest for DB isolation.

PR-2-pure-expansion-providers / PI-2 S2.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from src.shared.domain.base_entity import Base


@pytest.fixture(scope="module")
def sa_engine():
    """In-memory SQLite engine with required tables."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    # Import models to register in Base.metadata
    from src.modules.sales_agent.infrastructure.models.enrollment_model import EnrollmentModel
    from src.modules.sales_agent.infrastructure.models.message_model import MessageModel

    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(sa_engine):
    """Function-scoped session with rollback cleanup."""
    connection = sa_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


_TENANT_A = uuid.uuid4()
_TENANT_B = uuid.uuid4()
_NOW = datetime.now(tz=timezone.utc)
_RECENT = _NOW - timedelta(hours=1)
_OLD = _NOW - timedelta(days=10)


def _make_message(session, tenant_id, user_id, created_at):
    from src.modules.sales_agent.infrastructure.models.message_model import MessageModel

    msg = MessageModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        role="user",
        content="hello",
    )
    # SQLite doesn't support server_default for test inserts, set manually
    msg.created_at = created_at
    session.add(msg)
    return msg


def _make_enrollment(session, tenant_id, offer_id, status, created_at, edition_id=None):
    from src.modules.sales_agent.infrastructure.models.enrollment_model import EnrollmentModel

    enrollment = EnrollmentModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        offer_id=offer_id,
        contact_id=uuid.uuid4(),
        status=status,
        edition_id=edition_id,
    )
    enrollment.created_at = created_at
    session.add(enrollment)
    return enrollment


class TestCountLeadsSince:
    def test_count_leads_since_filters_by_tenant_and_date(self, db_session) -> None:
        """Count distinct user_ids for tenant_a from _RECENT onward only."""
        from src.modules.sales_agent.application.services.observability_adapter import (
            SalesAgentObservabilityAdapter,
        )

        user_a1 = uuid.uuid4()
        user_a2 = uuid.uuid4()
        user_b = uuid.uuid4()

        # tenant_a: 2 recent messages (distinct users) + 1 old
        _make_message(db_session, _TENANT_A, user_a1, _RECENT)
        _make_message(db_session, _TENANT_A, user_a2, _RECENT)
        _make_message(db_session, _TENANT_A, user_a1, _OLD)  # same user, old — not counted
        # tenant_b: 1 recent — should not affect tenant_a count
        _make_message(db_session, _TENANT_B, user_b, _RECENT)
        db_session.flush()

        adapter = SalesAgentObservabilityAdapter(db_session)
        count = adapter.count_leads_since(_TENANT_A, since=_RECENT - timedelta(minutes=1))

        assert count == 2, f"Expected 2 distinct leads for tenant_a, got {count}"

    def test_count_leads_since_tenant_b_not_leaking(self, db_session) -> None:
        """tenant_b messages do not bleed into tenant_a counts."""
        from src.modules.sales_agent.application.services.observability_adapter import (
            SalesAgentObservabilityAdapter,
        )

        user_b = uuid.uuid4()
        _make_message(db_session, _TENANT_B, user_b, _RECENT)
        db_session.flush()

        adapter = SalesAgentObservabilityAdapter(db_session)
        count = adapter.count_leads_since(_TENANT_A, since=_RECENT - timedelta(minutes=1))
        assert count == 0


class TestListEnrollmentsByStatus:
    def test_list_enrollments_by_status_filters(self, db_session) -> None:
        """Returns only enrollments matching requested statuses."""
        from src.modules.sales_agent.application.services.observability_adapter import (
            SalesAgentObservabilityAdapter,
        )

        offer = uuid.uuid4()
        _make_enrollment(db_session, _TENANT_A, offer, "payment_pending", _OLD)
        _make_enrollment(db_session, _TENANT_A, offer, "enrolled", _RECENT)
        _make_enrollment(db_session, _TENANT_A, offer, "waitlist", _RECENT)
        _make_enrollment(db_session, _TENANT_B, offer, "payment_pending", _OLD)
        db_session.flush()

        adapter = SalesAgentObservabilityAdapter(db_session)
        results = adapter.list_enrollments_by_status(_TENANT_A, statuses=("payment_pending",))

        assert len(results) == 1
        assert results[0].status == "payment_pending"

    def test_list_enrollments_empty_statuses_returns_empty(self, db_session) -> None:
        """Empty statuses tuple returns []."""
        from src.modules.sales_agent.application.services.observability_adapter import (
            SalesAgentObservabilityAdapter,
        )

        adapter = SalesAgentObservabilityAdapter(db_session)
        results = adapter.list_enrollments_by_status(_TENANT_A, statuses=())
        assert results == []


class TestAdapterProtocol:
    def test_adapter_implements_port_protocol(self) -> None:
        """Adapter is an instance of SalesAgentObservabilityPort."""
        from sqlalchemy.orm import Session
        from unittest.mock import MagicMock

        from src.modules.sales_agent.application.services.observability_adapter import (
            SalesAgentObservabilityAdapter,
        )
        from src.shared.links.ports.sales_agent import SalesAgentObservabilityPort

        adapter = SalesAgentObservabilityAdapter(MagicMock(spec=Session))
        assert isinstance(adapter, SalesAgentObservabilityPort)
