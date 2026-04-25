"""F5 — ConversationDataAccessProvider tests (own copilot module, no discovery)."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

import pytest

from src.modules.copilot.application.data_access.conversation import (
    ConversationDataAccessProvider,
)
from src.modules.copilot.domain.ports import DataQueryPlan
from src.modules.copilot.infrastructure.models.conversation_model import (
    CopilotConversationModel,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

TENANT_X = uuid.UUID("c0debabe-0000-4000-8000-000000000001")
USER_X = uuid.UUID("c0debabe-1111-4000-8000-000000000001")


def _make_conv(*, updated_at: datetime, archived: bool = False) -> CopilotConversationModel:
    conv = CopilotConversationModel(
        id=uuid.uuid4(),
        tenant_id=TENANT_X,
        user_id=USER_X,
        title="Conv",
        messages=[],
        created_at=updated_at,
        updated_at=updated_at,
        message_count=0,
        total_tokens=0,
        title_auto_generated=False,
    )
    if archived:
        conv.archived_at = updated_at
    return conv


@pytest.fixture
def access(db: Session) -> ConversationDataAccessProvider:
    return ConversationDataAccessProvider(db_factory=lambda: db)


def test_supports_conversation_count_only(access: ConversationDataAccessProvider) -> None:
    assert access.supports("conversation_count") is True
    assert access.supports("offer_lookup") is False


@pytest.mark.asyncio
async def test_execute_counts_window(
    db: Session,
    access: ConversationDataAccessProvider,
) -> None:
    now = datetime.now(timezone.utc)
    db.add_all(
        [
            _make_conv(updated_at=now - timedelta(days=2)),
            _make_conv(updated_at=now - timedelta(hours=4)),
            _make_conv(updated_at=now - timedelta(days=30)),
        ],
    )
    db.flush()

    plan = DataQueryPlan(
        kind="conversation_count",
        filters={
            "since": now - timedelta(days=7),
            "until": now,
        },
    )
    result = await access.execute(tenant_id=TENANT_X, plan=plan, context={"db": db})
    assert result.metadata["count"] == 2
    assert result.metadata["kind"] == "conversation_count"


@pytest.mark.asyncio
async def test_execute_excludes_archived_by_default(
    db: Session,
    access: ConversationDataAccessProvider,
) -> None:
    now = datetime.now(timezone.utc)
    db.add_all(
        [
            _make_conv(updated_at=now - timedelta(days=1)),
            _make_conv(updated_at=now - timedelta(days=2), archived=True),
        ],
    )
    db.flush()

    plan = DataQueryPlan(
        kind="conversation_count",
        filters={"since": now - timedelta(days=7), "until": now},
    )
    result = await access.execute(tenant_id=TENANT_X, plan=plan, context={"db": db})
    assert result.metadata["count"] == 1


@pytest.mark.asyncio
async def test_execute_requires_since_and_until(
    db: Session,
    access: ConversationDataAccessProvider,
) -> None:
    plan = DataQueryPlan(kind="conversation_count", filters={})
    with pytest.raises(ValueError, match="since"):
        await access.execute(tenant_id=TENANT_X, plan=plan, context={"db": db})
