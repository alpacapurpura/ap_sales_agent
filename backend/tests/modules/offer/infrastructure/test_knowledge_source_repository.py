"""Tests for KnowledgeSourceRepository.

Covers: CRUD, tenant isolation, soft-delete filtering, search/filter,
indexed counts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.modules.offer.domain.enums import (
    KnowledgeSourceStatus,
    KnowledgeSourceType,
)
from src.modules.offer.domain.knowledge_source import KnowledgeSource
from src.modules.offer.infrastructure.repositories.knowledge_source_repository import (
    KnowledgeSourceRepository,
)
from tests.modules.offer.conftest import create_product_model

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session


def _make_offer(db: Session, tenant_id: uuid.UUID) -> uuid.UUID:
    model = create_product_model(tenant_id)
    db.add(model)
    db.flush()
    return model.id


def _build_source(
    tenant_id: uuid.UUID,
    offer_id: uuid.UUID,
    *,
    name: str = "Source",
    type: KnowledgeSourceType = KnowledgeSourceType.PDF,
    status: KnowledgeSourceStatus = KnowledgeSourceStatus.QUEUED,
) -> KnowledgeSource:
    return KnowledgeSource(
        tenant_id=tenant_id,
        offer_id=offer_id,
        name=name,
        type=type,
        status=status,
    )


class TestCreate:
    def test_create_defaults(self, db: Session, tenant_a: uuid.UUID):
        offer_id = _make_offer(db, tenant_a)
        repo = KnowledgeSourceRepository(db)

        created = repo.create(_build_source(tenant_a, offer_id, name="Brochure"))

        assert created.id is not None
        assert created.name == "Brochure"
        assert created.status == KnowledgeSourceStatus.QUEUED
        assert created.indexed_chunk_count == 0
        assert created.qdrant_point_ids == []
        assert created.metadata == {}

    def test_create_persists_indexing_fields(self, db: Session, tenant_a: uuid.UUID):
        offer_id = _make_offer(db, tenant_a)
        repo = KnowledgeSourceRepository(db)

        src = _build_source(tenant_a, offer_id)
        src.indexed_chunk_count = 7
        src.qdrant_collection = "offer-kb"
        src.qdrant_point_ids = ["p1", "p2", "p3"]
        src.metadata = {"page_count": 42}

        created = repo.create(src)
        fetched = repo.get_by_id(tenant_a, offer_id, created.id)
        assert fetched is not None
        assert fetched.indexed_chunk_count == 7
        assert fetched.qdrant_collection == "offer-kb"
        assert fetched.qdrant_point_ids == ["p1", "p2", "p3"]
        assert fetched.metadata == {"page_count": 42}


class TestGetById:
    def test_tenant_isolation(
        self, db: Session, tenant_a: uuid.UUID, tenant_b: uuid.UUID
    ):
        offer_id = _make_offer(db, tenant_a)
        repo = KnowledgeSourceRepository(db)
        created = repo.create(_build_source(tenant_a, offer_id))

        assert repo.get_by_id(tenant_b, offer_id, created.id) is None

    def test_excludes_soft_deleted(self, db: Session, tenant_a: uuid.UUID):
        offer_id = _make_offer(db, tenant_a)
        repo = KnowledgeSourceRepository(db)
        created = repo.create(_build_source(tenant_a, offer_id))

        assert repo.soft_delete(tenant_a, offer_id, created.id) is True
        assert repo.get_by_id(tenant_a, offer_id, created.id) is None


class TestList:
    def test_list_filters_by_tenant_and_offer(
        self, db: Session, tenant_a: uuid.UUID, tenant_b: uuid.UUID
    ):
        offer_a = _make_offer(db, tenant_a)
        offer_b = _make_offer(db, tenant_b)
        repo = KnowledgeSourceRepository(db)

        repo.create(_build_source(tenant_a, offer_a, name="A1"))
        repo.create(_build_source(tenant_a, offer_a, name="A2"))
        repo.create(_build_source(tenant_b, offer_b, name="B1"))

        items_a = repo.list(tenant_a, offer_a)
        assert {s.name for s in items_a} == {"A1", "A2"}

        items_b = repo.list(tenant_b, offer_b)
        assert len(items_b) == 1
        assert items_b[0].name == "B1"

    def test_list_filter_by_type(self, db: Session, tenant_a: uuid.UUID):
        offer_id = _make_offer(db, tenant_a)
        repo = KnowledgeSourceRepository(db)
        repo.create(
            _build_source(tenant_a, offer_id, name="PDF", type=KnowledgeSourceType.PDF)
        )
        repo.create(
            _build_source(
                tenant_a,
                offer_id,
                name="Video",
                type=KnowledgeSourceType.VIDEO,
            )
        )

        items = repo.list(tenant_a, offer_id, type=KnowledgeSourceType.VIDEO)
        assert len(items) == 1
        assert items[0].name == "Video"

    def test_list_search_matches_url(self, db: Session, tenant_a: uuid.UUID):
        offer_id = _make_offer(db, tenant_a)
        repo = KnowledgeSourceRepository(db)
        src = _build_source(tenant_a, offer_id, type=KnowledgeSourceType.URL_ARTICLE)
        src.source_url = "https://blog.example/article-42"
        repo.create(src)
        repo.create(_build_source(tenant_a, offer_id, name="Other"))

        items = repo.list(tenant_a, offer_id, search="article-42")
        assert len(items) == 1


class TestUpdate:
    def test_update_status_and_chunks(self, db: Session, tenant_a: uuid.UUID):
        offer_id = _make_offer(db, tenant_a)
        repo = KnowledgeSourceRepository(db)
        created = repo.create(_build_source(tenant_a, offer_id))

        created.status = KnowledgeSourceStatus.INDEXED
        created.indexed_chunk_count = 10
        created.qdrant_point_ids = ["a", "b"]
        updated = repo.update(created)

        assert updated.status == KnowledgeSourceStatus.INDEXED
        assert updated.indexed_chunk_count == 10
        assert updated.qdrant_point_ids == ["a", "b"]


class TestCounts:
    def test_count_by_offer(self, db: Session, tenant_a: uuid.UUID):
        offer_id = _make_offer(db, tenant_a)
        repo = KnowledgeSourceRepository(db)
        repo.create(_build_source(tenant_a, offer_id))
        repo.create(_build_source(tenant_a, offer_id))
        doomed = repo.create(_build_source(tenant_a, offer_id))
        repo.soft_delete(tenant_a, offer_id, doomed.id)

        assert repo.count_by_offer(tenant_a, offer_id) == 2

    def test_count_indexed_by_offer(self, db: Session, tenant_a: uuid.UUID):
        offer_id = _make_offer(db, tenant_a)
        repo = KnowledgeSourceRepository(db)
        queued = repo.create(_build_source(tenant_a, offer_id))
        indexed = repo.create(_build_source(tenant_a, offer_id))
        indexed.status = KnowledgeSourceStatus.INDEXED
        repo.update(indexed)

        assert repo.count_indexed_by_offer(tenant_a, offer_id) == 1
        # sanity: the queued one still exists
        assert repo.get_by_id(tenant_a, offer_id, queued.id) is not None

    def test_tenant_isolation_on_counts(
        self, db: Session, tenant_a: uuid.UUID, tenant_b: uuid.UUID
    ):
        offer_a = _make_offer(db, tenant_a)
        offer_b = _make_offer(db, tenant_b)
        repo = KnowledgeSourceRepository(db)
        repo.create(_build_source(tenant_a, offer_a))
        repo.create(_build_source(tenant_b, offer_b))

        assert repo.count_by_offer(tenant_a, offer_a) == 1
        assert repo.count_by_offer(tenant_b, offer_b) == 1


class TestSoftDelete:
    def test_soft_delete_wrong_tenant_returns_false(
        self, db: Session, tenant_a: uuid.UUID, tenant_b: uuid.UUID
    ):
        offer_id = _make_offer(db, tenant_a)
        repo = KnowledgeSourceRepository(db)
        created = repo.create(_build_source(tenant_a, offer_id))

        assert repo.soft_delete(tenant_b, offer_id, created.id) is False
        assert repo.get_by_id(tenant_a, offer_id, created.id) is not None
