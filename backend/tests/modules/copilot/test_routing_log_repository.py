"""Tests for RoutingLogRepository — insert + query by tenant/time."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.modules.copilot.infrastructure.models.routing_log_model import RoutingLogModel
from src.modules.copilot.infrastructure.repositories.routing_log_repository import (
    RoutingLogRepository,
)


@pytest.fixture
def repo(db):
    return RoutingLogRepository(db)


@pytest.fixture
def tenant_id():
    return uuid4()


class TestRoutingLogInsert:
    """Routing log rows can be inserted with all required fields."""

    def test_insert_returns_model_with_id(self, repo, db, tenant_id) -> None:
        """insert() returns a RoutingLogModel with an auto-generated id."""
        conv_id = uuid4()
        msg_id = uuid4()

        row = repo.insert(
            tenant_id=tenant_id,
            conversation_id=conv_id,
            message_id=msg_id,
            role_selected="fast",
            classifier_used="rule",
            reason="keyword_compare_reason",
            confidence=0.92,
            user_msg_length=45,
            tools_available=3,
        )
        db.commit()

        assert row.id is not None
        assert row.tenant_id == tenant_id
        assert row.role_selected == "fast"
        assert row.classifier_used == "rule"

    def test_insert_confidence_none_allowed(self, repo, db, tenant_id) -> None:
        """confidence can be None for DEFAULT classifier."""
        row = repo.insert(
            tenant_id=tenant_id,
            conversation_id=uuid4(),
            message_id=uuid4(),
            role_selected="nano",
            classifier_used="default",
            reason="short_msg_no_tools",
            confidence=None,
            user_msg_length=10,
            tools_available=0,
        )
        db.commit()
        assert row.confidence is None


class TestRoutingLogQuery:
    """Query methods filter by tenant and time."""

    def test_list_by_tenant_returns_own_rows(self, repo, db, tenant_id) -> None:
        """list_by_tenant() returns rows for the given tenant."""
        repo.insert(
            tenant_id=tenant_id,
            conversation_id=uuid4(),
            message_id=uuid4(),
            role_selected="fast",
            classifier_used="rule",
            reason="test",
            confidence=0.8,
            user_msg_length=100,
            tools_available=2,
        )
        db.commit()

        rows = repo.list_by_tenant(tenant_id=tenant_id)
        assert len(rows) >= 1
        assert all(r.tenant_id == tenant_id for r in rows)

    def test_list_by_tenant_excludes_other_tenant(self, repo, db, tenant_id) -> None:
        """list_by_tenant() never returns rows from another tenant."""
        other = uuid4()
        repo.insert(
            tenant_id=other,
            conversation_id=uuid4(),
            message_id=uuid4(),
            role_selected="agent",
            classifier_used="llm",
            reason="test",
            confidence=0.5,
            user_msg_length=200,
            tools_available=5,
        )
        db.commit()

        rows = repo.list_by_tenant(tenant_id=tenant_id)
        assert all(r.tenant_id != other for r in rows)

    def test_list_by_conversation(self, repo, db, tenant_id) -> None:
        """list_by_conversation() returns rows for a specific conversation."""
        conv_id = uuid4()
        other_conv = uuid4()

        repo.insert(
            tenant_id=tenant_id,
            conversation_id=conv_id,
            message_id=uuid4(),
            role_selected="fast",
            classifier_used="rule",
            reason="test",
            confidence=0.7,
            user_msg_length=50,
            tools_available=1,
        )
        repo.insert(
            tenant_id=tenant_id,
            conversation_id=other_conv,
            message_id=uuid4(),
            role_selected="nano",
            classifier_used="default",
            reason="test2",
            confidence=None,
            user_msg_length=20,
            tools_available=0,
        )
        db.commit()

        rows = repo.list_by_conversation(tenant_id=tenant_id, conversation_id=conv_id)
        assert len(rows) == 1
        assert rows[0].conversation_id == conv_id
