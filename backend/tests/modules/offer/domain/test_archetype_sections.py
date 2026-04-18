"""Tests for ``ArchetypeCapabilities.sections`` — per-archetype section set.

Locks the section ordering for each offer archetype as declared in the
canonical catalog. Together with the scope rules enforced by
``test_archetype_section_scope_constraints`` (architecture) this is the
contract the frontend consumes via ``/api/v1/offer/archetypes/catalog``.

Related:
- `SPRINT-6-PLAN.md` §Phase A.3 — this file's purpose.
- `archetype_catalog.py` — the data under test.
- `section_catalog.py` — section metadata and scope authority.
"""

from __future__ import annotations

from src.modules.offer.domain.archetype_catalog import ARCHETYPE_CATALOG, get_capabilities
from src.modules.offer.domain.enums import OfferArchetype
from src.modules.offer.domain.section_catalog import SectionKey, SectionScope, get_section


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


class TestLockedSectionAssignments:
    """Exact section ordering per archetype (mirrors the frontend ARCHETYPE_BUILDER_CONFIG
    that Sprint 6 migrates to the backend as the single source of truth)."""

    def test_producto(self) -> None:
        assert get_capabilities(OfferArchetype.PRODUCTO).sections == (
            SectionKey.IDENTITY,
            SectionKey.STRATEGY,
            SectionKey.PSYCHOLOGY,
            SectionKey.PROMISE,
            SectionKey.PRODUCT_DETAILS,
            SectionKey.VALUE_STACK,
            SectionKey.RESOURCES,
            SectionKey.PRICING,
            SectionKey.CLOSING,
            SectionKey.KNOWLEDGE,
        )

    def test_programa(self) -> None:
        assert get_capabilities(OfferArchetype.PROGRAMA).sections == (
            SectionKey.IDENTITY,
            SectionKey.STRATEGY,
            SectionKey.PSYCHOLOGY,
            SectionKey.PROMISE,
            SectionKey.PROGRAM_DETAILS,
            SectionKey.INSTRUCTORS,
            SectionKey.VALUE_STACK,
            SectionKey.RESOURCES,
            SectionKey.PRICING,
            SectionKey.CLOSING,
            SectionKey.KNOWLEDGE,
        )

    def test_servicio(self) -> None:
        assert get_capabilities(OfferArchetype.SERVICIO).sections == (
            SectionKey.IDENTITY,
            SectionKey.STRATEGY,
            SectionKey.PSYCHOLOGY,
            SectionKey.PROMISE,
            SectionKey.SERVICE_DETAILS,
            SectionKey.INSTRUCTORS,
            SectionKey.VALUE_STACK,
            SectionKey.RESOURCES,
            SectionKey.PRICING,
            SectionKey.CLOSING,
            SectionKey.KNOWLEDGE,
        )

    def test_membresia(self) -> None:
        assert get_capabilities(OfferArchetype.MEMBRESIA).sections == (
            SectionKey.IDENTITY,
            SectionKey.STRATEGY,
            SectionKey.PSYCHOLOGY,
            SectionKey.PROMISE,
            SectionKey.SUBSCRIPTION_DETAILS,
            SectionKey.VALUE_STACK,
            SectionKey.RESOURCES,
            SectionKey.PRICING,
            SectionKey.CLOSING,
            SectionKey.KNOWLEDGE,
        )

    def test_experiencia(self) -> None:
        assert get_capabilities(OfferArchetype.EXPERIENCIA).sections == (
            SectionKey.IDENTITY,
            SectionKey.STRATEGY,
            SectionKey.PSYCHOLOGY,
            SectionKey.PROMISE,
            SectionKey.EVENT_DETAILS,
            SectionKey.INSTRUCTORS,
            SectionKey.VALUE_STACK,
            SectionKey.RESOURCES,
            SectionKey.PRICING,
            SectionKey.CLOSING,
            SectionKey.KNOWLEDGE,
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
                f"{archetype} does not support editions but lists EDITION_LEVEL sections {edition_only}. "
                "Either change their scope or drop them from this archetype's sections tuple."
            )

    def test_edition_supporting_archetypes_surface_at_least_one_non_offer_section(self) -> None:
        """An archetype with editions must surface something that varies per launch — otherwise
        the edition concept has no editor representation and users will not know why they have it."""
        for archetype, caps in ARCHETYPE_CATALOG.items():
            if not caps.supports_editions:
                continue
            non_offer = [s for s in caps.sections if get_section(s).scope is not SectionScope.OFFER_LEVEL]
            assert non_offer, (
                f"{archetype} supports editions but all its sections are OFFER_LEVEL. "
                "Users opting into editions would never see content that changes per launch. "
                "Add at least one EDITION_LEVEL or MIXED section."
            )
