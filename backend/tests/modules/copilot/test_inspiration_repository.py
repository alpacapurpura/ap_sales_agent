"""Tests for ``CopilotInspirationRepository`` — F4 url contextual cache."""

from __future__ import annotations

from uuid import uuid4

import pytest

from luana_core_copilot.infrastructure.repositories.inspiration_repository import (
    CopilotInspirationRepository,
)


@pytest.fixture
def repo(db):
    return CopilotInspirationRepository(db)


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def conversation_id():
    return uuid4()


def _make(repo, *, tenant_id, conversation_id, slug, url=None, why="", score=0.7):
    return repo.upsert(
        tenant_id=tenant_id,
        conversation_id=conversation_id,
        slug=slug,
        url=url or f"https://{slug}.example.com",
        why=why,
        domain=f"{slug}.example.com",
        title=f"Title {slug}",
        summary=f"Summary {slug}",
        sub_elements={"testimonials": [], "ctas": []},
        brand_relevance_score=score,
        content_md=f"# {slug}\nbody",
        og_image=None,
    )


class TestUpsert:
    def test_first_call_inserts(self, repo, db, tenant_id, conversation_id) -> None:
        row = _make(repo, tenant_id=tenant_id, conversation_id=conversation_id, slug="comp1")
        db.commit()
        assert row.id is not None
        assert row.slug == "comp1"
        assert float(row.brand_relevance_score) == pytest.approx(0.7, abs=0.01)

    def test_second_call_updates_in_place(
        self,
        repo,
        db,
        tenant_id,
        conversation_id,
    ) -> None:
        first = _make(repo, tenant_id=tenant_id, conversation_id=conversation_id, slug="x")
        db.commit()
        second = repo.upsert(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            slug="x",
            url="https://x.example.com",
            why="updated reason",
            domain="x.example.com",
            title="New Title",
            summary="New Summary",
            sub_elements={"testimonials": ["t1"]},
            brand_relevance_score=0.9,
            content_md="# new",
            og_image=None,
        )
        db.commit()
        assert second.id == first.id
        assert second.summary == "New Summary"
        assert float(second.brand_relevance_score) == pytest.approx(0.9, abs=0.01)


class TestTenantIsolation:
    def test_get_by_slug_isolated_per_tenant(self, repo, db, conversation_id) -> None:
        tenant_a = uuid4()
        tenant_b = uuid4()
        _make(repo, tenant_id=tenant_a, conversation_id=conversation_id, slug="x")
        db.commit()
        assert repo.get_by_slug(tenant_id=tenant_a, conversation_id=conversation_id, slug="x") is not None
        assert repo.get_by_slug(tenant_id=tenant_b, conversation_id=conversation_id, slug="x") is None

    def test_list_isolated_per_conversation(self, repo, db, tenant_id) -> None:
        conv_a = uuid4()
        conv_b = uuid4()
        _make(repo, tenant_id=tenant_id, conversation_id=conv_a, slug="a")
        _make(repo, tenant_id=tenant_id, conversation_id=conv_b, slug="b")
        db.commit()
        rows_a = repo.list_active_for_conversation(
            tenant_id=tenant_id,
            conversation_id=conv_a,
        )
        assert len(rows_a) == 1
        assert rows_a[0].slug == "a"


class TestListAndCount:
    def test_list_orders_newest_first(
        self,
        repo,
        db,
        tenant_id,
        conversation_id,
    ) -> None:
        for slug in ("a", "b", "c"):
            _make(repo, tenant_id=tenant_id, conversation_id=conversation_id, slug=slug)
            db.commit()
        rows = repo.list_active_for_conversation(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
        )
        # Newest first: c, b, a
        assert [r.slug for r in rows] == ["c", "b", "a"]

    def test_list_respects_limit(self, repo, db, tenant_id, conversation_id) -> None:
        for slug in ("a", "b", "c", "d", "e", "f"):
            _make(repo, tenant_id=tenant_id, conversation_id=conversation_id, slug=slug)
            db.commit()
        rows = repo.list_active_for_conversation(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            limit=3,
        )
        assert len(rows) == 3

    def test_count_for_conversation(self, repo, db, tenant_id, conversation_id) -> None:
        for slug in ("a", "b", "c"):
            _make(repo, tenant_id=tenant_id, conversation_id=conversation_id, slug=slug)
            db.commit()
        assert (
            repo.count_for_conversation(
                tenant_id=tenant_id,
                conversation_id=conversation_id,
            )
            == 3
        )


class TestFifoCap:
    def test_delete_oldest_beyond_cap_keeps_newest(
        self,
        repo,
        db,
        tenant_id,
        conversation_id,
    ) -> None:
        for slug in ("a", "b", "c", "d", "e", "f", "g"):
            _make(repo, tenant_id=tenant_id, conversation_id=conversation_id, slug=slug)
            db.commit()
        removed = repo.delete_oldest_beyond_cap(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            cap=5,
        )
        db.commit()
        assert removed == 2
        rows = repo.list_active_for_conversation(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            limit=10,
        )
        assert {r.slug for r in rows} == {"c", "d", "e", "f", "g"}
