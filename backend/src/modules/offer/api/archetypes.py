"""Archetypes API — exposes the ArchetypeCapabilities catalog to clients.

The catalog is domain metadata (not tenant-scoped), so these endpoints are
public and highly cacheable. Frontend consumes them to render wizard copy,
edition-related UI conditionals, and archetype pickers.

Since Sprint 6 Phase A.5, the response also carries per-archetype section
lists (mirroring the former frontend ``ARCHETYPE_BUILDER_CONFIG``) and a
global ``section_catalog`` so clients can resolve metadata for any
``SectionKey`` without a second round-trip. See ``SECTION_CATALOG`` in
``section_catalog.py`` and ``SPRINT-6-PLAN.md`` §Phase A.5 for context.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from src.modules.offer.domain.archetype_catalog import (
    ARCHETYPE_CATALOG,
    ArchetypeCapabilities,
)
from src.modules.offer.domain.section_catalog import (
    SECTION_CATALOG,
    SectionKey,
    SectionMetadata,
)

router = APIRouter()


class EditionsWizardCopyDTO(BaseModel):
    """Spanish copy for the 'will this offer have editions?' wizard step."""

    model_config = ConfigDict(frozen=True)

    title: str
    description: str
    yes_label: str
    no_label: str


class SectionMetadataDTO(BaseModel):
    """DTO mirror of :class:`SectionMetadata`.

    Declared explicitly (not derived) because the domain dataclass uses
    ``slots`` and is pydantic-unaware. Preserves the DDD boundary between
    domain and API.
    """

    model_config = ConfigDict(frozen=True)

    key: str
    label_es: str
    subtitle_es: str
    help_text_es: str
    icon_name: str
    scope: str  # OFFER_LEVEL | EDITION_LEVEL | MIXED — lowercase values per StrEnum.
    completion_weight: float
    required_to_publish: bool

    @classmethod
    def from_domain(cls, meta: SectionMetadata) -> SectionMetadataDTO:
        """Build a DTO from the frozen domain record."""
        return cls(
            key=meta.key.value,
            label_es=meta.label_es,
            subtitle_es=meta.subtitle_es,
            help_text_es=meta.help_text_es,
            icon_name=meta.icon_name,
            scope=meta.scope.value,
            completion_weight=meta.completion_weight,
            required_to_publish=meta.required_to_publish,
        )

    @classmethod
    def from_key(cls, key: SectionKey) -> SectionMetadataDTO:
        """Build a DTO by looking up the canonical metadata for ``key``."""
        return cls.from_domain(SECTION_CATALOG[key])


class ArchetypeCapabilitiesDTO(BaseModel):
    """DTO mirror of :class:`ArchetypeCapabilities`.

    Declared explicitly (not derived) because the domain dataclass uses
    ``slots`` and is pydantic-unaware — keeping a dedicated DTO preserves
    the DDD boundary between domain and API.
    """

    model_config = ConfigDict(frozen=True)

    archetype: str
    supports_editions: bool
    edition_structure: str
    edition_noun_es: str
    edition_noun_plural_es: str
    requires_start_date_on_publish: bool
    requires_end_date_on_publish: bool
    requires_location_on_publish: bool
    supports_capacity: bool
    supports_waitlist: bool
    default_delivery: str
    default_fulfillment: str
    label_es: str
    subtitle_es: str
    icon_name: str
    examples_es: list[str]
    editions_wizard_copy: EditionsWizardCopyDTO | None = None
    # Ordered per archetype — clients render the nav rail in this order.
    # Each entry is the full metadata record (not just the key) so clients
    # avoid a second lookup against ``section_catalog`` for rail rendering.
    sections: list[SectionMetadataDTO]

    @classmethod
    def from_domain(cls, caps: ArchetypeCapabilities) -> ArchetypeCapabilitiesDTO:
        """Build a DTO from the frozen domain record."""
        wizard_copy: EditionsWizardCopyDTO | None = None
        if caps.supports_editions and caps.editions_wizard_title_es:
            wizard_copy = EditionsWizardCopyDTO(
                title=caps.editions_wizard_title_es,
                description=caps.editions_wizard_description_es or "",
                yes_label=caps.editions_wizard_yes_label_es or "",
                no_label=caps.editions_wizard_no_label_es or "",
            )
        return cls(
            archetype=caps.archetype.value,
            supports_editions=caps.supports_editions,
            edition_structure=caps.edition_structure.value,
            edition_noun_es=caps.edition_noun_es,
            edition_noun_plural_es=caps.edition_noun_plural_es,
            requires_start_date_on_publish=caps.requires_start_date_on_publish,
            requires_end_date_on_publish=caps.requires_end_date_on_publish,
            requires_location_on_publish=caps.requires_location_on_publish,
            supports_capacity=caps.supports_capacity,
            supports_waitlist=caps.supports_waitlist,
            default_delivery=caps.default_delivery.value,
            default_fulfillment=caps.default_fulfillment.value,
            label_es=caps.label_es,
            subtitle_es=caps.subtitle_es,
            icon_name=caps.icon_name,
            examples_es=list(caps.examples_es),
            editions_wizard_copy=wizard_copy,
            sections=[SectionMetadataDTO.from_key(key) for key in caps.sections],
        )


class ArchetypeCatalogResponse(BaseModel):
    """Wrapper so clients can cache the whole catalog by version string."""

    model_config = ConfigDict(frozen=True)

    version: str  # bump when the catalog changes → cache-buster for the frontend
    archetypes: list[ArchetypeCapabilitiesDTO]
    # Global section metadata — lets clients render any section referenced
    # by any archetype (or by future consumers like copilot) without making
    # per-key lookups.
    section_catalog: list[SectionMetadataDTO]


# Bump this when ``archetype_catalog.py`` OR ``section_catalog.py`` changes
# materially. Clients use it as the cache key so old copies are evicted on
# deploy.
_CATALOG_VERSION = "2026-04-18-section-enriched"


@router.get(
    "/catalog",
    response_model=ArchetypeCatalogResponse,
    summary="Offer archetype capabilities catalog (public, cacheable)",
)
async def get_archetype_catalog() -> ArchetypeCatalogResponse:
    """Return capabilities for every offer archetype plus the global section catalog.

    Not tenant-scoped — this is domain metadata shared across tenants.
    """
    return ArchetypeCatalogResponse(
        version=_CATALOG_VERSION,
        archetypes=[ArchetypeCapabilitiesDTO.from_domain(c) for c in ARCHETYPE_CATALOG.values()],
        section_catalog=[SectionMetadataDTO.from_domain(m) for m in SECTION_CATALOG.values()],
    )
