"""Tests for OfferPersister and its registry entry."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.modules.copilot.infrastructure.persisters.offer_persister import (
    OfferPersister,
)
from src.modules.copilot.infrastructure.persisters.persister_registry import (
    get_persister,
)
from src.modules.offer.domain.enums import (
    DeliverableFormat,
    GuaranteeType,
    OfferArchetype,
    OfferStatus,
    PaymentPlanType,
)
from src.modules.offer.domain.offer import (
    DeliverableItem,
    ObjectionItem,
    Offer,
    PricingStructure,
)
from src.shared.domain.enums import FinancialCapacity


def _make_offer(**overrides) -> Offer:
    """Build a minimal valid Offer entity for testing."""
    defaults = {
        "id": uuid4(),
        "tenant_id": uuid4(),
        "internal_sku": "TEST-001",
        "public_name": "Test Offer",
        "archetype": OfferArchetype.PROGRAMA,
        "headline_promise": "Transform your business in 30 days",
        "target_avatar_match": [],
        "primary_outcome": "Doubled revenue",
        "time_to_value": "30 days",
        "requires_application": False,
        "min_financial_capacity": FinancialCapacity.MIDDLE_CLASS,
        "pricing_options": [],
        "guarantee_type": GuaranteeType.NONE,
        "guarantee_terms": "",
        "status": OfferStatus.DRAFT,
    }
    defaults.update(overrides)
    return Offer(**defaults)


class TestOfferPersister:
    def test_persist_simple_fields(self):
        """Persist flat string/list fields from mapa_global."""
        db = MagicMock()
        persister = OfferPersister(db)
        tenant_id = uuid4()
        offer_id = uuid4()
        offer = _make_offer(id=offer_id, tenant_id=tenant_id)

        mapa_global = {
            "headline_promise": "New promise in 14 days",
            "primary_outcome": "10x more sales",
            "marketing_pain_points": ["No clients", "No visibility"],
        }
        fields_to_persist = list(mapa_global.keys())

        with patch.object(persister, "repo") as mock_repo:
            mock_repo.get_by_id.return_value = offer
            mock_repo.update.return_value = offer

            persister.persist(tenant_id, mapa_global, fields_to_persist, offer_id)

            mock_repo.update.assert_called_once()
            updated_offer = mock_repo.update.call_args[0][0]
            assert updated_offer.headline_promise == "New promise in 14 days"
            assert updated_offer.primary_outcome == "10x more sales"
            assert updated_offer.marketing_pain_points == [
                "No clients",
                "No visibility",
            ]

    def test_persist_objections_complex_type(self):
        """Persist objections as list[ObjectionItem] from raw dicts."""
        db = MagicMock()
        persister = OfferPersister(db)
        tenant_id = uuid4()
        offer_id = uuid4()
        offer = _make_offer(id=offer_id, tenant_id=tenant_id)

        mapa_global = {
            "objections": [
                {
                    "type": "price",
                    "trigger_phrases": ["es muy caro", "no me alcanza"],
                    "strategy": "ROI Reframing",
                    "rebuttal": "Compara con el costo de no resolver el problema",
                },
            ],
        }
        fields_to_persist = ["objections"]

        with patch.object(persister, "repo") as mock_repo:
            mock_repo.get_by_id.return_value = offer
            mock_repo.update.return_value = offer

            persister.persist(tenant_id, mapa_global, fields_to_persist, offer_id)

            updated_offer = mock_repo.update.call_args[0][0]
            assert len(updated_offer.objections) == 1
            assert isinstance(updated_offer.objections[0], ObjectionItem)
            assert updated_offer.objections[0].type == "price"
            assert updated_offer.objections[0].strategy == "ROI Reframing"

    def test_persist_pricing_options_complex_type(self):
        """Persist pricing_options as list[PricingStructure] from raw dicts."""
        db = MagicMock()
        persister = OfferPersister(db)
        tenant_id = uuid4()
        offer_id = uuid4()
        offer = _make_offer(id=offer_id, tenant_id=tenant_id)

        mapa_global = {
            "pricing_options": [
                {
                    "label": "Pago único",
                    "plan_type": "one_time",
                    "total_amount": 997.0,
                    "is_default": True,
                },
                {
                    "label": "3 cuotas",
                    "plan_type": "payment_plan",
                    "total_amount": 1197.0,
                    "number_of_installments": 3,
                    "installment_amount": 399.0,
                },
            ],
        }
        fields_to_persist = ["pricing_options"]

        with patch.object(persister, "repo") as mock_repo:
            mock_repo.get_by_id.return_value = offer
            mock_repo.update.return_value = offer

            persister.persist(tenant_id, mapa_global, fields_to_persist, offer_id)

            updated_offer = mock_repo.update.call_args[0][0]
            assert len(updated_offer.pricing_options) == 2
            assert isinstance(updated_offer.pricing_options[0], PricingStructure)
            assert updated_offer.pricing_options[0].label == "Pago único"
            assert updated_offer.pricing_options[0].total_amount == 997.0

    def test_persist_deliverables_complex_type(self):
        """Persist deliverables as list[DeliverableItem] from raw dicts."""
        db = MagicMock()
        persister = OfferPersister(db)
        tenant_id = uuid4()
        offer_id = uuid4()
        offer = _make_offer(id=offer_id, tenant_id=tenant_id)

        mapa_global = {
            "deliverables": [
                {
                    "name": "Guía PDF",
                    "format": "pdf",
                    "quantity": "1",
                    "value_stack_price": 97.0,
                },
            ],
        }
        fields_to_persist = ["deliverables"]

        with patch.object(persister, "repo") as mock_repo:
            mock_repo.get_by_id.return_value = offer
            mock_repo.update.return_value = offer

            persister.persist(tenant_id, mapa_global, fields_to_persist, offer_id)

            updated_offer = mock_repo.update.call_args[0][0]
            assert len(updated_offer.deliverables) == 1
            assert isinstance(updated_offer.deliverables[0], DeliverableItem)
            assert updated_offer.deliverables[0].name == "Guía PDF"
            assert updated_offer.deliverables[0].format == DeliverableFormat.PDF

    def test_persist_skips_missing_fields(self):
        """Fields in fields_to_persist but not in mapa_global are skipped."""
        db = MagicMock()
        persister = OfferPersister(db)
        tenant_id = uuid4()
        offer_id = uuid4()
        offer = _make_offer(
            id=offer_id,
            tenant_id=tenant_id,
            headline_promise="Original promise",
        )

        mapa_global = {"headline_promise": "Updated promise"}
        fields_to_persist = ["headline_promise", "primary_outcome"]

        with patch.object(persister, "repo") as mock_repo:
            mock_repo.get_by_id.return_value = offer
            mock_repo.update.return_value = offer

            persister.persist(tenant_id, mapa_global, fields_to_persist, offer_id)

            updated_offer = mock_repo.update.call_args[0][0]
            assert updated_offer.headline_promise == "Updated promise"
            # primary_outcome remains as original (not in mapa_global)
            assert updated_offer.primary_outcome == "Doubled revenue"

    def test_persist_requires_entity_id(self):
        """OfferPersister requires entity_id (offer_id) — not creating new offers."""
        db = MagicMock()
        persister = OfferPersister(db)
        tenant_id = uuid4()

        with pytest.raises(ValueError, match=r"entity_id.*required"):
            persister.persist(tenant_id, {"x": "y"}, ["x"], entity_id=None)

    def test_persist_returns_early_if_offer_not_found(self):
        """If the offer doesn't exist, do nothing."""
        db = MagicMock()
        persister = OfferPersister(db)
        tenant_id = uuid4()
        offer_id = uuid4()

        with patch.object(persister, "repo") as mock_repo:
            mock_repo.get_by_id.return_value = None
            persister.persist(tenant_id, {"x": "y"}, ["x"], offer_id)
            mock_repo.update.assert_not_called()

    def test_load_existing_returns_flat_dict(self):
        """load_existing returns a flat dict from Offer entity fields."""
        db = MagicMock()
        persister = OfferPersister(db)
        tenant_id = uuid4()
        offer_id = uuid4()
        offer = _make_offer(
            id=offer_id,
            tenant_id=tenant_id,
            public_name="My Course",
            headline_promise="Transform in 30 days",
            marketing_pain_points=["low sales"],
            objections=[
                ObjectionItem(
                    type="price",
                    trigger_phrases=["es caro"],
                    strategy="ROI",
                    rebuttal="Vale la inversión",
                )
            ],
            pricing_options=[
                PricingStructure(
                    label="Pago único",
                    plan_type=PaymentPlanType.ONE_TIME,
                    total_amount=997.0,
                )
            ],
            deliverables=[
                DeliverableItem(
                    name="Módulo 1",
                    format=DeliverableFormat.VIDEO,
                    quantity="10 videos",
                    value_stack_price=297.0,
                )
            ],
        )

        with patch.object(persister, "repo") as mock_repo:
            mock_repo.get_by_id.return_value = offer

            result = persister.load_existing(tenant_id, offer_id)

            assert result["public_name"] == "My Course"
            assert result["headline_promise"] == "Transform in 30 days"
            assert result["marketing_pain_points"] == ["low sales"]
            # Complex types should be serialized as dicts
            assert isinstance(result["objections"], list)
            assert len(result["objections"]) == 1
            assert result["objections"][0]["type"] == "price"
            assert isinstance(result["pricing_options"], list)
            assert result["pricing_options"][0]["label"] == "Pago único"
            assert isinstance(result["deliverables"], list)
            assert result["deliverables"][0]["name"] == "Módulo 1"

    def test_load_existing_returns_empty_if_not_found(self):
        """If offer not found, return empty dict."""
        db = MagicMock()
        persister = OfferPersister(db)
        tenant_id = uuid4()
        offer_id = uuid4()

        with patch.object(persister, "repo") as mock_repo:
            mock_repo.get_by_id.return_value = None
            result = persister.load_existing(tenant_id, offer_id)
            assert result == {}


class TestPersisterRegistryOffer:
    def test_get_offer_persister(self):
        db = MagicMock()
        persister = get_persister("offer", db)
        assert isinstance(persister, OfferPersister)

    def test_brand_persister_still_works(self):
        """Ensure adding offer didn't break brand."""
        from src.modules.copilot.infrastructure.persisters.brand_persister import (
            BrandPersister,
        )

        db = MagicMock()
        persister = get_persister("brand", db)
        assert isinstance(persister, BrandPersister)
