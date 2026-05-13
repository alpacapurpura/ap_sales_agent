"""Tests for tenant isolation in Offer module."""

import uuid

import pytest
from sqlalchemy.orm import Session

from luana_core_offer_studio.infrastructure.repositories.offer_repository import (
    OfferRepository,
)
from tests.modules.offer.conftest import TENANT_A, TENANT_B


class TestGetByIdTenantIsolation:
    def test_returns_own_tenant_offer(self, db: Session, db_with_offers):
        repo = OfferRepository(db)
        result = repo.get_by_id(db_with_offers["a1"].id, TENANT_A)
        assert result is not None
        assert result.tenant_id == TENANT_A

    def test_rejects_cross_tenant(self, db: Session, db_with_offers):
        repo = OfferRepository(db)
        result = repo.get_by_id(db_with_offers["a1"].id, TENANT_B)
        assert result is None

    def test_nonexistent_id_returns_none(self, db: Session, db_with_offers):
        repo = OfferRepository(db)
        assert repo.get_by_id(uuid.uuid4(), TENANT_A) is None


class TestGetAllByTenantIsolation:
    def test_only_returns_own_tenant(self, db: Session, db_with_offers):
        repo = OfferRepository(db)
        assert len(repo.get_all_by_tenant(TENANT_A)) == 2
        assert len(repo.get_all_by_tenant(TENANT_B)) == 1


class TestUpdateTenantIsolation:
    def test_update_rejects_cross_tenant(self, db: Session, db_with_offers):
        repo = OfferRepository(db)
        offer = repo.get_by_id(db_with_offers["a1"].id, TENANT_A)
        offer.headline_promise = "Hacked"
        with pytest.raises(ValueError, match="not found"):
            repo.update(offer, TENANT_B)

    def test_update_succeeds_for_own_tenant(self, db: Session, db_with_offers):
        repo = OfferRepository(db)
        offer = repo.get_by_id(db_with_offers["a1"].id, TENANT_A)
        offer.headline_promise = "Updated"
        updated = repo.update(offer, TENANT_A)
        assert updated.headline_promise == "Updated"
