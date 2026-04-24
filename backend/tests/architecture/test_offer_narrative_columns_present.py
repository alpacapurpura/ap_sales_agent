"""Arch test: every narrative field on Offer domain maps to a ProductModel column.

refs: docs/contracts/offer-narrative-fields-CONTRACT.md §13.1
"""

from src.modules.offer.domain.offer import Offer
from src.modules.offer.infrastructure.models.product_model import ProductModel

NARRATIVE_FIELDS = frozenset(
    {
        "before_state",
        "after_state",
        "why_now",
        "measurable_outcomes",
        "cultural_trust_barriers",
        "emotional_triggers",
        "status_drivers",
        "regret_scenarios",
        "refund_process_description",
        "urgency_drivers",
        "scarcity_reason_honest",
        "bonus_if_act_now",
        "final_push_copy",
    }
)


def test_narrative_fields_exist_on_offer_domain() -> None:
    """All 13 narrative fields are declared on the Offer domain aggregate."""
    offer_fields = set(Offer.model_fields.keys())
    missing = NARRATIVE_FIELDS - offer_fields
    assert not missing, f"Narrative fields missing on Offer domain: {missing}"


def test_narrative_columns_exist_on_product_model() -> None:
    """All 13 narrative columns are declared on ProductModel (SA table metadata)."""
    columns = {c.name for c in ProductModel.__table__.columns}
    missing = NARRATIVE_FIELDS - columns
    assert not missing, f"Narrative columns missing on ProductModel: {missing}"
