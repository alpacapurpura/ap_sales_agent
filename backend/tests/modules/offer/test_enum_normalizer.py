"""Tests for enum_normalizer pure functions."""
import pytest
from src.modules.offer.infrastructure.repositories.enum_normalizer import (
    normalize_archetype, normalize_delivery_model, normalize_deliverables,
    normalize_guarantee_type, normalize_pricing_options, normalize_specific_details,
    normalize_value_level,
)
from src.modules.offer.domain.enums import OfferArchetype, OfferValueLevel

class TestNormalizeValueLevel:
    def test_lowercase_valid(self):
        assert normalize_value_level("activacion") == OfferValueLevel.ACTIVACION
    def test_uppercase_normalizes(self):
        assert normalize_value_level("ACTIVACION") == OfferValueLevel.ACTIVACION
    def test_none_returns_none(self):
        assert normalize_value_level(None) is None
    def test_invalid_returns_none(self):
        assert normalize_value_level("potato") is None

class TestNormalizeGuarantee:
    def test_no_refunds_maps_to_none(self):
        assert normalize_guarantee_type("NO_REFUNDS") == "none"
    def test_valid_passthrough(self):
        assert normalize_guarantee_type("conditional_action_based") == "conditional_action_based"
    def test_null_returns_none(self):
        assert normalize_guarantee_type(None) == "none"

class TestNormalizePricingOptions:
    def test_pay_in_full(self):
        r = normalize_pricing_options([{"plan_type": "PAY_IN_FULL", "label": "x", "total_amount": 100}])
        assert r[0]["plan_type"] == "one_time"
    def test_split_pay(self):
        r = normalize_pricing_options([{"plan_type": "SPLIT_PAY", "label": "x", "total_amount": 300}])
        assert r[0]["plan_type"] == "payment_plan"

class TestNormalizeDeliverables:
    def test_live_group_call(self):
        r = normalize_deliverables([{"format": "LIVE_GROUP_CALL", "name": "Q&A"}])
        assert r[0]["format"] == "live_session"
    def test_uppercase_lowered(self):
        r = normalize_deliverables([{"format": "PDF", "name": "Guide"}])
        assert r[0]["format"] == "pdf"

class TestNormalizeSpecificDetails:
    def test_recorded_content(self):
        assert normalize_specific_details({"format": "RECORDED_CONTENT"})["format"] == "video_course"
    def test_fixed_cohort(self):
        assert normalize_specific_details({"structure_type": "FIXED_COHORT"})["structure_type"] == "fixed_cohort"
    def test_virtual_location(self):
        assert normalize_specific_details({"location_type": "VIRTUAL"})["location_type"] == "virtual"

class TestNormalizeArchetype:
    def test_lowercase(self):
        assert normalize_archetype("producto") == OfferArchetype.PRODUCTO
    def test_uppercase(self):
        assert normalize_archetype("PROGRAMA") == OfferArchetype.PROGRAMA
    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            normalize_archetype("garbage")

class TestNormalizeDeliveryModel:
    def test_valid(self):
        assert normalize_delivery_model("diy") == "diy"
    def test_uppercase(self):
        assert normalize_delivery_model("DWY") == "dwy"
    def test_none(self):
        assert normalize_delivery_model(None) is None
    def test_invalid(self):
        assert normalize_delivery_model("garbage") is None
