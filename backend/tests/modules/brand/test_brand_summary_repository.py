"""Tests for ``BrandSummaryRepository`` — upsert + tenant isolation + version bump."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.modules.brand.infrastructure.repositories.brand_summary_repository import (
    BrandSummaryRepository,
)


@pytest.fixture
def repo(db):
    return BrandSummaryRepository(db)


@pytest.fixture
def tenant_id():
    return uuid4()


class TestUpsert:
    """upsert() inserts on first call, bumps version on second."""

    def test_first_call_inserts_version_one(self, repo, db, tenant_id) -> None:
        row = repo.upsert(
            tenant_id=tenant_id,
            summary="Marca con propósito. Voz cercana.",
            model_used="gpt-4o-mini",
            last_section_changed="identity",
        )
        db.commit()
        assert row.tenant_id == tenant_id
        assert row.version == 1
        assert row.chars_count == len("Marca con propósito. Voz cercana.")
        assert row.summary == "Marca con propósito. Voz cercana."
        assert row.model_used == "gpt-4o-mini"
        assert row.last_section_changed == "identity"

    def test_second_call_increments_version(self, repo, db, tenant_id) -> None:
        repo.upsert(
            tenant_id=tenant_id,
            summary="v1",
            model_used="gpt-4o-mini",
        )
        db.commit()
        second = repo.upsert(
            tenant_id=tenant_id,
            summary="v2 distinto",
            model_used="gpt-4o-mini",
            last_section_changed="voice",
        )
        db.commit()
        assert second.version == 2
        assert second.summary == "v2 distinto"
        assert second.last_section_changed == "voice"


class TestTenantIsolation:
    def test_get_isolated_per_tenant(self, repo, db) -> None:
        a = uuid4()
        b = uuid4()
        repo.upsert(tenant_id=a, summary="A", model_used="m")
        db.commit()
        assert repo.get(tenant_id=a) is not None
        assert repo.get(tenant_id=b) is None
