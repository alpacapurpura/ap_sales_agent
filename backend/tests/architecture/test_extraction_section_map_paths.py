"""Arch test: every path in OFFER_FIELDS_BY_FE_SECTION must exist as a
Pydantic field on the Offer domain aggregate.

refs: docs/contracts/offer-narrative-fields-CONTRACT.md §12 + §13.1
"""

from src.modules.offer.domain.extraction_section_map import OFFER_FIELDS_BY_FE_SECTION
from src.modules.offer.domain.offer import Offer


def test_every_mapped_field_exists_on_offer_aggregate() -> None:
    """Every field path in the section map resolves to a real Offer attribute."""
    offer_fields = set(Offer.model_fields.keys())
    for slug, field_names in OFFER_FIELDS_BY_FE_SECTION.items():
        for name in field_names:
            assert name in offer_fields, (
                f"OFFER_FIELDS_BY_FE_SECTION[{slug!r}] references "
                f"'{name}' which is not a field of Offer. Either add it to "
                f"the domain aggregate or remove it from the map."
            )
