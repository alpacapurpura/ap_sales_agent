"""Architecture fitness: ``supported_variant_structures`` invariants.

Sprint 15.1 adds ``ArchetypeCapabilities.supported_variant_structures`` so
the wizard can offer a "¿Cómo varía tu oferta?" step for archetypes that
admit more than one variant shape (e.g. PROGRAMA can be COHORT or
MODALITY; SERVICIO can be RECURRING_INTAKE, TIER or MODALITY).

Invariants:

1. Archetypes with ``supports_editions=True`` declare a **non-empty**
   ``supported_variant_structures`` tuple. An empty tuple would tell the
   wizard "no options available" while the capabilities claim editions
   are supported — contradictory.

2. The ``default_variant_structure`` MUST appear inside
   ``supported_variant_structures``. Otherwise a tenant selecting the
   preset's default gets a structure the archetype doesn't accept.

3. Archetypes with ``supports_editions=False`` keep
   ``supported_variant_structures`` empty. Non-empty would invite the
   wizard to surface options for an archetype that rejects editions.

4. Entries are unique — a structure cannot appear twice in the same
   tuple. Duplicates are almost certainly a copy-paste bug.
"""

from __future__ import annotations

from src.modules.offer.domain.archetype_catalog import ARCHETYPE_CATALOG


def test_edition_supporting_archetypes_have_non_empty_supported_tuple() -> None:
    empty = [
        archetype.value
        for archetype, caps in ARCHETYPE_CATALOG.items()
        if caps.supports_editions and not caps.supported_variant_structures
    ]
    assert empty == [], (
        "Edition-supporting archetypes must declare at least one structure in "
        f"supported_variant_structures. Empty: {empty}. "
        "Without options the wizard's 'how does your offer vary?' step has nothing to render."
    )


def test_default_variant_structure_is_in_supported() -> None:
    misaligned = [
        (archetype.value, caps.default_variant_structure.value)
        for archetype, caps in ARCHETYPE_CATALOG.items()
        if (
            caps.default_variant_structure is not None
            and caps.default_variant_structure not in caps.supported_variant_structures
        )
    ]
    assert misaligned == [], (
        "Every archetype's default_variant_structure must appear in its "
        f"supported_variant_structures tuple. Misaligned: {misaligned}. "
        "Preset-driven offer creation would pick a structure the archetype rejects."
    )


def test_non_edition_archetypes_have_empty_supported_tuple() -> None:
    leaks = [
        (archetype.value, [s.value for s in caps.supported_variant_structures])
        for archetype, caps in ARCHETYPE_CATALOG.items()
        if not caps.supports_editions and caps.supported_variant_structures
    ]
    assert leaks == [], (
        "Archetypes with supports_editions=False must keep "
        f"supported_variant_structures empty. Leaks: {leaks}. "
        "Non-empty values would invite the wizard to surface options for an "
        "archetype that semantically rejects editions."
    )


def test_supported_variant_structures_are_unique_per_archetype() -> None:
    duplicates = []
    for archetype, caps in ARCHETYPE_CATALOG.items():
        seen: set[str] = set()
        dups: list[str] = []
        for structure in caps.supported_variant_structures:
            if structure.value in seen:
                dups.append(structure.value)
            seen.add(structure.value)
        if dups:
            duplicates.append((archetype.value, dups))
    assert duplicates == [], (
        "supported_variant_structures must not contain duplicates. "
        f"Offending archetypes: {duplicates}. "
        "Almost certainly a copy-paste bug — remove the repeated entry."
    )
