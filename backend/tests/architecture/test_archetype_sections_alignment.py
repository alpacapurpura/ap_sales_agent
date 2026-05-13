"""Architecture fitness: archetype.sections are consistent with the SectionCatalog.

Drift between ``ArchetypeCapabilities.sections`` and the ``SECTION_CATALOG``
is a silent-failure vector — an archetype can point at a section key that
has no metadata, or list an EDITION_LEVEL section under an edition-less
archetype. These tests fail CI before the damage reaches a client.

Related:
- `SPRINT-6-PLAN.md` §Phase A.4 — this file's purpose.
- `test_archetype_sections.py` — unit tests on locked assignments.
- `section_catalog.py` — the referenced catalog.
"""

from __future__ import annotations

from luana_core_offer_studio.domain.archetype_catalog import ARCHETYPE_CATALOG
from luana_core_offer_studio.domain.section_catalog import SECTION_CATALOG, SectionScope


def test_every_archetype_declares_sections() -> None:
    for archetype, caps in ARCHETYPE_CATALOG.items():
        assert hasattr(caps, "sections"), f"{archetype} is missing the sections field"
        assert caps.sections, f"{archetype}.sections is empty"


def test_every_section_reference_has_metadata() -> None:
    for archetype, caps in ARCHETYPE_CATALOG.items():
        for section in caps.sections:
            assert section in SECTION_CATALOG, (
                f"{archetype}.sections references {section!r} which has no SECTION_CATALOG entry."
            )


def test_edition_less_archetypes_have_no_edition_level_sections() -> None:
    """D22 invariant — enforced architecturally, not just via unit tests."""
    for archetype, caps in ARCHETYPE_CATALOG.items():
        if caps.supports_editions:
            continue
        edition_only = [s for s in caps.sections if SECTION_CATALOG[s].scope is SectionScope.EDITION_LEVEL]
        assert edition_only == [], (
            f"{archetype} has supports_editions=False but lists EDITION_LEVEL sections {edition_only}. "
            "These sections would be invisible forever — drop them or change their scope."
        )


def test_edition_supporting_archetypes_have_at_least_one_non_offer_section() -> None:
    """D22 invariant — edition capability must have editor representation."""
    for archetype, caps in ARCHETYPE_CATALOG.items():
        if not caps.supports_editions:
            continue
        non_offer = [s for s in caps.sections if SECTION_CATALOG[s].scope is not SectionScope.OFFER_LEVEL]
        assert non_offer, (
            f"{archetype} supports editions but all its sections are OFFER_LEVEL. "
            "Add at least one EDITION_LEVEL or MIXED section."
        )
