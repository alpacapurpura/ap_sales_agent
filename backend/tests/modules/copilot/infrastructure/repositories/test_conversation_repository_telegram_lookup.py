"""Tests for ``ConversationRepository.get_or_create_by_channel`` (PI-5 PR-2).

D-PI5-007: 1 conversation per ``(tenant_id, user_id, channel_type,
channel_chat_id)`` quadruple. Idempotent — second call with same keys
returns the same row. Tenant-scoped — same chat_id under a different
tenant creates a NEW row (no cross-tenant leak). Soft-deleted rows are
treated as missing.

Q5 PM-resolved (CONTRACT § 16): UNIQUE constraint deferred to S5 PR-5.
The repository today uses optimistic SELECT-then-INSERT — at MVP
Telegram volume the race window is statistically negligible. These
tests verify the deterministic single-thread behaviour.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from src.modules.copilot.infrastructure.repositories.conversation_repository import (
    ConversationRepository,
)


# ── Idempotency ─────────────────────────────────────────────────────────


def test_get_or_create_by_channel_creates_then_returns_same_row(db) -> None:
    repo = ConversationRepository(db)
    tenant_id = uuid4()
    user_id = uuid4()

    first = repo.get_or_create_by_channel(
        tenant_id=tenant_id,
        user_id=user_id,
        channel_type="telegram",
        channel_chat_id="123456",
    )
    db.commit()
    assert first.id is not None
    assert first.channel_type == "telegram"
    assert first.channel_chat_id == "123456"
    assert first.tenant_id == tenant_id
    assert first.user_id == user_id

    second = repo.get_or_create_by_channel(
        tenant_id=tenant_id,
        user_id=user_id,
        channel_type="telegram",
        channel_chat_id="123456",
    )
    assert second.id == first.id, "second call must return the same conversation row"


def test_get_or_create_by_channel_three_calls_idempotent(db) -> None:
    """Three back-to-back calls produce one row."""
    repo = ConversationRepository(db)
    tenant_id = uuid4()
    user_id = uuid4()

    ids = set()
    for _ in range(3):
        conv = repo.get_or_create_by_channel(
            tenant_id=tenant_id,
            user_id=user_id,
            channel_type="telegram",
            channel_chat_id="999",
        )
        db.commit()
        ids.add(conv.id)

    assert len(ids) == 1, f"expected 1 unique conversation id across 3 calls, got {ids}"


# ── Cross-tenant isolation ──────────────────────────────────────────────


def test_get_or_create_by_channel_isolates_across_tenants(db) -> None:
    """Same chat_id under different tenants → distinct conversations."""
    repo = ConversationRepository(db)
    tenant_a = uuid4()
    tenant_b = uuid4()
    user_a = uuid4()
    user_b = uuid4()

    conv_a = repo.get_or_create_by_channel(
        tenant_id=tenant_a,
        user_id=user_a,
        channel_type="telegram",
        channel_chat_id="42",
    )
    db.commit()

    conv_b = repo.get_or_create_by_channel(
        tenant_id=tenant_b,
        user_id=user_b,
        channel_type="telegram",
        channel_chat_id="42",
    )
    db.commit()

    assert conv_a.id != conv_b.id, "cross-tenant SAME chat_id must create distinct conversations"
    assert conv_a.tenant_id == tenant_a
    assert conv_b.tenant_id == tenant_b


# ── Cross-user isolation (same tenant) ──────────────────────────────────


def test_get_or_create_by_channel_isolates_across_users_same_tenant(db) -> None:
    """Same chat_id under different users in the same tenant → distinct conversations.

    The composite key includes user_id so two operators in one workspace
    using the same Telegram bot do not share state.
    """
    repo = ConversationRepository(db)
    tenant_id = uuid4()
    user_a = uuid4()
    user_b = uuid4()

    conv_a = repo.get_or_create_by_channel(
        tenant_id=tenant_id,
        user_id=user_a,
        channel_type="telegram",
        channel_chat_id="77",
    )
    db.commit()

    conv_b = repo.get_or_create_by_channel(
        tenant_id=tenant_id,
        user_id=user_b,
        channel_type="telegram",
        channel_chat_id="77",
    )
    db.commit()

    assert conv_a.id != conv_b.id


# ── Soft-delete handling ────────────────────────────────────────────────


def test_get_or_create_by_channel_soft_deleted_row_creates_new(db) -> None:
    """A soft-deleted (``deleted_at IS NOT NULL``) row is treated as missing."""
    repo = ConversationRepository(db)
    tenant_id = uuid4()
    user_id = uuid4()

    first = repo.get_or_create_by_channel(
        tenant_id=tenant_id,
        user_id=user_id,
        channel_type="telegram",
        channel_chat_id="500",
    )
    db.commit()
    first_id = first.id

    # Soft-delete the existing row.
    first.deleted_at = datetime.now(UTC)
    db.flush()
    db.commit()

    second = repo.get_or_create_by_channel(
        tenant_id=tenant_id,
        user_id=user_id,
        channel_type="telegram",
        channel_chat_id="500",
    )
    db.commit()

    assert second.id != first_id, "soft-deleted row must NOT be returned — new row required"
    assert second.deleted_at is None
