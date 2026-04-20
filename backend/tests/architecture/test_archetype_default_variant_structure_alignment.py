"""Architecture fitness: archetype catalog ↔ variant structure invariants.

Sprint 14.1 promotes the archetype-↔-default-structure mapping from raw SQL
in migration 049 into ``ArchetypeCapabilities.default_variant_structure``.
Once promoted, the catalog must satisfy three invariants:

1. Every archetype with ``supports_editions=True`` declares a non-None
   ``default_variant_structure``. Without it, ``OfferService`` cannot spawn
   the placeholder edition, and the user gets a 500 on offer creation
   (the bug this whole change set fixes).

2. Every archetype with ``supports_editions=False`` declares
   ``default_variant_structure=None``. Setting one would invite callers to
   create editions for archetypes that semantically reject them.

3. The default must be temporal-anchored — TEMPORAL_*, RECURRING_*. A
   PROGRAMA placeholder defaulting to TIER would be a UX disaster: the
   wizard pre-fills the wrong rail. Non-temporal structures (TIER, REGIONAL,
   …) are valid second-row variants but never the placeholder default.

These rules complement ``test_variant_structure_catalog_purity.py`` (zero
outbound imports from the variant catalog) and
``test_archetype_catalog_completeness.py`` (every enum has an entry).
"""

from __future__ import annotations

from src.modules.offer.domain.archetype_catalog import ARCHETYPE_CATALOG
from src.modules.offer.domain.enums import VariantStructure

# Structures valid as a placeholder default. Mirrors the temporal subset of
# the VariantStructure enum — the placeholder is always the "first launch"
# edition and the first launch is always anchored in time. Non-temporal
# structures (TIER, REGIONAL, MODALITY, etc.) are valid additional editions
# but not the seed.
_TEMPORAL_STRUCTURES: frozenset[VariantStructure] = frozenset(
    {
        VariantStructure.TEMPORAL_COHORT,
        VariantStructure.TEMPORAL_SINGLE_DATE,
        VariantStructure.RECURRING_INTAKE,
    }
)


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


def test_default_variant_structure_is_temporal_anchored() -> None:
    non_temporal = [
        (archetype.value, caps.default_variant_structure.value)
        for archetype, caps in ARCHETYPE_CATALOG.items()
        if caps.default_variant_structure is not None and caps.default_variant_structure not in _TEMPORAL_STRUCTURES
    ]
    assert non_temporal == [], (
        "Placeholder edition defaults must be temporal-anchored (TEMPORAL_* / RECURRING_*). "
        f"Offending archetypes: {non_temporal}. "
        "Non-temporal structures (TIER, REGIONAL, MODALITY, …) are valid second-row variants "
        "but never the seed edition."
    )
