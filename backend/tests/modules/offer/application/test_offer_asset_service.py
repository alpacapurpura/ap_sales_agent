"""Unit tests for OfferAssetService — upload/generate/list/delete flows."""

from __future__ import annotations

from io import BytesIO
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from src.modules.offer.application.services.offer_asset_service import (
    OfferAssetService,
)
from src.modules.offer.domain.assets import OfferAsset
from src.modules.offer.domain.enums import AssetSource, AssetStatus, AssetType
from src.modules.offer.domain.exceptions import AssetNotFoundError


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def offer_id():
    return uuid4()


@pytest.fixture
def asset_repo():
    return MagicMock()


@pytest.fixture
def file_storage():
    port = MagicMock()
    port.upload.return_value = ("https://cdn.example/file.pdf", 1024)
    port.get_download_stream.return_value = BytesIO(b"bytes")
    return port


@pytest.fixture
def event_bus():
    return MagicMock()


@pytest.fixture
def service(asset_repo, file_storage, event_bus):
    return OfferAssetService(
        asset_repo=asset_repo,
        file_storage=file_storage,
        event_bus=event_bus,
    )


def _make_asset_mock(
    *,
    tenant_id,
    offer_id,
    asset_type=AssetType.DOCUMENT,
    source=AssetSource.EXTERNAL,
    status=AssetStatus.READY,
):
    m = MagicMock(spec=OfferAsset)
    m.id = uuid4()
    m.tenant_id = tenant_id
    m.offer_id = offer_id
    m.type = asset_type
    m.source = source
    m.status = status
    return m


# ------------------------------------------------------------------- upload


def test_upload_asset_stores_file_and_persists_row(
    service, asset_repo, file_storage, tenant_id, offer_id
):
    created = _make_asset_mock(tenant_id=tenant_id, offer_id=offer_id)
    asset_repo.create.return_value = created

    result = service.upload_asset(
        tenant_id=tenant_id,
        offer_id=offer_id,
        file_bytes=b"raw pdf bytes",
        filename="brief.pdf",
        type=AssetType.DOCUMENT,
        mime_type="application/pdf",
    )

    assert result is created
    file_storage.upload.assert_called_once()
    asset_repo.create.assert_called_once()
    passed_asset = asset_repo.create.call_args.args[0]
    assert passed_asset.tenant_id == tenant_id
    assert passed_asset.offer_id == offer_id
    assert passed_asset.source == AssetSource.EXTERNAL
    assert passed_asset.status == AssetStatus.READY
    assert passed_asset.file_url == "https://cdn.example/file.pdf"
    assert passed_asset.size_bytes == 1024


# ----------------------------------------------------------------- generate


def test_generate_asset_creates_processing_stub(
    service, asset_repo, tenant_id, offer_id
):
    """AI generation is a stub — row is created with status PROCESSING and
    returned immediately. No real AI call."""
    stub = _make_asset_mock(
        tenant_id=tenant_id,
        offer_id=offer_id,
        asset_type=AssetType.FLYER,
        source=AssetSource.AI,
        status=AssetStatus.PROCESSING,
    )
    asset_repo.create.return_value = stub

    result = service.generate_asset(
        tenant_id=tenant_id,
        offer_id=offer_id,
        type=AssetType.FLYER,
        prompt_params={"style": "bold", "palette": "warm"},
    )

    assert result is stub
    passed = asset_repo.create.call_args.args[0]
    assert passed.source == AssetSource.AI
    assert passed.status == AssetStatus.PROCESSING
    assert passed.editable_in_puck is True
    assert passed.prompt_params == {"style": "bold", "palette": "warm"}


# --------------------------------------------------------------------- list


def test_list_assets_passes_filters_through(service, asset_repo, tenant_id, offer_id):
    asset_repo.list.return_value = ([], 0)
    service.list_assets(
        tenant_id=tenant_id,
        offer_id=offer_id,
        search="foo",
        type=AssetType.VIDEO,
        source=AssetSource.AI,
        sort="name_asc",
        limit=12,
        offset=24,
    )
    call = asset_repo.list.call_args
    assert call.kwargs["search"] == "foo"
    assert call.kwargs["type"] == AssetType.VIDEO
    assert call.kwargs["source"] == AssetSource.AI
    assert call.kwargs["sort"] == "name_asc"
    assert call.kwargs["limit"] == 12
    assert call.kwargs["offset"] == 24


# ---------------------------------------------------------------- get_asset


def test_get_asset_missing_raises(service, asset_repo, tenant_id, offer_id):
    asset_repo.get_by_id.return_value = None
    with pytest.raises(AssetNotFoundError):
        service.get_asset(tenant_id=tenant_id, offer_id=offer_id, asset_id=uuid4())


def test_get_asset_returns_entity(service, asset_repo, tenant_id, offer_id):
    entity = MagicMock(spec=OfferAsset)
    asset_repo.get_by_id.return_value = entity
    result = service.get_asset(tenant_id=tenant_id, offer_id=offer_id, asset_id=uuid4())
    assert result is entity


# ------------------------------------------------------------------ update


def test_update_asset_patches_entity(service, asset_repo, tenant_id, offer_id):
    entity = OfferAsset(
        tenant_id=tenant_id,
        offer_id=offer_id,
        name="old",
        type=AssetType.FLYER,
        source=AssetSource.EXTERNAL,
        status=AssetStatus.READY,
    )
    asset_repo.get_by_id.return_value = entity
    asset_repo.update.side_effect = lambda a: a

    result = service.update_asset(
        tenant_id=tenant_id,
        offer_id=offer_id,
        asset_id=entity.id,
        fields={"name": "new"},
    )
    assert result.name == "new"
    asset_repo.update.assert_called_once()


# ------------------------------------------------------------------ delete


def test_delete_asset_soft_deletes(service, asset_repo, tenant_id, offer_id):
    asset_repo.soft_delete.return_value = True
    service.delete_asset(tenant_id=tenant_id, offer_id=offer_id, asset_id=uuid4())
    asset_repo.soft_delete.assert_called_once()


def test_delete_asset_missing_raises(service, asset_repo, tenant_id, offer_id):
    asset_repo.soft_delete.return_value = False
    with pytest.raises(AssetNotFoundError):
        service.delete_asset(tenant_id=tenant_id, offer_id=offer_id, asset_id=uuid4())


# ------------------------------------------------------------ download_url


def test_get_download_url_delegates_to_storage(
    service, asset_repo, file_storage, tenant_id, offer_id
):
    entity = MagicMock(spec=OfferAsset)
    entity.file_url = "https://cdn.example/file.pdf"
    asset_repo.get_by_id.return_value = entity
    file_storage.get_signed_url = MagicMock(return_value="https://signed.url")

    result = service.get_download_url(
        tenant_id=tenant_id, offer_id=offer_id, asset_id=uuid4()
    )
    assert result == "https://signed.url"
    file_storage.get_signed_url.assert_called_once_with("https://cdn.example/file.pdf")
