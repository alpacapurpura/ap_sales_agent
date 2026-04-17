"""Domain tests for ``OfferAsset.edition_id`` + ``shared_across_editions`` (Phase 3).

Asset scoping rules:

- ``edition_id IS NULL`` ⇒ offer-level asset (default, pre-Phase-3 behaviour).
- ``edition_id`` set + ``shared_across_editions = False`` ⇒ asset visible
  ONLY inside that edition's gallery.
- ``edition_id`` set + ``shared_across_editions = True`` ⇒ asset visible
  inside every edition of the same offer (an edition-borne template
  that the creator chose to promote offer-wide).

The ``is_edition_scoped`` property encodes this in one place so repos,
services, and the clone flow don't each re-derive it.
"""

from __future__ import annotations

from uuid import uuid4

from src.modules.offer.domain.assets import OfferAsset
from src.modules.offer.domain.enums import AssetSource, AssetStatus, AssetType


def _make_asset(**overrides: object) -> OfferAsset:
    defaults: dict[str, object] = {
        "tenant_id": uuid4(),
        "offer_id": uuid4(),
        "name": "flyer.png",
        "type": AssetType.FLYER,
        "source": AssetSource.EXTERNAL,
        "status": AssetStatus.READY,
    }
    defaults.update(overrides)
    return OfferAsset(**defaults)  # type: ignore[arg-type]


class TestOfferAssetEditionBinding:
    def test_default_asset_is_offer_level(self) -> None:
        asset = _make_asset()
        assert asset.edition_id is None
        assert asset.shared_across_editions is False
        assert asset.is_edition_scoped is False

    def test_asset_with_edition_id_is_edition_scoped(self) -> None:
        asset = _make_asset(edition_id=uuid4())
        assert asset.is_edition_scoped is True

    def test_asset_with_edition_id_and_shared_is_not_edition_scoped(self) -> None:
        """A shared asset, even when born inside an edition, lives offer-wide."""
        asset = _make_asset(edition_id=uuid4(), shared_across_editions=True)
        assert asset.is_edition_scoped is False

    def test_asset_without_edition_id_cannot_be_edition_scoped(self) -> None:
        asset = _make_asset(shared_across_editions=True)
        assert asset.edition_id is None
        assert asset.is_edition_scoped is False
