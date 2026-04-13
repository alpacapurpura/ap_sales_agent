"""Tests for OfferAssetRepository.

Covers: CRUD, tenant isolation, soft-delete filtering, search + filters,
sorting, pagination, and counts.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from src.modules.offer.domain.assets import OfferAsset
from src.modules.offer.domain.enums import AssetSource, AssetStatus, AssetType
from src.modules.offer.infrastructure.repositories.offer_asset_repository import (
    OfferAssetRepository,
)
from tests.modules.offer.conftest import create_product_model

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def _make_offer(db: Session, tenant_id: uuid.UUID) -> uuid.UUID:
    model = create_product_model(tenant_id)
    db.add(model)
    db.flush()
    return model.id


def _build_asset(
    tenant_id: uuid.UUID,
    offer_id: uuid.UUID,
    *,
    name: str = "Asset",
    type_: AssetType = AssetType.FLYER,
    source: AssetSource = AssetSource.AI,
    status: AssetStatus = AssetStatus.DRAFT,
) -> OfferAsset:
    return OfferAsset(
        tenant_id=tenant_id,
        offer_id=offer_id,
        name=name,
        type=type_,
        source=source,
        status=status,
        editable_in_puck=(source == AssetSource.AI),
    )


class TestCreate:
    def test_create_roundtrip(self, db: Session, tenant_a: uuid.UUID):
        offer_id = _make_offer(db, tenant_a)
        repo = OfferAssetRepository(db)

        created = repo.create(
            _build_asset(tenant_a, offer_id, name="Flyer promo", source=AssetSource.AI)
        )

        assert created.id is not None
        assert created.tenant_id == tenant_a
        assert created.offer_id == offer_id
        assert created.name == "Flyer promo"
        assert created.type == AssetType.FLYER
        assert created.source == AssetSource.AI
        assert created.status == AssetStatus.DRAFT
        assert created.editable_in_puck is True
        assert created.metadata == {}

    def test_create_persists_metadata_and_prompt_params(
        self, db: Session, tenant_a: uuid.UUID
    ):
        offer_id = _make_offer(db, tenant_a)
        repo = OfferAssetRepository(db)

        asset = _build_asset(tenant_a, offer_id)
        asset.metadata = {"page_count": 3}
        asset.prompt_params = {"prompt": "hero image"}
        created = repo.create(asset)

        fetched = repo.get_by_id(tenant_a, offer_id, created.id)
        assert fetched is not None
        assert fetched.metadata == {"page_count": 3}
        assert fetched.prompt_params == {"prompt": "hero image"}


class TestGetById:
    def test_returns_none_when_missing(self, db: Session, tenant_a: uuid.UUID):
        offer_id = _make_offer(db, tenant_a)
        repo = OfferAssetRepository(db)

        assert repo.get_by_id(tenant_a, offer_id, uuid.uuid4()) is None

    def test_enforces_tenant_isolation(
        self, db: Session, tenant_a: uuid.UUID, tenant_b: uuid.UUID
    ):
        offer_a = _make_offer(db, tenant_a)
        repo = OfferAssetRepository(db)
        created = repo.create(_build_asset(tenant_a, offer_a))

        # Wrong tenant → cannot see it
        assert repo.get_by_id(tenant_b, offer_a, created.id) is None

    def test_excludes_soft_deleted(self, db: Session, tenant_a: uuid.UUID):
        offer_id = _make_offer(db, tenant_a)
        repo = OfferAssetRepository(db)
        created = repo.create(_build_asset(tenant_a, offer_id))

        assert repo.soft_delete(tenant_a, offer_id, created.id) is True
        assert repo.get_by_id(tenant_a, offer_id, created.id) is None


class TestList:
    def test_list_filters_by_tenant_and_offer(
        self, db: Session, tenant_a: uuid.UUID, tenant_b: uuid.UUID
    ):
        offer_a = _make_offer(db, tenant_a)
        offer_b = _make_offer(db, tenant_b)
        repo = OfferAssetRepository(db)

        repo.create(_build_asset(tenant_a, offer_a, name="A1"))
        repo.create(_build_asset(tenant_a, offer_a, name="A2"))
        repo.create(_build_asset(tenant_b, offer_b, name="B1"))

        items_a, total_a = repo.list(tenant_a, offer_a)
        assert total_a == 2
        assert {a.name for a in items_a} == {"A1", "A2"}

        items_b, total_b = repo.list(tenant_b, offer_b)
        assert total_b == 1
        assert items_b[0].name == "B1"

    def test_list_filters_by_type_and_source(self, db: Session, tenant_a: uuid.UUID):
        offer_id = _make_offer(db, tenant_a)
        repo = OfferAssetRepository(db)

        repo.create(
            _build_asset(
                tenant_a,
                offer_id,
                name="AI flyer",
                type_=AssetType.FLYER,
                source=AssetSource.AI,
            )
        )
        repo.create(
            _build_asset(
                tenant_a,
                offer_id,
                name="External video",
                type_=AssetType.VIDEO,
                source=AssetSource.EXTERNAL,
            )
        )

        items, total = repo.list(tenant_a, offer_id, type_=AssetType.VIDEO)
        assert total == 1
        assert items[0].name == "External video"

        items, total = repo.list(tenant_a, offer_id, source=AssetSource.AI)
        assert total == 1
        assert items[0].name == "AI flyer"

    def test_list_search_matches_name(self, db: Session, tenant_a: uuid.UUID):
        offer_id = _make_offer(db, tenant_a)
        repo = OfferAssetRepository(db)
        repo.create(_build_asset(tenant_a, offer_id, name="Promo de lanzamiento"))
        repo.create(_build_asset(tenant_a, offer_id, name="Testimonial"))

        items, total = repo.list(tenant_a, offer_id, search="lanzamiento")
        assert total == 1
        assert items[0].name == "Promo de lanzamiento"

    def test_list_pagination(self, db: Session, tenant_a: uuid.UUID):
        offer_id = _make_offer(db, tenant_a)
        repo = OfferAssetRepository(db)
        for i in range(5):
            repo.create(_build_asset(tenant_a, offer_id, name=f"Asset{i}"))

        page1, total = repo.list(tenant_a, offer_id, limit=2, offset=0)
        page2, _ = repo.list(tenant_a, offer_id, limit=2, offset=2)

        assert total == 5
        assert len(page1) == 2
        assert len(page2) == 2
        assert {a.id for a in page1}.isdisjoint({a.id for a in page2})

    def test_list_excludes_soft_deleted(self, db: Session, tenant_a: uuid.UUID):
        offer_id = _make_offer(db, tenant_a)
        repo = OfferAssetRepository(db)
        alive = repo.create(_build_asset(tenant_a, offer_id, name="alive"))
        doomed = repo.create(_build_asset(tenant_a, offer_id, name="doomed"))

        repo.soft_delete(tenant_a, offer_id, doomed.id)

        items, total = repo.list(tenant_a, offer_id)
        assert total == 1
        assert items[0].id == alive.id


class TestUpdate:
    def test_update_mutates_fields(self, db: Session, tenant_a: uuid.UUID):
        offer_id = _make_offer(db, tenant_a)
        repo = OfferAssetRepository(db)
        created = repo.create(_build_asset(tenant_a, offer_id))

        created.name = "Renamed"
        created.status = AssetStatus.READY
        created.file_url = "https://cdn/asset.png"
        created.size_bytes = 1234
        updated = repo.update(created)

        assert updated.name == "Renamed"
        assert updated.status == AssetStatus.READY
        assert updated.file_url == "https://cdn/asset.png"
        assert updated.size_bytes == 1234


class TestSoftDelete:
    def test_soft_delete_returns_false_when_missing(
        self, db: Session, tenant_a: uuid.UUID
    ):
        offer_id = _make_offer(db, tenant_a)
        repo = OfferAssetRepository(db)

        assert repo.soft_delete(tenant_a, offer_id, uuid.uuid4()) is False

    def test_soft_delete_enforces_tenant(
        self, db: Session, tenant_a: uuid.UUID, tenant_b: uuid.UUID
    ):
        offer_id = _make_offer(db, tenant_a)
        repo = OfferAssetRepository(db)
        created = repo.create(_build_asset(tenant_a, offer_id))

        # Wrong tenant cannot delete it
        assert repo.soft_delete(tenant_b, offer_id, created.id) is False
        # Still visible to rightful owner
        assert repo.get_by_id(tenant_a, offer_id, created.id) is not None


class TestCountByOffer:
    def test_counts_only_tenant_live(
        self, db: Session, tenant_a: uuid.UUID, tenant_b: uuid.UUID
    ):
        offer_a = _make_offer(db, tenant_a)
        offer_b = _make_offer(db, tenant_b)
        repo = OfferAssetRepository(db)

        repo.create(_build_asset(tenant_a, offer_a))
        repo.create(_build_asset(tenant_a, offer_a))
        deleted = repo.create(_build_asset(tenant_a, offer_a))
        repo.soft_delete(tenant_a, offer_a, deleted.id)
        repo.create(_build_asset(tenant_b, offer_b))

        assert repo.count_by_offer(tenant_a, offer_a) == 2
        assert repo.count_by_offer(tenant_b, offer_b) == 1
