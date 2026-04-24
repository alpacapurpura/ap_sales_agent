"""Arch test: every offer FieldContract path resolves to a real Offer attribute.

Post field-contract-platform refactor (Fase 04), the legacy
``OFFER_FIELDS_BY_FE_SECTION`` dict was removed. Coverage is enforced by
checking that every path in the platform registry maps to a real
Pydantic field (top-level, ``specific_details.*`` per variant, or
``platform_details.*``).

refs: docs/refactors/field-contract-platform/DESIGN.md
"""

from __future__ import annotations

from src.modules.offer.domain.details import (
    EventDetails,
    PlatformDetails,
    ProductDetails,
    ProgramDetails,
    ServiceDetails,
    SubscriptionDetails,
)
from src.modules.offer.domain.field_contract import OFFER_FIELD_CONTRACTS
from src.modules.offer.domain.offer import Offer


def _all_known_paths() -> set[str]:
    """Build the set of valid Offer paths the registry can reference."""
    paths: set[str] = set(Offer.model_fields.keys())
    for cls in (ProductDetails, ServiceDetails, ProgramDetails, SubscriptionDetails, EventDetails):
        for fname in cls.model_fields:
            paths.add(f"specific_details.{fname}")
    for fname in PlatformDetails.model_fields:
        paths.add(f"platform_details.{fname}")
    return paths


def test_every_field_contract_path_exists_on_offer_aggregate() -> None:
    """Every path in OFFER_FIELD_CONTRACTS resolves to a real Pydantic field."""
    valid_paths = _all_known_paths()
    invalid: list[str] = []
    for c in OFFER_FIELD_CONTRACTS:
        if c.path not in valid_paths:
            invalid.append(c.path)
    assert not invalid, (
        f"FieldContract paths not present in Offer / details / platform_details: "
        f"{invalid}. Either add the field to the Pydantic model or remove the "
        f"override + section_map entry in offer/domain/field_contract.py."
    )
