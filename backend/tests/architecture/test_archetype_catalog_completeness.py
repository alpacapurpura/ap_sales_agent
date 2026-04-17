"""Architecture fitness: every OfferArchetype enum value has a catalog entry.

This gate prevents silent drift between the ``OfferArchetype`` enum and the
``ARCHETYPE_CATALOG`` dict. Adding a new archetype without a catalog entry
fails the build at CI — forcing the author to declare capabilities explicitly.
"""

from __future__ import annotations

from src.modules.offer.domain.archetype_catalog import ARCHETYPE_CATALOG
from src.modules.offer.domain.enums import OfferArchetype


def test_every_offer_archetype_has_a_catalog_entry() -> None:
    missing = [a for a in OfferArchetype if a not in ARCHETYPE_CATALOG]
    assert missing == [], (
        "Every OfferArchetype must have an ARCHETYPE_CATALOG entry. "
        f"Missing: {missing}. "
        "Add a record to archetype_catalog.py declaring the archetype's "
        "capabilities (supports_editions, defaults, wizard copy, etc.)."
    )


def test_catalog_has_no_orphan_entries() -> None:
    enum_values = set(OfferArchetype)
    catalog_values = set(ARCHETYPE_CATALOG.keys())
    orphans = catalog_values - enum_values
    assert orphans == set(), f"Catalog has entries for archetypes that no longer exist in the enum: {orphans}"


def test_catalog_records_self_reference_their_archetype() -> None:
    for archetype, caps in ARCHETYPE_CATALOG.items():
        assert caps.archetype is archetype, f"Catalog entry for {archetype} declares archetype={caps.archetype}"
