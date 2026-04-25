"""Cross-cutting fitness tests for the FieldContract platform.

Enforces that consumers (editable_fields catalog, persistable_fields,
extraction grouping) stay derived from the platform registry — drift
between paralllel registries is blocked by these tests.

Add a module to ``MIGRATED_MODULES`` here when its FieldContract is
declared (Fase 06 brand, 07 buyer_persona). For non-migrated modules,
their consumers may still use legacy hand-written catalogs.

refs: docs/refactors/field-contract-platform/DESIGN.md
"""

from __future__ import annotations

from src.modules.brand.domain.aggregates import BrandSettings
from src.modules.brand.domain.copilot_editable_fields import BRAND_EDITABLE_FIELDS
from src.modules.brand.domain.field_contract import (
    BRAND_COMPOSABLE_FIELDS,
    BRAND_FIELD_CONTRACTS,
    BRAND_IGNORE_PATHS,
    BRAND_SECTION_MAP,
)
from src.modules.copilot.domain.offer_fields import PERSISTABLE_FIELDS
from src.modules.offer.domain.copilot_editable_fields import OFFER_EDITABLE_FIELDS
from src.modules.offer.domain.details import (
    EventDetails,
    PlatformDetails,
    ProductDetails,
    ProgramDetails,
    ServiceDetails,
    SubscriptionDetails,
)
from src.modules.offer.domain.field_contract import (
    OFFER_FIELD_CONTRACTS,
    OFFER_IGNORE_PATHS,
    OFFER_SECTION_MAP,
)
from src.modules.offer.domain.offer import Offer
from src.shared.domain.field_contract import FieldStatus

# Modules that have migrated to the platform. Add buyer_persona in Fase 07.
# Tests here apply only to migrated modules — non-migrated catalogs follow
# the legacy pattern.
MIGRATED_MODULES: tuple[str, ...] = ("offer", "brand")


# ---------------------------------------------------------------------------
# Pydantic ⊆ FieldContract per migrated module
# ---------------------------------------------------------------------------


def _all_offer_pydantic_paths() -> set[str]:
    """Build the set of Offer Pydantic paths user-facing.

    Includes top-level Offer fields + every variant of ``specific_details``
    (with prefix) + every PlatformDetails field (with prefix).
    """
    paths: set[str] = set(Offer.model_fields.keys())
    for cls in (ProductDetails, ServiceDetails, ProgramDetails, SubscriptionDetails, EventDetails):
        for fname in cls.model_fields:
            paths.add(f"specific_details.{fname}")
    for fname in PlatformDetails.model_fields:
        paths.add(f"platform_details.{fname}")
    return paths


def _all_brand_pydantic_paths() -> set[str]:
    """Build the set of BrandSettings Pydantic paths user-facing.

    Top-level fields plus every nested Pydantic field walked one level
    deep (composable handles). Top-level lists (team, testimonials,
    authority_vault) appear as their bare names — emitted as LIST contracts.
    """
    paths: set[str] = set()
    for fname, finfo in BrandSettings.model_fields.items():
        if fname not in BRAND_COMPOSABLE_FIELDS:
            paths.add(fname)
            continue
        annotation = finfo.annotation
        # ``X | None`` -> X (composable nested model)
        from types import UnionType  # local import to keep top imports clean
        from typing import Union, get_args, get_origin

        if get_origin(annotation) in (Union, UnionType):
            args = [a for a in get_args(annotation) if a is not type(None)]
            if len(args) == 1:
                annotation = args[0]
        nested_fields = getattr(annotation, "model_fields", None)
        if nested_fields:
            for sub_name in nested_fields:
                paths.add(f"{fname}.{sub_name}")
    return paths


