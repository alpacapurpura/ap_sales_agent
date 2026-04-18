"""Architecture fitness: VariantStructure ↔ VARIANT_STRUCTURE_CATALOG alignment.

Prevents silent drift between the ``VariantStructure`` enum and the
``VARIANT_STRUCTURE_CATALOG`` dict that the 6th SSoT axis relies on.
Mirrors the pattern used by the other catalog gates
(``test_archetype_catalog_completeness``,
``test_section_catalog_completeness``,
``test_value_level_catalog_completeness``).

Failing this gate means a new structure was added without its metadata
record, or a metadata record was left orphaned after an enum deletion —
both of which break frontend consumers that read the catalog endpoint.

Related:
    - ``variant_structure_catalog.py`` — catalog data.
    - ``test_variant_structure_catalog_purity.py`` — zero-outbound-FK gate.
    - ``tests/modules/offer/domain/test_variant_structure_catalog.py``
      — semantic invariants (per-structure field coherence).
"""

from __future__ import annotations

from src.modules.offer.domain.enums import VariantStructure
from src.modules.offer.domain.variant_structure_catalog import (
    VARIANT_STRUCTURE_CATALOG,
    CloneCopyPolicy,
    VariantCardinality,
)


def test_every_variant_structure_has_a_catalog_entry() -> None:
    missing = [s for s in VariantStructure if s not in VARIANT_STRUCTURE_CATALOG]
    assert missing == [], (
        "Every VariantStructure must have a VARIANT_STRUCTURE_CATALOG entry. "
        f"Missing: {missing}. "
        "Add a record to variant_structure_catalog.py declaring label_es, "
        "noun_es, mechanics flags, clone_policy, cardinality, and optional "
        "required/forbidden field names."
    )


def test_catalog_has_no_orphan_entries() -> None:
    enum_values = set(VariantStructure)
    catalog_values = set(VARIANT_STRUCTURE_CATALOG.keys())
    orphans = catalog_values - enum_values
    assert orphans == set(), (
        f"VARIANT_STRUCTURE_CATALOG has entries for keys that no longer exist in the VariantStructure enum: {orphans}"
    )


def test_catalog_records_self_reference_their_key() -> None:
    for structure, metadata in VARIANT_STRUCTURE_CATALOG.items():
        assert metadata.key is structure, (
            f"Catalog entry for {structure} declares key={metadata.key} — "
            "every metadata record MUST reference its own enum value in "
            "the ``key`` field."
        )


def test_orders_are_unique_and_contiguous() -> None:
    orders = sorted(m.order for m in VARIANT_STRUCTURE_CATALOG.values())
    expected = list(range(len(VARIANT_STRUCTURE_CATALOG)))
    assert orders == expected, (
        f"VariantStructure orders must be unique and contiguous from 0. "
        f"Got {orders}, expected {expected}. Bump or shift existing orders "
        "when inserting a new structure."
    )


def test_every_entry_has_non_empty_spanish_copy() -> None:
    for structure, metadata in VARIANT_STRUCTURE_CATALOG.items():
        assert metadata.label_es.strip(), f"{structure} has empty label_es"
        assert metadata.description_es.strip(), f"{structure} has empty description_es"
        assert metadata.noun_es.strip(), f"{structure} has empty noun_es"
        assert metadata.noun_plural_es.strip(), f"{structure} has empty noun_plural_es"
        assert metadata.icon_name.strip(), f"{structure} has empty icon_name"


def test_icon_names_are_pascal_case() -> None:
    for structure, metadata in VARIANT_STRUCTURE_CATALOG.items():
        first = metadata.icon_name[0]
        assert first.isupper(), (
            f"{structure} icon_name '{metadata.icon_name}' must be PascalCase "
            "to match Lucide React convention — the frontend resolver maps "
            "PascalCase strings to icon components."
        )


def test_clone_policy_is_a_valid_enum_value() -> None:
    for structure, metadata in VARIANT_STRUCTURE_CATALOG.items():
        assert metadata.clone_policy in CloneCopyPolicy, (
            f"{structure} declares clone_policy={metadata.clone_policy!r} which is not a valid CloneCopyPolicy value."
        )


def test_cardinality_is_a_valid_enum_value() -> None:
    for structure, metadata in VARIANT_STRUCTURE_CATALOG.items():
        assert metadata.cardinality in VariantCardinality, (
            f"{structure} declares cardinality={metadata.cardinality!r} which is not a valid VariantCardinality value."
        )


def test_forbidden_base_fields_reference_known_columns() -> None:
    """Guard rail: ``forbidden_base_fields`` must name real LaunchEdition columns.

    Typos here would silently bypass validation at service layer. The
    allowed set is the subset of ``LaunchEditionModel`` columns that
    make semantic sense to forbid per-structure (dates, capacity,
    location).
    """
    allowed_columns = {
        "start_date",
        "end_date",
        "registration_start",
        "registration_end",
        "timezone",
        "location_override",
        "capacity",
        "pricing_tiers",
        "pricing_override",
    }
    for structure, metadata in VARIANT_STRUCTURE_CATALOG.items():
        unknown = set(metadata.forbidden_base_fields) - allowed_columns
        assert unknown == set(), (
            f"{structure}.forbidden_base_fields references unknown columns: {unknown}. "
            f"Allowed: {sorted(allowed_columns)}. "
            "Fix the typo or add the column to the allowed set if it is a legitimate target."
        )


def test_temporal_structures_require_temporal_anchor() -> None:
    """Semantic gate: TEMPORAL_* structures must declare ``requires_temporal_anchor``.

    Anything else is a contradiction — a "temporal" variant without a
    date anchor would be a non-temporal variant.
    """
    temporal_keys = {
        VariantStructure.TEMPORAL_COHORT,
        VariantStructure.TEMPORAL_SINGLE_DATE,
        VariantStructure.RECURRING_INTAKE,
    }
    for structure in temporal_keys:
        metadata = VARIANT_STRUCTURE_CATALOG[structure]
        assert metadata.requires_temporal_anchor, (
            f"{structure} is a temporal variant but declares "
            "requires_temporal_anchor=False. This is a semantic contradiction."
        )


def test_non_temporal_structures_forbid_date_columns() -> None:
    """Non-temporal structures must forbid start/end/registration dates.

    Otherwise TIER / SKU / REGIONAL would accept stray dates that the
    editor would then render, confusing users. The guard rail is
    declarative: the catalog lists the columns; the service layer
    enforces the ban at write time.
    """
    non_temporal_keys = {
        VariantStructure.TIER,
        VariantStructure.SKU_VARIANT,
        VariantStructure.REGIONAL,
    }
    required_forbidden = {
        "start_date",
        "end_date",
        "registration_start",
        "registration_end",
    }
    for structure in non_temporal_keys:
        metadata = VARIANT_STRUCTURE_CATALOG[structure]
        missing = required_forbidden - set(metadata.forbidden_base_fields)
        assert not missing, (
            f"{structure} is non-temporal but does not forbid {missing}. "
            "Add the columns to forbidden_base_fields so the service "
            "layer rejects stray date assignments."
        )
