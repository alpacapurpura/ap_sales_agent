"""Offer module test fixtures."""

import uuid

import pytest
from sqlalchemy.orm import Session

from luana_core_offer_studio.domain.enums import OfferArchetype, OfferStatus, OfferValueLevel
from luana_core_offer_studio.infrastructure.models.product_model import ProductModel

TENANT_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
TENANT_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


@pytest.fixture
def tenant_a() -> uuid.UUID:
    return TENANT_A


@pytest.fixture
def tenant_b() -> uuid.UUID:
    return TENANT_B


def create_product_model(
    tenant_id: uuid.UUID,
    *,
    archetype: str = OfferArchetype.PRODUCTO.value,
    status: str = OfferStatus.ACTIVE.value,
    name: str = "Test Offer",
    value_level: str | None = OfferValueLevel.ACTIVACION.value,
    **overrides,
) -> ProductModel:
    defaults = {
        "id": uuid.uuid4(),
        "tenant_id": tenant_id,
        "name": name,
        "archetype": archetype,
        "status": status,
        "value_level": value_level,
        "format_hint": None,
        "is_lead_magnet": False,
        "has_editions": True,
        "pricing": [],
        "currency": "USD",
        "specific_details": {},
        "deliverables": [],
        "headline_promise": "Headline",
        "primary_outcome": "Outcome",
        "time_to_value": "1 week",
        "marketing_pain_points": [],
        "marketing_desires": [],
        "objections": [],
        "target_avatar_match": [],
        "access_duration": None,
        "access_duration_text": None,
        "support_duration_days": None,
        "delivery_model": "diy",
        "requires_application": False,
        "min_financial_capacity": "LOW_INCOME",
        "prerequisites": [],
        "anti_avatar_keywords": [],
        "guarantee_type": "none",
        "guarantee_terms": "",
        "downsell_product_id": None,
        "upsell_product_id": None,
        "includes_offers": [],
        "onboarding_action": None,
        "onboarding_url": None,
        "calendar_type_id": None,
        "checkout_page_url": None,
        "vsl_link": None,
        "landing_page_config": {},
        "metadata_info": {},
        "archived_at": None,
        "deleted_at": None,
    }
    defaults.update(overrides)
    return ProductModel(**defaults)


@pytest.fixture
def db_with_offers(db: Session, tenant_a: uuid.UUID, tenant_b: uuid.UUID):
    offer_a1 = create_product_model(tenant_a, name="Offer A1", status="active")
    offer_a2 = create_product_model(tenant_a, name="Offer A2", status="draft")
    offer_b1 = create_product_model(tenant_b, name="Offer B1", status="active")
    db.add_all([offer_a1, offer_a2, offer_b1])
    db.flush()
    return {"a1": offer_a1, "a2": offer_a2, "b1": offer_b1}
