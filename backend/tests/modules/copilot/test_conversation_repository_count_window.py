"""F5 — ConversationRepository.count_window (date window) tests."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

import pytest

from src.modules.copilot.infrastructure.models.conversation_model import (
    CopilotConversationModel,
)
from src.modules.copilot.infrastructure.repositories.conversation_repository import (
    ConversationRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

TENANT_X = uuid.UUID("c001ab1e-0000-4000-8000-000000000001")
TENANT_Y = uuid.UUID("c001ab1e-0000-4000-8000-000000000002")
USER_X = uuid.UUID("c001ab1e-1111-4000-8000-000000000001")


def _make_conv(
    *,
    tenant_id: uuid.UUID,
    updated_at: datetime,
    title: str | None = None,
) -> CopilotConversationModel:
    return CopilotConversationModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=USER_X,
        title=title,
        messages=[],
        created_at=updated_at,
        updated_at=updated_at,
        message_count=0,
        total_tokens=0,
        title_auto_generated=False,
    )


@pytest.fixture
def conv_seed(db: Session) -> dict[str, uuid.UUID]:
    now = datetime.now(timezone.utc)
    inside = _make_conv(
        tenant_id=TENANT_X,
        updated_at=now - timedelta(days=2),
        title="Conversación reciente",
    )
    inside_no_title = _make_conv(
        tenant_id=TENANT_X,
        updated_at=now - timedelta(hours=4),
    )
    outside = _make_conv(
        tenant_id=TENANT_X,
        updated_at=now - timedelta(days=30),
        title="Vieja",
    )
    archived = _make_conv(
        tenant_id=TENANT_X,
        updated_at=now - timedelta(days=1),
        title="Archivada",
    )
    archived.archived_at = now - timedelta(hours=1)
    other_tenant = _make_conv(
        tenant_id=TENANT_Y,
        updated_at=now - timedelta(days=1),
        title="Otra marca",
    )
    db.add_all([inside, inside_no_title, outside, archived, other_tenant])
    db.flush()
    return {
        "inside": inside.id,
        "inside_no_title": inside_no_title.id,
        "outside": outside.id,
        "archived": archived.id,
        "other_tenant": other_tenant.id,
    }


def test_count_window_filters_by_tenant_and_window(
    db: Session,
    conv_seed: dict[str, uuid.UUID],
) -> None:
    repo = ConversationRepository(db)
    now = datetime.now(timezone.utc)
    count = repo.count_window(
        tenant_id=TENANT_X,
        since=now - timedelta(days=7),
        until=now,
    )
    # inside + inside_no_title — archived excluded; outside excluded
    assert count == 2


def test_count_window_excludes_archived(
    db: Session,
    conv_seed: dict[str, uuid.UUID],
) -> None:
    repo = ConversationRepository(db)
    now = datetime.now(timezone.utc)
    count_with_archived = repo.count_window(
        tenant_id=TENANT_X,
        since=now - timedelta(days=7),
        until=now,
        include_archived=True,
    )
    assert count_with_archived == 3  # adds archived row


def test_count_window_other_tenant_isolated(
    db: Session,
    conv_seed: dict[str, uuid.UUID],
) -> None:
    repo = ConversationRepository(db)
    now = datetime.now(timezone.utc)
    count_y = repo.count_window(
        tenant_id=TENANT_Y,
        since=now - timedelta(days=7),
        until=now,
    )
    assert count_y == 1


def test_count_window_zero_when_empty(db: Session) -> None:
    repo = ConversationRepository(db)
    now = datetime.now(timezone.utc)
    count = repo.count_window(
        tenant_id=TENANT_X,
        since=now - timedelta(hours=1),
        until=now,
    )
    assert count == 0
