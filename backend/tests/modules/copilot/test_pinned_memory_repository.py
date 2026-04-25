"""Tests for ``CopilotPinnedMemoryRepository`` — upsert + tenant isolation."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.modules.copilot.infrastructure.repositories.pinned_memory_repository import (
    CopilotPinnedMemoryRepository,
)


@pytest.fixture
def repo(db):
    return CopilotPinnedMemoryRepository(db)


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def user_id():
    return uuid4()


class TestUpsert:
    """upsert() inserts on first call, updates on second."""

    def test_first_call_inserts(self, repo, db, tenant_id, user_id) -> None:
        row = repo.upsert(
            tenant_id=tenant_id,
            user_id=user_id,
            path="/memories/competitor.md",
            content="hook + body",
        )
        db.commit()
        assert row.id is not None
        assert row.path == "/memories/competitor.md"
        assert row.content == "hook + body"

    def test_second_call_updates_content_in_place(
        self,
        repo,
        db,
        tenant_id,
        user_id,
    ) -> None:
        first = repo.upsert(
            tenant_id=tenant_id,
            user_id=user_id,
            path="/memories/x.md",
            content="v1",
        )
        db.commit()
        second = repo.upsert(
            tenant_id=tenant_id,
            user_id=user_id,
            path="/memories/x.md",
            content="v2",
        )
        db.commit()
        assert second.id == first.id
        assert second.content == "v2"


class TestTenantIsolation:
    """Queries filter by tenant_id + user_id."""

    def test_get_isolated_per_tenant(self, repo, db, user_id) -> None:
        tenant_a = uuid4()
        tenant_b = uuid4()
        repo.upsert(
            tenant_id=tenant_a,
            user_id=user_id,
            path="/memories/x.md",
            content="A",
        )
        db.commit()
        assert repo.get(tenant_id=tenant_a, user_id=user_id, path="/memories/x.md") is not None
        assert repo.get(tenant_id=tenant_b, user_id=user_id, path="/memories/x.md") is None

    def test_list_for_user_filters_by_prefix(self, repo, db, tenant_id, user_id) -> None:
        repo.upsert(
            tenant_id=tenant_id,
            user_id=user_id,
            path="/memories/x.md",
            content="m",
        )
        repo.upsert(
            tenant_id=tenant_id,
            user_id=user_id,
            path="/notes/y.md",
            content="n",
        )
        db.commit()
        memories = repo.list_for_user(
            tenant_id=tenant_id,
            user_id=user_id,
            path_prefix="/memories/",
        )
        assert len(memories) == 1
        assert memories[0].path == "/memories/x.md"


class TestDelete:
    def test_delete_returns_true_when_row_removed(
        self,
        repo,
        db,
        tenant_id,
        user_id,
    ) -> None:
        repo.upsert(
            tenant_id=tenant_id,
            user_id=user_id,
            path="/memories/x.md",
            content="m",
        )
        db.commit()
        assert repo.delete(tenant_id=tenant_id, user_id=user_id, path="/memories/x.md") is True
        assert repo.get(tenant_id=tenant_id, user_id=user_id, path="/memories/x.md") is None

    def test_delete_returns_false_when_row_missing(self, repo, tenant_id, user_id) -> None:
        assert repo.delete(tenant_id=tenant_id, user_id=user_id, path="/missing.md") is False
