"""Tests for edition-aware filtering on ``OfferAssetRepository`` (Phase 3).

Contract:

- ``list(..., edition_id=None)`` → legacy behaviour: returns every live asset
  for the offer (offer-level + all edition-scoped + shared). Keeps existing
  callers working without flipping their semantics.
- ``list(..., edition_id=X)`` → returns assets that belong to edition ``X``
  (``edition_id = X``) OR are shared across editions
  (``shared_across_editions = TRUE``). Offer-level-only rows (``edition_id
  IS NULL`` and not shared) are excluded — they belong to a different
  visibility bucket.

The explicit ``edition_id`` parameter avoids relying on a sentinel value
inside the repository; callers that want "offer-level only" can query
through ``get_by_id`` or use the (future) dedicated listing.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from luana_core_offer_studio.domain.assets import OfferAsset
from luana_core_offer_studio.domain.enums import AssetSource, AssetStatus, AssetType
from luana_core_offer_studio.infrastructure.repositories.offer_asset_repository import (
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


def _asset(
    tenant_id: uuid.UUID,
    offer_id: uuid.UUID,
    *,
    name: str,
    edition_id: uuid.UUID | None = None,
    shared: bool = False,
) -> OfferAsset:
    return OfferAsset(
        tenant_id=tenant_id,
        offer_id=offer_id,
        edition_id=edition_id,
        shared_across_editions=shared,
        name=name,
        type=AssetType.FLYER,
        source=AssetSource.EXTERNAL,
        status=AssetStatus.READY,
    )


class TestEditionFiltering:
    def test_edition_scoped_list_excludes_other_editions(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ):
        offer_id = _make_offer(db, tenant_a)
        repo = OfferAssetRepository(db)

        edition_a = uuid.uuid4()
        edition_b = uuid.uuid4()

        repo.create(_asset(tenant_a, offer_id, name="A_only", edition_id=edition_a))
        repo.create(_asset(tenant_a, offer_id, name="B_only", edition_id=edition_b))
        repo.create(_asset(tenant_a, offer_id, name="offer_level"))  # edition_id NULL

        items, total = repo.list(tenant_a, offer_id, edition_id=edition_a)
        names = {a.name for a in items}

        assert names == {"A_only"}
        assert total == 1

    def test_shared_asset_shows_in_every_edition_listing(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ):
        offer_id = _make_offer(db, tenant_a)
        repo = OfferAssetRepository(db)

        edition_a = uuid.uuid4()
        edition_b = uuid.uuid4()

        repo.create(_asset(tenant_a, offer_id, name="A_only", edition_id=edition_a))
        repo.create(
            _asset(
                tenant_a,
                offer_id,
                name="shared_from_b",
                edition_id=edition_b,
                shared=True,
            ),
        )

        items_a, total_a = repo.list(tenant_a, offer_id, edition_id=edition_a)
        assert {a.name for a in items_a} == {"A_only", "shared_from_b"}
        assert total_a == 2

        items_b, total_b = repo.list(tenant_a, offer_id, edition_id=edition_b)
        assert {a.name for a in items_b} == {"shared_from_b"}
        assert total_b == 1

    def test_legacy_call_without_edition_returns_everything(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ):
        """No ``edition_id`` argument → unchanged behaviour, returns all offer assets."""
        offer_id = _make_offer(db, tenant_a)
        repo = OfferAssetRepository(db)

        edition_a = uuid.uuid4()
        repo.create(_asset(tenant_a, offer_id, name="A_only", edition_id=edition_a))
        repo.create(_asset(tenant_a, offer_id, name="offer_level"))

        items, total = repo.list(tenant_a, offer_id)

        assert {a.name for a in items} == {"A_only", "offer_level"}
        assert total == 2

    def test_roundtrip_preserves_edition_fields(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ):
        offer_id = _make_offer(db, tenant_a)
        repo = OfferAssetRepository(db)
        edition_id = uuid.uuid4()

        created = repo.create(
            _asset(
                tenant_a,
                offer_id,
                name="scoped",
                edition_id=edition_id,
                shared=False,
            ),
        )

        fetched = repo.get_by_id(tenant_a, offer_id, created.id)

        assert fetched is not None
        assert fetched.edition_id == edition_id
        assert fetched.shared_across_editions is False
        assert fetched.is_edition_scoped is True
