"""Tests for MessageRepository -- History + tenant isolation."""

import uuid

from src.modules.sales_agent.domain.enums import MessageSender
from src.modules.sales_agent.domain.message import Message
from src.modules.sales_agent.infrastructure.repositories.message_repository import (
    MessageRepository,
)


def _make_message(tenant_id: uuid.UUID, lead_id: uuid.UUID | None = None) -> Message:
    return Message(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        lead_id=lead_id or uuid.uuid4(),
        sender_type=MessageSender.USER,
        content="Hello",
        channel="whatsapp",
        external_id=str(uuid.uuid4()),
        metadata_info={},
    )


class TestMessageRepository:
    def test_get_history_filters_by_tenant(
        self,
        db,
        seed_tenant,
        tenant_id,
        seed_other_tenant,
        other_tenant_id,
    ):
        repo = MessageRepository(db)
        lead_id = uuid.uuid4()

        # Message for tenant A
        msg_a = _make_message(tenant_id, lead_id=lead_id)
        repo.create(msg_a)

        # Message for tenant B with same lead_id (hypothetical collision or attacker)
        msg_b = _make_message(other_tenant_id, lead_id=lead_id)
        repo.create(msg_b)

        # Should only get tenant A messages
        history_a = repo.get_history(lead_id, tenant_id=tenant_id)
        assert len(history_a) == 1
        assert history_a[0].id == msg_a.id

        # Should only get tenant B messages
        history_b = repo.get_history(lead_id, tenant_id=other_tenant_id)
        assert len(history_b) == 1
        assert history_b[0].id == msg_b.id
