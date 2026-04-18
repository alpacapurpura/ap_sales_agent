"""VariantStructure catalog — the 6th SSoT axis of the offer-studio DAG.

Declares how a single offer fragments into sellable instances
(``LaunchEdition`` rows). Pure base axis: this module is forbidden from
referencing any other catalog (``SectionCatalog``, ``ArchetypeCatalog``,
``OfferFormat``, ``ExpertBusinessType``). The coupling direction is
**inbound only** — ``ArchetypeCapabilities.supported_variant_structures``
(Sprint 8) and ``SectionMetadata`` MIXED ownership rules (Sprint 9) will
reference VariantStructure, never the other way around.

Guarantees:
    1. Every ``VariantStructure`` enum value appears in
       ``VARIANT_STRUCTURE_CATALOG``. Enforced by
       ``tests/architecture/test_variant_structure_catalog_completeness.py``.
    2. The module imports zero other catalogs. Enforced by
       ``tests/architecture/test_variant_structure_catalog_purity.py``.
    3. Metadata is frozen — mutations raise at runtime. Frozen dataclass
       with ``slots=True`` mirrors the other catalogs.

See ``docs/domains/offer/variant-structure-catalog.md`` for the design
rationale, the DAG integration, and decisions D26-D30.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from src.modules.offer.domain.enums import VariantStructure


class VariantCardinality(StrEnum):
    """How many variants a single offer can reasonably host simultaneously.

    Informational metadata — does not affect storage. Drives wizard copy
    hints and validation warnings ("usually 2-5 tiers"). Not a hard limit.
    """

    SINGULAR = "singular"  # Typically 1 active instance at a time (SINGLE_DATE).
    FEW = "few"  # 2-10 parallel (TIER, MODALITY).
    MANY = "many"  # 10+ (COHORT over time, SKU_VARIANT, REGIONAL).


class CloneCopyPolicy(StrEnum):
    """How clone-from-previous copies fields between variants.

    Governs the ``POST /editions/{id}/clone`` endpoint (Sprint 11). Each
    structure declares a policy so the clone API does the right thing
    per case — temporal clones shift dates forward, TIER clones preserve
    features but bump price, SKU clones null the attributes, etc.
    """

    TEMPORAL_SHIFT = "temporal_shift"  # Copy everything, shift dates forward by prev duration.
    PRESERVE_WITH_SUFFIX = "preserve_with_suffix"  # Copy everything, append "(copia)" to name.
    RESET_IDENTIFIERS = "reset_identifiers"  # Copy, null unique identifiers (SKU code).
    STRUCTURAL_ONLY = "structural_only"  # Copy structure_data, null dates + enrollments.


@dataclass(frozen=True, slots=True)
class VariantStructureMetadata:
    """Frozen record describing a single ``VariantStructure``.

    All fields are derivable from the enum value alone — metadata does not
    reference tenant state, other catalogs, or database rows. Changes to
    this record require a ``_CATALOG_VERSION`` bump in
    ``api/variant_structures.py`` so clients evict cached copies.
    """

    key: VariantStructure
    order: int  # 0..N-1 contiguous; drives wizard display order.

    # --- User-facing labels (Spanish) -----------------------------------
    label_es: str
    description_es: str
    noun_es: str  # singular: "cohorte", "plan", "variante".
    noun_plural_es: str  # plural: "cohortes", "planes", "variantes".
    icon_name: str  # Lucide PascalCase — resolved on the frontend.

    # --- Mechanics flags ------------------------------------------------
    # True when the structure requires a start_date (and usually end_date).
    # Drives validation: TEMPORAL_* are the only structures where a naked
    # LaunchEdition without dates is a publishing error.
    requires_temporal_anchor: bool
    # True when the structure pins to a physical or virtual location that
    # is instance-specific (single events, onsite modality).
    requires_location: bool
    # True when each variant has an independent seat count.
    supports_capacity: bool
    # True when the structure uses the Phase-4 pricing_tiers JSONB for
    # intra-variant tiered pricing (regular / early-bird / etc.). TIER
    # structures differ: the variant IS the tier, so pricing_tiers is
    # repurposed to hold the plan's single price ladder if any.
    supports_pricing_tiers: bool
    # True when the structure supports serialized ordering (plan rank,
    # SKU display order). Consumers persist this in the ``sort_rank``
    # column on ``launch_editions``.
    supports_sort_rank: bool

    # --- Clone behaviour ------------------------------------------------
    clone_policy: CloneCopyPolicy

    # --- Cardinality hint (informational) -------------------------------
    cardinality: VariantCardinality

    # --- JSONB schema contract ------------------------------------------
    # Field names (structure_data JSONB keys) required when publishing a
    # variant of this structure. Empty tuple = structure has no
    # structure-specific required payload beyond the base columns.
    required_structure_data_fields: tuple[str, ...] = field(default_factory=tuple)
    # Field names that structures must NOT persist (guard rails — e.g.
    # TIER must not persist start_date; SKU_VARIANT must not persist
    # timezone). These flag misuse at service-layer validation.
    forbidden_base_fields: tuple[str, ...] = field(default_factory=tuple)

    # --- Wizard hints (Spanish) -----------------------------------------
    # Copy for the future "¿cómo varía tu oferta?" wizard step
    # (Sprint 8+). Optional — None means the structure is not yet surfaced
    # to wizards.
    wizard_prompt_es: str | None = None


VARIANT_STRUCTURE_CATALOG: dict[VariantStructure, VariantStructureMetadata] = {
    VariantStructure.TEMPORAL_COHORT: VariantStructureMetadata(
        key=VariantStructure.TEMPORAL_COHORT,
        order=0,
        label_es="Cohortes",
        description_es=(
            "Grupos de alumnos que empiezan y terminan juntos en fechas fijas. "
            "Cada cohorte es una edición con fechas propias."
        ),
        noun_es="cohorte",
        noun_plural_es="cohortes",
        icon_name="Users",
        requires_temporal_anchor=True,
        requires_location=False,
        supports_capacity=True,
        supports_pricing_tiers=True,
        supports_sort_rank=False,
        clone_policy=CloneCopyPolicy.TEMPORAL_SHIFT,
        cardinality=VariantCardinality.MANY,
        required_structure_data_fields=(),
        forbidden_base_fields=(),
        wizard_prompt_es="¿Se dictará en cohortes con fechas fijas?",
    ),
    VariantStructure.TEMPORAL_SINGLE_DATE: VariantStructureMetadata(
        key=VariantStructure.TEMPORAL_SINGLE_DATE,
        order=1,
        label_es="Salidas",
        description_es=(
            "Un evento o experiencia que ocurre en una fecha puntual (webinar, retiro, taller presencial)."
        ),
        noun_es="salida",
        noun_plural_es="salidas",
        icon_name="Calendar",
        requires_temporal_anchor=True,
        requires_location=True,
        supports_capacity=True,
        supports_pricing_tiers=True,
        supports_sort_rank=False,
        clone_policy=CloneCopyPolicy.TEMPORAL_SHIFT,
        cardinality=VariantCardinality.SINGULAR,
        required_structure_data_fields=(),
        forbidden_base_fields=(),
        wizard_prompt_es="¿Se repetirá en varias fechas?",
    ),
    VariantStructure.RECURRING_INTAKE: VariantStructureMetadata(
        key=VariantStructure.RECURRING_INTAKE,
        order=2,
        label_es="Convocatorias",
        description_es=(
            "Servicios que abren inscripciones en batches periódicos. "
            "Cada convocatoria es una edición con inicio agendado."
        ),
        noun_es="convocatoria",
        noun_plural_es="convocatorias",
        icon_name="CalendarClock",
        requires_temporal_anchor=True,
        requires_location=False,
        supports_capacity=True,
        supports_pricing_tiers=True,
        supports_sort_rank=False,
        clone_policy=CloneCopyPolicy.TEMPORAL_SHIFT,
        cardinality=VariantCardinality.MANY,
        required_structure_data_fields=(),
        forbidden_base_fields=(),
        wizard_prompt_es="¿Se ofrecerá en convocatorias agrupadas?",
    ),
    VariantStructure.TIER: VariantStructureMetadata(
        key=VariantStructure.TIER,
        order=3,
        label_es="Planes",
        description_es=(
            "Niveles paralelos de la misma oferta con precio y beneficios distintos (gold / platinum / básico / pro)."
        ),
        noun_es="plan",
        noun_plural_es="planes",
        icon_name="Layers",
        requires_temporal_anchor=False,
        requires_location=False,
        supports_capacity=False,
        supports_pricing_tiers=False,
        supports_sort_rank=True,
        clone_policy=CloneCopyPolicy.PRESERVE_WITH_SUFFIX,
        cardinality=VariantCardinality.FEW,
        required_structure_data_fields=("features", "price_amount", "price_currency"),
        forbidden_base_fields=("start_date", "end_date", "registration_start", "registration_end"),
        wizard_prompt_es="¿Tiene distintos planes o niveles?",
    ),
    VariantStructure.SKU_VARIANT: VariantStructureMetadata(
        key=VariantStructure.SKU_VARIANT,
        order=4,
        label_es="Variantes de producto",
        description_es=(
            "Versiones del mismo producto que se diferencian por atributos "
            "(talla, color, material). Cada variante tiene su propio SKU e inventario."
        ),
        noun_es="variante",
        noun_plural_es="variantes",
        icon_name="Package",
        requires_temporal_anchor=False,
        requires_location=False,
        supports_capacity=True,
        supports_pricing_tiers=False,
        supports_sort_rank=True,
        clone_policy=CloneCopyPolicy.RESET_IDENTIFIERS,
        cardinality=VariantCardinality.MANY,
        required_structure_data_fields=("attributes", "sku_code"),
        forbidden_base_fields=("start_date", "end_date", "registration_start", "registration_end"),
        wizard_prompt_es="¿Tiene variantes (talla, color, material)?",
    ),
    VariantStructure.REGIONAL: VariantStructureMetadata(
        key=VariantStructure.REGIONAL,
        order=5,
        label_es="Variantes regionales",
        description_es=(
            "Misma oferta adaptada por país o región: precio, moneda, impuestos e idioma local. "
            "Cada región es una edición."
        ),
        noun_es="región",
        noun_plural_es="regiones",
        icon_name="Globe",
        requires_temporal_anchor=False,
        requires_location=False,
        supports_capacity=False,
        supports_pricing_tiers=True,
        supports_sort_rank=True,
        clone_policy=CloneCopyPolicy.PRESERVE_WITH_SUFFIX,
        cardinality=VariantCardinality.FEW,
        required_structure_data_fields=("country_codes", "currency"),
        forbidden_base_fields=("start_date", "end_date", "registration_start", "registration_end"),
        wizard_prompt_es="¿Cambia por país o región (precio, moneda, idioma)?",
    ),
    VariantStructure.MODALITY: VariantStructureMetadata(
        key=VariantStructure.MODALITY,
        order=6,
        label_es="Modalidades",
        description_es=(
            "Misma oferta entregada en formato distinto: presencial, online o híbrido. "
            "Cada modalidad tiene logística y a veces precio distinto."
        ),
        noun_es="modalidad",
        noun_plural_es="modalidades",
        icon_name="MonitorSmartphone",
        requires_temporal_anchor=False,
        requires_location=False,
        supports_capacity=True,
        supports_pricing_tiers=True,
        supports_sort_rank=True,
        clone_policy=CloneCopyPolicy.PRESERVE_WITH_SUFFIX,
        cardinality=VariantCardinality.FEW,
        required_structure_data_fields=("mode",),
        forbidden_base_fields=(),
        wizard_prompt_es="¿Se entrega en distintas modalidades (presencial / online)?",
    ),
    VariantStructure.LANGUAGE: VariantStructureMetadata(
        key=VariantStructure.LANGUAGE,
        order=7,
        label_es="Idiomas",
        description_es=(
            "Misma oferta disponible en distintos idiomas. Cada idioma es una edición con copy y material traducidos."
        ),
        noun_es="idioma",
        noun_plural_es="idiomas",
        icon_name="Languages",
        requires_temporal_anchor=False,
        requires_location=False,
        supports_capacity=False,
        supports_pricing_tiers=False,
        supports_sort_rank=True,
        clone_policy=CloneCopyPolicy.PRESERVE_WITH_SUFFIX,
        cardinality=VariantCardinality.FEW,
        required_structure_data_fields=("locale",),
        forbidden_base_fields=(),
        wizard_prompt_es="¿Se ofrece en más de un idioma?",
    ),
}


def get_variant_structure_metadata(structure: VariantStructure) -> VariantStructureMetadata:
    """Return the metadata record for ``structure``.

    The architecture test
    ``test_variant_structure_catalog_completeness`` guarantees every enum
    value has an entry, so in practice this lookup cannot raise at
    runtime. The explicit ``KeyError`` path is kept for defensive
    programming only.
    """
    return VARIANT_STRUCTURE_CATALOG[structure]
