"""Tests for ``ArchetypeCapabilities.sections`` — per-archetype section set.

Rather than hard-coding the full section tuple per archetype (brittle,
broke on every content iteration through Sprint 6→12), we assert the
**invariants** the frontend depends on:

1. The tuple is non-empty, contains only valid ``SectionKey`` values and
   has no duplicates.
2. Every archetype carries the universal minimum (IDENTITY, PROMISE,
   PRICING, CLOSING) so every published offer is recognisable.
3. The archetype-specific "core" section is the first domain-content
   entry after the universal preamble — PRODUCT_DETAILS for PRODUCTO,
   PROGRAM_DETAILS for PROGRAMA, and so on. This is the invariant the
   wizard relies on to slot the archetype-unique question mid-flow.
4. Scope rules (D22) from the section catalog are respected: edition-less
   archetypes (PRODUCTO, MEMBRESIA) never carry EDITION_LEVEL sections;
   edition-supporting archetypes carry at least one non-OFFER_LEVEL
   section so the edition concept has an editor representation.

Related:
- `archetype_catalog.py` — the data under test.
- `section_catalog.py` — section metadata and scope authority.
- `offer_type_preset_catalog.py` — 7th SSoT axis (Sprint 12+).
"""

from __future__ import annotations

from src.modules.offer.domain.archetype_catalog import (
    ARCHETYPE_CATALOG,
    get_capabilities,
)
from src.modules.offer.domain.enums import OfferArchetype
from src.modules.offer.domain.section_catalog import (
    SectionKey,
    SectionScope,
    get_section,
)

UNIVERSAL_REQUIRED = frozenset(
    {SectionKey.IDENTITY, SectionKey.PROMISE, SectionKey.PRICING, SectionKey.CLOSING},
)

ARCHETYPE_CORE_SECTION: dict[OfferArchetype, SectionKey] = {
    OfferArchetype.PRODUCTO: SectionKey.PRODUCT_DETAILS,
    OfferArchetype.PROGRAMA: SectionKey.PROGRAM_DETAILS,
    OfferArchetype.SERVICIO: SectionKey.SERVICE_DETAILS,
    OfferArchetype.MEMBRESIA: SectionKey.SUBSCRIPTION_DETAILS,
    OfferArchetype.EXPERIENCIA: SectionKey.EVENT_DETAILS,
}


class TestSectionsFieldShape:
    def test_every_archetype_declares_a_non_empty_sections_tuple(self) -> None:
        for archetype, caps in ARCHETYPE_CATALOG.items():
            assert isinstance(caps.sections, tuple), f"{archetype}.sections must be a tuple"
            assert len(caps.sections) > 0, f"{archetype}.sections must not be empty"

    def test_sections_contains_only_valid_section_keys(self) -> None:
        for archetype, caps in ARCHETYPE_CATALOG.items():
            for section in caps.sections:
                assert isinstance(section, SectionKey), f"{archetype}.sections entry {section!r} is not a SectionKey"

    def test_sections_are_unique_within_an_archetype(self) -> None:
        for archetype, caps in ARCHETYPE_CATALOG.items():
            assert len(caps.sections) == len(set(caps.sections)), (
                f"{archetype}.sections contains duplicates: {caps.sections}"
            )


class TestUniversalMinimum:
    """Every archetype surfaces the bloque universal — no exceptions."""

    def test_every_archetype_includes_universal_required_sections(self) -> None:
        for archetype, caps in ARCHETYPE_CATALOG.items():
            missing = UNIVERSAL_REQUIRED - set(caps.sections)
            assert missing == set(), (
                f"{archetype} is missing required universal sections "
                f"{sorted(m.value for m in missing)}. "
                "Every offer must be recognisable — identity + promise + pricing + closing."
            )


class TestArchetypeCoreSection:
    """Every archetype declares its domain-specific ``_DETAILS`` section."""

    def test_every_archetype_declares_its_archetype_core_section(self) -> None:
        for archetype, expected_core in ARCHETYPE_CORE_SECTION.items():
            caps = get_capabilities(archetype)
            assert expected_core in caps.sections, (
                f"{archetype} must declare {expected_core.value!r} as its archetype-specific "
                "content section. Without it the wizard has nothing to render for the "
                "archetype-unique question."
            )


class TestScopeConstraints:
    """D22 invariants — verify them as unit tests so IDE-level regressions surface fast."""

    def test_edition_less_archetypes_do_not_list_edition_level_sections(self) -> None:
        """PRODUCTO + MEMBRESIA must never surface a section that only exists on launches."""
        for archetype, caps in ARCHETYPE_CATALOG.items():
            if caps.supports_editions:
                continue
            edition_only = [s for s in caps.sections if get_section(s).scope is SectionScope.EDITION_LEVEL]
            assert edition_only == [], (
                f"{archetype} does not support editions but lists EDITION_LEVEL sections "
                f"{edition_only}. Either change their scope or drop them from this archetype's "
                "sections tuple."
            )

    def test_edition_supporting_archetypes_surface_at_least_one_non_offer_section(self) -> None:
        """An archetype with editions must surface something that varies per launch."""
        for archetype, caps in ARCHETYPE_CATALOG.items():
            if not caps.supports_editions:
                continue
            non_offer = [s for s in caps.sections if get_section(s).scope is not SectionScope.OFFER_LEVEL]
            assert non_offer, (
                f"{archetype} supports editions but all its sections are OFFER_LEVEL. "
                "Users opting into editions would never see content that changes per launch. "
                "Add at least one EDITION_LEVEL or MIXED section."
            )
