"""Tests for OfferService archive / restore / soft-delete flows."""

import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.modules.offer.application.offer_service import OfferService
from src.modules.offer.domain.enums import OfferArchetype
from src.shared.domain.datetime_utils import utc_now
from tests.modules.offer.conftest import create_product_model


class TestArchiveOffer:
    def test_archive_offer_returns_domain_with_archived_at(self, db: Session, tenant_a):
        service = OfferService(db)
        model = create_product_model(tenant_a, name="Active")
        db.add(model)
        db.flush()

        offer = service.archive_offer(model.id, tenant_a)
        assert offer is not None
        assert offer.is_archived is True
        assert offer.archived_at is not None

    def test_archive_offer_unpublishes_embedded_landing_page(
        self, db: Session, tenant_a
    ):
        """Archiving an offer unpublishes its embedded landing page config.

        The ``landing_page_config`` JSONB is part of the Offer aggregate,
        so the service mutates it in the same transaction as the archive.
        """
        service = OfferService(db)
        model = create_product_model(
            tenant_a,
            name="WithLanding",
            landing_page_config={
                "is_published": True,
                "slug": "my-offer",
                "hero_headline": "Hello",
            },
        )
        db.add(model)
        db.flush()

        offer = service.archive_offer(model.id, tenant_a)
        assert offer is not None
        assert offer.landing_page_config is not None
        assert offer.landing_page_config.get("is_published") is False
        # Other config fields preserved
        assert offer.landing_page_config.get("slug") == "my-offer"

    def test_archive_offer_without_landing_config_does_not_fail(
        self, db: Session, tenant_a
    ):
        service = OfferService(db)
        model = create_product_model(tenant_a, landing_page_config={})
        db.add(model)
        db.flush()

        offer = service.archive_offer(model.id, tenant_a)
        assert offer is not None
        assert offer.is_archived is True

    def test_archive_offer_not_found_raises_404(self, db: Session, tenant_a):
        service = OfferService(db)
        with pytest.raises(HTTPException) as exc_info:
            service.archive_offer(uuid.uuid4(), tenant_a)
        assert exc_info.value.status_code == 404


class TestRestoreOffer:
    def test_restore_offer_clears_archived_at(self, db: Session, tenant_a):
        service = OfferService(db)
        model = create_product_model(tenant_a, archived_at=utc_now())
        db.add(model)
        db.flush()

        offer = service.restore_offer(model.id, tenant_a)
        assert offer is not None
        assert offer.is_archived is False

    def test_restore_offer_does_not_republish_landing(self, db: Session, tenant_a):
        """Restoring does NOT auto-republish the landing.

        Rationale: avoid sudden re-exposure — the user must republish
        manually after reviewing the offer state.
        """
        service = OfferService(db)
        model = create_product_model(
            tenant_a,
            archived_at=utc_now(),
            landing_page_config={"is_published": False, "slug": "restored"},
        )
        db.add(model)
        db.flush()

        offer = service.restore_offer(model.id, tenant_a)
        assert offer is not None
        assert offer.landing_page_config.get("is_published") is False

    def test_restore_offer_not_found_raises_404(self, db: Session, tenant_a):
        service = OfferService(db)
        with pytest.raises(HTTPException) as exc_info:
            service.restore_offer(uuid.uuid4(), tenant_a)
        assert exc_info.value.status_code == 404


class TestDeleteOffer:
    def test_delete_offer_on_archived_soft_deletes(self, db: Session, tenant_a):
        service = OfferService(db)
        model = create_product_model(tenant_a, archived_at=utc_now())
        db.add(model)
        db.flush()

        service.delete_offer(model.id, tenant_a)

        # No longer visible even in archived list
        assert service.get_offer(model.id, tenant_a) is None
        assert all(o.id != model.id for o in service.list_archived_offers(tenant_a))

    def test_delete_offer_on_active_returns_409(self, db: Session, tenant_a):
        service = OfferService(db)
        model = create_product_model(tenant_a)
        db.add(model)
        db.flush()

        with pytest.raises(HTTPException) as exc_info:
            service.delete_offer(model.id, tenant_a)
        assert exc_info.value.status_code == 409

    def test_delete_offer_not_found_raises_404(self, db: Session, tenant_a):
        service = OfferService(db)
        with pytest.raises(HTTPException) as exc_info:
            service.delete_offer(uuid.uuid4(), tenant_a)
        assert exc_info.value.status_code == 404


class TestListArchivedOffers:
    def test_list_archived_offers(self, db: Session, tenant_a):
        service = OfferService(db)
        db.add_all(
            [
                create_product_model(tenant_a, name="Active"),
                create_product_model(tenant_a, name="Archived1", archived_at=utc_now()),
                create_product_model(tenant_a, name="Archived2", archived_at=utc_now()),
            ]
        )
        db.flush()

        names = {o.public_name for o in service.list_archived_offers(tenant_a)}
        assert names == {"Archived1", "Archived2"}


class TestCreateOfferCurrency:
    """Regression: new offers must inherit the tenant's default currency
    when the caller does not provide one, instead of a hardcoded 'USD'.
    """

    def test_create_offer_with_explicit_currency_preserves_it(
        self, db: Session, tenant_a
    ):
        service = OfferService(db)
        offer = service.create_offer(
            name="Soles Offer",
            tenant_id=tenant_a,
            archetype=OfferArchetype.PRODUCTO,
            currency="PEN",
        )
        assert offer.currency == "PEN"
        # Reload from DB to confirm persistence
        reloaded = service.get_offer(offer.id, tenant_a)
        assert reloaded is not None
        assert reloaded.currency == "PEN"

    def test_create_offer_without_currency_leaves_it_null(self, db: Session, tenant_a):
        """Without an explicit currency, the service must persist NULL
        (the API layer is responsible for resolving TenantLocale; the
        service itself is locale-agnostic). This is the contract the
        endpoint relies on via get_tenant_locale.
        """
        service = OfferService(db)
        offer = service.create_offer(
            name="No Currency",
            tenant_id=tenant_a,
            archetype=OfferArchetype.PRODUCTO,
        )
        assert offer.currency is None
