"""Brand Studio section catalog — single source of truth for editor sections.

Mirrors the offer-studio pattern at
``backend/src/modules/offer/domain/section_catalog.py``. Previously the
labels + icons + kind lived hardcoded in
``frontend/src/features/brand-studio/lib/section-catalog.ts::BRAND_SECTIONS``
— promoted to BE so both studios share one discovery surface (Fase 03 ·
Block C).

Architecture
~~~~~~~~~~~~
Each ``BrandSectionKey`` is a stable id for an editor bloc. The catalog
declares Spanish copy (label) tuned for Latam microempresarios. ``kind``
drives the form-runtime dispatch: ``collection`` sections edit a list with
landing + detail routes (buyer personas, team, testimonials, authority),
``singleton`` sections edit a single form.

Unlike the offer-studio catalog, brand sections are NOT archetype-filtered
— every tenant sees the same 14 entries. If per-tenant hiding ever
becomes necessary, add a filter layer in a future phase.

Invariants (arch-test-enforced)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Every ``BrandSectionKey`` enum member has a matching
   ``BRAND_SECTION_CATALOG`` entry.
2. No orphan catalog entries (no keys without an enum member).
3. Every entry declares non-empty label + icon + kind.
4. Every entry self-references its key (``entry.key is enum_value``).
5. ``icon_name`` strings align with frontend ``icon-name-resolver.ts``
   — FE test ``test-no-hardcoded-section-list`` enforces.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class BrandSectionKey(StrEnum):
    """Stable identifier for a Brand Studio editor section.

    Values match the frontend section slug and URL segment verbatim.
    """

    PUBLICO = "publico"
    IDENTITY = "identity"
    ESTILO = "estilo"
    POSITIONING = "positioning"
    NARRATIVE = "narrative"
    METHODOLOGY = "methodology"
    STORY = "story"
    TEAM = "team"
    AUTHORITY = "authority"
    TESTIMONIALS = "testimonials"
    VISUALS = "visuals"
    COMMUNICATION_ASSETS = "communication-assets"
    CONTACT = "contact"
    LEGAL = "legal"


class BrandSectionKind(StrEnum):
    """Editing UX mode. Mirror of ``offer.domain.section_catalog.SectionKind``.

    - ``SINGLETON``: single-form section (identity, positioning, story, …).
    - ``COLLECTION``: list-based section with landing + detail routes
      (publico/buyer personas, team, authority, testimonials).
    """

    SINGLETON = "singleton"
    COLLECTION = "collection"


@dataclass(frozen=True, slots=True)
class BrandSectionMetadata:
    """Frozen record describing a single brand-studio editor section."""

    key: BrandSectionKey
    label_es: str
    icon_name: str
    kind: BrandSectionKind


BRAND_SECTION_CATALOG: dict[BrandSectionKey, BrandSectionMetadata] = {
    BrandSectionKey.PUBLICO: BrandSectionMetadata(
        key=BrandSectionKey.PUBLICO,
        label_es="Buyer personas",
        icon_name="Sparkles",
        kind=BrandSectionKind.COLLECTION,
    ),
    BrandSectionKey.IDENTITY: BrandSectionMetadata(
        key=BrandSectionKey.IDENTITY,
        label_es="Identidad",
        icon_name="Fingerprint",
        kind=BrandSectionKind.SINGLETON,
    ),
    BrandSectionKey.ESTILO: BrandSectionMetadata(
        key=BrandSectionKey.ESTILO,
        label_es="Estilo Comunicacional",
        icon_name="MessageCircle",
        kind=BrandSectionKind.SINGLETON,
    ),
    BrandSectionKey.POSITIONING: BrandSectionMetadata(
        key=BrandSectionKey.POSITIONING,
        label_es="Posicionamiento",
        icon_name="Target",
        kind=BrandSectionKind.SINGLETON,
    ),
    BrandSectionKey.NARRATIVE: BrandSectionMetadata(
        key=BrandSectionKey.NARRATIVE,
        label_es="Narrativa",
        icon_name="ScrollText",
        kind=BrandSectionKind.SINGLETON,
    ),
    BrandSectionKey.METHODOLOGY: BrandSectionMetadata(
        key=BrandSectionKey.METHODOLOGY,
        label_es="Metodología",
        icon_name="Flag",
        kind=BrandSectionKind.SINGLETON,
    ),
    BrandSectionKey.STORY: BrandSectionMetadata(
        key=BrandSectionKey.STORY,
        label_es="Historia",
        icon_name="FileText",
        kind=BrandSectionKind.SINGLETON,
    ),
    BrandSectionKey.TEAM: BrandSectionMetadata(
        key=BrandSectionKey.TEAM,
        label_es="Equipo",
        icon_name="Users",
        kind=BrandSectionKind.COLLECTION,
    ),
    BrandSectionKey.AUTHORITY: BrandSectionMetadata(
        key=BrandSectionKey.AUTHORITY,
        label_es="Autoridad",
        icon_name="Landmark",
        kind=BrandSectionKind.COLLECTION,
    ),
    BrandSectionKey.TESTIMONIALS: BrandSectionMetadata(
        key=BrandSectionKey.TESTIMONIALS,
        label_es="Testimonios",
        icon_name="Headphones",
        kind=BrandSectionKind.COLLECTION,
    ),
    BrandSectionKey.VISUALS: BrandSectionMetadata(
        key=BrandSectionKey.VISUALS,
        label_es="Visuales",
        icon_name="Palette",
        kind=BrandSectionKind.SINGLETON,
    ),
    BrandSectionKey.COMMUNICATION_ASSETS: BrandSectionMetadata(
        key=BrandSectionKey.COMMUNICATION_ASSETS,
        label_es="Assets",
        icon_name="Layers",
        kind=BrandSectionKind.SINGLETON,
    ),
    BrandSectionKey.CONTACT: BrandSectionMetadata(
        key=BrandSectionKey.CONTACT,
        label_es="Contacto",
        icon_name="Megaphone",
        kind=BrandSectionKind.SINGLETON,
    ),
    BrandSectionKey.LEGAL: BrandSectionMetadata(
        key=BrandSectionKey.LEGAL,
        label_es="Legal",
        icon_name="Scale",
        kind=BrandSectionKind.SINGLETON,
    ),
}


def get_brand_section(key: BrandSectionKey) -> BrandSectionMetadata:
    """Return the metadata record for ``key``. Raises ``KeyError`` if missing."""
    return BRAND_SECTION_CATALOG[key]
