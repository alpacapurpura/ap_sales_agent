"""Tests for OfferRepository CRUD and domain mapping."""

from sqlalchemy.orm import Session

from src.modules.offer.domain.enums import OfferArchetype, OfferValueLevel
from src.modules.offer.infrastructure.repositories.offer_repository import (
    OfferRepository,
)
from tests.modules.offer.conftest import create_product_model


class TestCreateAndRetrieveRoundtrip:
    def test_roundtrip(self, db: Session, tenant_a):
        repo = OfferRepository(db)
        model = create_product_model(
            tenant_a,
            name="Roundtrip",
            archetype="programa",
            value_level="transformacion",
            headline_promise="Transform",
        )
        db.add(model)
        db.flush()
        result = repo.get_by_id(model.id, tenant_a)
        assert result is not None
        assert result.public_name == "Roundtrip"
        assert result.archetype == OfferArchetype.PROGRAMA


class TestGetAllExcludesArchived:
    def test_archived_not_in_results(self, db: Session, tenant_a):
        repo = OfferRepository(db)
        db.add_all(
            [
                create_product_model(tenant_a, name="Active", status="active"),
                create_product_model(tenant_a, name="Archived", status="archived"),
            ]
        )
        db.flush()
        names = [o.public_name for o in repo.get_all_by_tenant(tenant_a)]
        assert "Active" in names and "Archived" not in names


class TestUpdatePersistsChanges:
    def test_update(self, db: Session, tenant_a):
        repo = OfferRepository(db)
        model = create_product_model(tenant_a)
        db.add(model)
        db.flush()
        offer = repo.get_by_id(model.id, tenant_a)
        offer.headline_promise = "Updated"
        updated = repo.update(offer, tenant_a)
        assert updated.headline_promise == "Updated"


class TestToDomainNormalization:
    def test_uppercase_value_level(self, db: Session, tenant_a):
        repo = OfferRepository(db)
        model = create_product_model(tenant_a, value_level="ACTIVACION")
        db.add(model)
        db.flush()
        assert (
            repo.get_by_id(model.id, tenant_a).value_level == OfferValueLevel.ACTIVACION
        )

    def test_legacy_guarantee(self, db: Session, tenant_a):
        repo = OfferRepository(db)
        model = create_product_model(tenant_a, guarantee_type="NO_REFUNDS")
        db.add(model)
        db.flush()
        assert repo.get_by_id(model.id, tenant_a).guarantee_type == "none"

    def test_legacy_pricing(self, db: Session, tenant_a):
        repo = OfferRepository(db)
        model = create_product_model(
            tenant_a,
            pricing=[{"plan_type": "PAY_IN_FULL", "label": "x", "total_amount": 997}],
        )
        db.add(model)
        db.flush()
        assert (
            repo.get_by_id(model.id, tenant_a).pricing_options[0].plan_type
            == "one_time"
        )
