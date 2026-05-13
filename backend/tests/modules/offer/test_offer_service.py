"""Tests for OfferService archive / restore / soft-delete flows."""

import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from luana_core_offer_studio.application.offer_service import OfferService
from luana_core_offer_studio.domain.enums import OfferArchetype, OfferValueLevel
from luana_core_offer_studio.domain.offer import PricingStructure
from luana_core_platform.domain.datetime_utils import utc_now
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
        self,
        db: Session,
        tenant_a,
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
        self,
        db: Session,
        tenant_a,
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
            ],
        )
        db.flush()

        names = {o.public_name for o in service.list_archived_offers(tenant_a)}
        assert names == {"Archived1", "Archived2"}


class TestCreateOfferCurrency:
    """Regression: new offers must inherit the tenant's default currency
    when the caller does not provide one, instead of a hardcoded 'USD'.
    """

    def test_create_offer_with_explicit_currency_preserves_it(
        self,
        db: Session,
        tenant_a,
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


class TestCreateOfferValueLevelInvariant:
    """Regression: newly-created offers must NOT default to LEAD_MAGNET when
    the wizard omits ``value_level`` and ``is_lead_magnet`` is False. The
    service enforces the invariant ``value_level == LEAD_MAGNET`` iff
    ``is_lead_magnet``. See `.claude/rules/` + Offer Studio ladder grouping.
    """

    def test_non_lead_magnet_without_value_level_defaults_to_activacion(self, db: Session, tenant_a):
        service = OfferService(db)
        offer = service.create_offer(
            name="Paid Offer",
            tenant_id=tenant_a,
            archetype=OfferArchetype.PRODUCTO,
            is_lead_magnet=False,
            value_level=None,
        )
        assert offer.is_lead_magnet is False
        assert offer.value_level == OfferValueLevel.ACTIVACION

    def test_is_lead_magnet_forces_value_level_lead_magnet(self, db: Session, tenant_a):
        service = OfferService(db)
        offer = service.create_offer(
            name="Free Ebook",
            tenant_id=tenant_a,
            archetype=OfferArchetype.PRODUCTO,
            is_lead_magnet=True,
            value_level=None,
        )
        assert offer.is_lead_magnet is True
        assert offer.value_level == OfferValueLevel.LEAD_MAGNET

    def test_explicit_value_level_is_preserved_when_consistent(self, db: Session, tenant_a):
        service = OfferService(db)
        offer = service.create_offer(
            name="Core Program",
            tenant_id=tenant_a,
            archetype=OfferArchetype.PROGRAMA,
            is_lead_magnet=False,
            value_level=OfferValueLevel.TRANSFORMACION,
        )
        assert offer.is_lead_magnet is False
        assert offer.value_level == OfferValueLevel.TRANSFORMACION

    def test_value_level_lead_magnet_forces_is_lead_magnet_true(self, db: Session, tenant_a):
        """If caller passes value_level=LEAD_MAGNET with is_lead_magnet=False
        (legacy frontend), normalize to the consistent state instead of
        silently dropping the ladder position."""
        service = OfferService(db)
        offer = service.create_offer(
            name="Inconsistent Input",
            tenant_id=tenant_a,
            archetype=OfferArchetype.PRODUCTO,
            is_lead_magnet=False,
            value_level=OfferValueLevel.LEAD_MAGNET,
        )
        assert offer.is_lead_magnet is True
        assert offer.value_level == OfferValueLevel.LEAD_MAGNET

    def test_is_lead_magnet_true_with_non_lead_magnet_value_level_is_normalized(self, db: Session, tenant_a):
        """is_lead_magnet is the user-facing intent and wins: a caller that
        says "this IS a lead magnet" with value_level=ACTIVACION gets
        value_level overridden to LEAD_MAGNET to keep the ladder coherent."""
        service = OfferService(db)
        offer = service.create_offer(
            name="Conflicting Input",
            tenant_id=tenant_a,
            archetype=OfferArchetype.PRODUCTO,
            is_lead_magnet=True,
            value_level=OfferValueLevel.ACTIVACION,
        )
        assert offer.is_lead_magnet is True
        assert offer.value_level == OfferValueLevel.LEAD_MAGNET


class TestCreateOfferPricing:
    """Regression: the wizard seeds its price + currency as the offer's
    first ``PricingStructure`` so the editor's pricing section opens with
    a concrete starting point instead of an empty list."""

    def test_pricing_options_persist_when_provided(self, db: Session, tenant_a):
        service = OfferService(db)
        seed = PricingStructure(
            label="Standard",
            plan_type="one_time",
            total_amount=497.0,
            currency="PEN",
        )
        offer = service.create_offer(
            name="Programa de Ventas",
            tenant_id=tenant_a,
            archetype=OfferArchetype.PROGRAMA,
            value_level=OfferValueLevel.TRANSFORMACION,
            currency="PEN",
            pricing_options=[seed],
        )
        assert len(offer.pricing_options) == 1
        persisted = offer.pricing_options[0]
        assert persisted.label == "Standard"
        assert persisted.total_amount == 497.0
        assert persisted.currency == "PEN"

    def test_pricing_options_default_empty_when_omitted(self, db: Session, tenant_a):
        """Lead magnets and legacy callers that don't send pricing keep the
        existing behavior — empty list, editor starts from scratch."""
        service = OfferService(db)
        offer = service.create_offer(
            name="Lead Magnet",
            tenant_id=tenant_a,
            archetype=OfferArchetype.PRODUCTO,
            is_lead_magnet=True,
        )
        assert offer.pricing_options == []
