"""Unit tests for OfferKnowledgeService — upload/url/delete/reindex flows."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from luana_core_offer_studio.application.services.offer_knowledge_service import (
    OfferKnowledgeService,
)
from luana_core_offer_studio.domain.enums import (
    KnowledgeSourceStatus,
    KnowledgeSourceType,
)
from luana_core_offer_studio.domain.exceptions import KnowledgeSourceNotFoundError
from luana_core_offer_studio.domain.knowledge_source import KnowledgeSource


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.fixture
def offer_id():
    return uuid4()


@pytest.fixture
def knowledge_repo():
    return MagicMock()


@pytest.fixture
def file_storage():
    port = MagicMock()
    port.upload.return_value = ("https://cdn.example/doc.pdf", 2048)
    return port


@pytest.fixture
def rag_indexer():
    return MagicMock()


@pytest.fixture
def event_bus():
    return MagicMock()


@pytest.fixture
def service(knowledge_repo, file_storage, rag_indexer, event_bus):
    return OfferKnowledgeService(
        knowledge_repo=knowledge_repo,
        file_storage=file_storage,
        rag_indexer=rag_indexer,
        event_bus=event_bus,
    )


def _make_source_mock(
    *,
    tenant_id,
    offer_id,
    type_=KnowledgeSourceType.PDF,
    status=KnowledgeSourceStatus.PROCESSING,
):
    m = MagicMock(spec=KnowledgeSource)
    m.id = uuid4()
    m.tenant_id = tenant_id
    m.offer_id = offer_id
    m.type = type_
    m.status = status
    return m


# ------------------------------------------------------------------- upload


def test_upload_source_stores_file_creates_row_indexes(
    service,
    knowledge_repo,
    file_storage,
    rag_indexer,
    tenant_id,
    offer_id,
):
    stub = _make_source_mock(tenant_id=tenant_id, offer_id=offer_id)
    knowledge_repo.create.return_value = stub

    service.upload_source(
        tenant_id=tenant_id,
        offer_id=offer_id,
        file_bytes=b"pdf-bytes",
        filename="whitepaper.pdf",
        type_=KnowledgeSourceType.PDF,
        mime_type="application/pdf",
    )

    file_storage.upload.assert_called_once()
    knowledge_repo.create.assert_called_once()
    passed = knowledge_repo.create.call_args.args[0]
    assert passed.tenant_id == tenant_id
    assert passed.offer_id == offer_id
    assert passed.status == KnowledgeSourceStatus.PROCESSING
    assert passed.file_url == "https://cdn.example/doc.pdf"
    rag_indexer.index_source.assert_called_once()


# ------------------------------------------------------------------- url


def test_add_url_source_creates_row_and_indexes(
    service,
    knowledge_repo,
    rag_indexer,
    tenant_id,
    offer_id,
):
    stub = _make_source_mock(
        tenant_id=tenant_id,
        offer_id=offer_id,
        type_=KnowledgeSourceType.URL_YOUTUBE,
    )
    knowledge_repo.create.return_value = stub

    service.add_url_source(
        tenant_id=tenant_id,
        offer_id=offer_id,
        url="https://youtu.be/abc",
        type_=KnowledgeSourceType.URL_YOUTUBE,
        name="Intro video",
    )

    passed = knowledge_repo.create.call_args.args[0]
    assert passed.source_url == "https://youtu.be/abc"
    assert passed.status == KnowledgeSourceStatus.PROCESSING
    assert passed.type == KnowledgeSourceType.URL_YOUTUBE
    rag_indexer.index_source.assert_called_once()


# ------------------------------------------------------------------- list


def test_list_sources_passes_filters(service, knowledge_repo, tenant_id, offer_id):
    knowledge_repo.list.return_value = []
    service.list_sources(
        tenant_id=tenant_id,
        offer_id=offer_id,
        search="pdf",
        type_=KnowledgeSourceType.PDF,
    )
    call = knowledge_repo.list.call_args
    assert call.kwargs["search"] == "pdf"
    assert call.kwargs["type_"] == KnowledgeSourceType.PDF


# ------------------------------------------------------------------ delete


def test_delete_source_soft_deletes_and_removes_from_index(
    service,
    knowledge_repo,
    rag_indexer,
    tenant_id,
    offer_id,
):
    stub = MagicMock(spec=KnowledgeSource)
    knowledge_repo.get_by_id.return_value = stub
    knowledge_repo.soft_delete.return_value = True

    service.delete_source(tenant_id=tenant_id, offer_id=offer_id, source_id=uuid4())
    knowledge_repo.soft_delete.assert_called_once()
    rag_indexer.delete_source.assert_called_once_with(stub)


def test_delete_source_missing_raises(service, knowledge_repo, tenant_id, offer_id):
    knowledge_repo.get_by_id.return_value = None
    with pytest.raises(KnowledgeSourceNotFoundError):
        service.delete_source(tenant_id=tenant_id, offer_id=offer_id, source_id=uuid4())


# ------------------------------------------------------------------ reindex


def test_reindex_source_resets_status_and_calls_indexer(
    service,
    knowledge_repo,
    rag_indexer,
    tenant_id,
    offer_id,
):
    stub = MagicMock(spec=KnowledgeSource)
    stub.status = KnowledgeSourceStatus.INDEXED
    knowledge_repo.get_by_id.return_value = stub
    knowledge_repo.update.return_value = stub

    service.reindex_source(tenant_id=tenant_id, offer_id=offer_id, source_id=uuid4())
    assert stub.status == KnowledgeSourceStatus.PROCESSING
    knowledge_repo.update.assert_called_once_with(stub)
    rag_indexer.reindex_source.assert_called_once_with(stub)


def test_reindex_missing_source_raises(service, knowledge_repo, tenant_id, offer_id):
    knowledge_repo.get_by_id.return_value = None
    with pytest.raises(KnowledgeSourceNotFoundError):
        service.reindex_source(
            tenant_id=tenant_id,
            offer_id=offer_id,
            source_id=uuid4(),
        )
