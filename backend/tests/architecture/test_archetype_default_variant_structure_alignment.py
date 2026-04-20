"""Architecture fitness: archetype catalog ↔ variant structure invariants.

Sprint 14.1 promoted the archetype-↔-default-structure mapping from raw SQL
in migration 049 into ``ArchetypeCapabilities.default_variant_structure``.
Sprint 15.1 extends the relationship with
``ArchetypeCapabilities.supported_variant_structures`` and the ``PRODUCTO``
/``MEMBRESIA`` promotion so non-temporal variants (SKU, TIER) are
first-class.

Invariants enforced here:

1. Every archetype with ``supports_editions=True`` declares a non-None
   ``default_variant_structure``. Without it, ``OfferService`` cannot spawn
   the placeholder edition and offer creation returns 500.

2. Every archetype with ``supports_editions=False`` declares
   ``default_variant_structure=None``. A non-None value would invite
   callers to create editions for an archetype that semantically rejects
   them.

Note (Sprint 15.1): the previous "placeholder defaults must be
temporal-anchored" rule was DROPPED. TIER and SKU_VARIANT are legitimate
placeholder defaults for MEMBRESIA and PRODUCTO respectively — the
"first launch" is a tier/sku record, not a cohort window. The wizard no
longer pre-fills a temporal rail for those archetypes.

These rules complement:
- ``test_variant_structure_catalog_purity.py`` (no outbound imports)
- ``test_archetype_catalog_completeness.py`` (every enum has an entry)
- ``test_archetype_supported_variant_structures.py`` (supported tuple
  invariants)
"""

from __future__ import annotations

from src.modules.offer.domain.archetype_catalog import ARCHETYPE_CATALOG


def test_edition_supporting_archetypes_declare_default_variant_structure() -> None:
    missing = [
        archetype.value
        for archetype, caps in ARCHETYPE_CATALOG.items()
        if caps.supports_editions and caps.default_variant_structure is None
    ]
    assert missing == [], (
        "Every edition-supporting archetype must declare default_variant_structure. "
        f"Missing: {missing}. "
        "Add the field to the ARCHETYPE_CATALOG entry — without it, "
        "OfferService cannot spawn the placeholder edition (500 on offer creation)."
    )


def test_non_edition_archetypes_have_no_default_variant_structure() -> None:
    leaks = [
        (archetype.value, caps.default_variant_structure)
        for archetype, caps in ARCHETYPE_CATALOG.items()
        if not caps.supports_editions and caps.default_variant_structure is not None
    ]
    assert leaks == [], (
        "Archetypes with supports_editions=False must keep default_variant_structure=None. "
        f"Leaks: {leaks}. "
        "A non-None value would invite callers to seed editions for an archetype "
        "that semantically rejects them."
    )