class TestPydanticSubsetOfFieldContract:
    """Every user-facing Pydantic field has a FieldContract entry."""

    def test_offer_model_fields_subset_of_field_contract(self) -> None:
        """Pydantic Offer + nested ⊆ OFFER_FIELD_CONTRACTS (excluding IGNORE)."""
        pydantic_paths = _all_offer_pydantic_paths()
        contract_paths = {c.path for c in OFFER_FIELD_CONTRACTS}
        # ``specific_details`` and ``platform_details`` are top-level Pydantic
        # fields handled by the walker as polymorphic / composable — their
        # subfields appear in the registry with a prefix, the bare names do
        # not (and don't need to).
        composable_handles: set[str] = {"specific_details", "platform_details"}
        expected = pydantic_paths - OFFER_IGNORE_PATHS - composable_handles
        missing = expected - contract_paths
        assert not missing, (
            f"Pydantic Offer / nested fields without a FieldContract entry: "
            f"{sorted(missing)}.\nAdd them to OFFER_SECTION_MAP (or "
            f"OFFER_IGNORE_PATHS if internal) in offer/domain/field_contract.py."
        )

    def test_brand_model_fields_subset_of_field_contract(self) -> None:
        """Pydantic BrandSettings + nested ⊆ BRAND_FIELD_CONTRACTS."""
        pydantic_paths = _all_brand_pydantic_paths()
        contract_paths = {c.path for c in BRAND_FIELD_CONTRACTS}
        # Composable handles: bare name not in registry, sub-paths are.
        composable_handles = set(BRAND_COMPOSABLE_FIELDS)
        expected = pydantic_paths - BRAND_IGNORE_PATHS - composable_handles
        missing = expected - contract_paths
        assert not missing, (
            f"Pydantic BrandSettings / nested fields without a FieldContract entry: "
            f"{sorted(missing)}.\nAdd them to BRAND_SECTION_MAP (or "
            f"BRAND_IGNORE_PATHS if internal) in brand/domain/field_contract.py."
        )

    def test_brand_section_map_covers_every_pydantic_path(self) -> None:
        """Every BRAND_FIELD_CONTRACTS path has a BRAND_SECTION_MAP entry."""
        contract_paths = {c.path for c in BRAND_FIELD_CONTRACTS}
        section_paths = set(BRAND_SECTION_MAP.keys())
        # Section map is the source — every contract must have come from it.
        orphans = contract_paths - section_paths
        assert not orphans, (
            f"Brand contracts without a BRAND_SECTION_MAP entry: {sorted(orphans)}. "
            f"Walker derived them from Pydantic but the section was looked up "
            f"from default_section / override.section instead."
        )


# ---------------------------------------------------------------------------
# Consumer projections ⊆ FieldContract paths
# ---------------------------------------------------------------------------


class TestEditableFieldsSubsetOfFieldContract:
    """copilot_editable_fields catalog ⊆ FieldContract paths.

    Detects manual additions to ``OFFER_EDITABLE_FIELDS`` that bypass
    the registry (defeats the purpose of the platform).
    """

    def test_offer_editable_fields_paths_in_field_contract(self) -> None:
        contract_paths = {c.path for c in OFFER_FIELD_CONTRACTS}
        editable_paths = {f.path for f in OFFER_EDITABLE_FIELDS}
        leaks = editable_paths - contract_paths
        assert not leaks, (
            f"OFFER_EDITABLE_FIELDS contains paths not in FieldContract: "
            f"{sorted(leaks)}. Catalog must derive from the registry — see "
            f"offer/domain/copilot_editable_fields.py."
        )

    def test_offer_editable_fields_only_active_can_propose(self) -> None:
        """Catalog only emits ACTIVE + can_propose=True contracts."""
        active_proposable = {c.path for c in OFFER_FIELD_CONTRACTS if c.can_propose and c.status == FieldStatus.ACTIVE}
        editable_paths = {f.path for f in OFFER_EDITABLE_FIELDS}
        # Catalog should match the proposable subset (modulo dedup of
        # polymorphic shared paths — both share-path contracts produce
        # one editable entry).
        assert editable_paths == active_proposable, (
            f"OFFER_EDITABLE_FIELDS diverged from active-proposable subset.\n"
            f"Missing in catalog: {sorted(active_proposable - editable_paths)}\n"
            f"Extra in catalog: {sorted(editable_paths - active_proposable)}"
        )


class TestPersistableFieldsSubsetOfFieldContract:
    """copilot.offer_fields.PERSISTABLE_FIELDS ⊆ FieldContract paths."""

    def test_persistable_fields_paths_in_field_contract(self) -> None:
        contract_paths = {c.path for c in OFFER_FIELD_CONTRACTS}
        leaks = PERSISTABLE_FIELDS - contract_paths
        assert not leaks, (
            f"PERSISTABLE_FIELDS contains paths not in FieldContract: "
            f"{sorted(leaks)}. Set must derive from the registry — see "
            f"copilot/domain/offer_fields.py."
        )

    def test_persistable_fields_equals_active_can_propose(self) -> None:
        """PERSISTABLE_FIELDS == set of ACTIVE + can_propose paths."""
        expected = {c.path for c in OFFER_FIELD_CONTRACTS if c.can_propose and c.status == FieldStatus.ACTIVE}
        assert expected == PERSISTABLE_FIELDS, (
            f"PERSISTABLE_FIELDS diverged.\n"
            f"Missing: {sorted(expected - PERSISTABLE_FIELDS)}\n"
            f"Extra: {sorted(PERSISTABLE_FIELDS - expected)}"
        )


# ---------------------------------------------------------------------------
# SECTION_MAP completeness for top-level fields
# ---------------------------------------------------------------------------


class TestSectionMapCompleteness:
    """Every Offer top-level Pydantic field has a section (or is ignored)."""

    def test_offer_top_level_fields_have_section(self) -> None:
        top_level_paths = set(Offer.model_fields.keys())
        # `specific_details` and `platform_details` are handled by the walker
        # as composable / polymorphic — they don't need a top-level entry.
        composables = {"specific_details", "platform_details"}
        expected = top_level_paths - OFFER_IGNORE_PATHS - composables
        missing = expected - set(OFFER_SECTION_MAP.keys())
        assert not missing, (
            f"Top-level Offer fields without a section in OFFER_SECTION_MAP: "
            f"{sorted(missing)}. Add them to OFFER_SECTION_MAP or OFFER_IGNORE_PATHS."
        )


# ---------------------------------------------------------------------------
# Field lifecycle invariants
# ---------------------------------------------------------------------------


class TestFieldLifecycle:
    """Lifecycle invariants per ADR-013."""

    def test_deprecated_contracts_have_deprecation_metadata(self) -> None:
        """status=DEPRECATED contracts must declare deprecated_in."""
        violations: list[str] = []
        for c in OFFER_FIELD_CONTRACTS:
            if c.status == FieldStatus.DEPRECATED and not c.deprecated_in:
                violations.append(c.path)
        assert not violations, (
            f"Deprecated contracts without deprecated_in: {violations}. "
            f"Set deprecated_in='YYYY-MM-DD-fase-NN' in the override."
        )

    def test_replaced_by_paths_resolve(self) -> None:
        """If replaced_by is set, it must point to an existing contract path."""
        contract_paths = {c.path for c in OFFER_FIELD_CONTRACTS}
        violations: list[str] = []
        for c in OFFER_FIELD_CONTRACTS:
            if c.replaced_by and c.replaced_by not in contract_paths:
                violations.append(f"{c.path} → {c.replaced_by}")
        assert not violations, f"replaced_by paths don't resolve to existing contracts: {violations}"


# ---------------------------------------------------------------------------
# Cross-module import boundary
# ---------------------------------------------------------------------------


class TestPlatformImportBoundary:
    """The shared platform module must not import any modules/."""

    def test_shared_field_contract_no_module_imports(self) -> None:
        """src/shared/domain/field_contract.py must not import from src/modules/."""
        from pathlib import Path

        shared = Path(__file__).parent.parent.parent / "src" / "shared" / "domain" / "field_contract.py"
        content = shared.read_text(encoding="utf-8")
        leaks = [
            line.rstrip()
            for line in content.splitlines()
            if line.lstrip().startswith(("import ", "from ")) and "src.modules" in line
        ]
        assert not leaks, (
            f"src/shared/domain/field_contract.py imports from modules/: {leaks}. "
            f"Shared platform code must stay framework-/module-agnostic."
        )
