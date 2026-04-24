"""Generic guards for future module migrations to FieldContract platform.

When brand (Fase 06) / buyer-persona (Fase 07) / future modules adopt
the FieldContract platform pattern, append their key to ``MIGRATED_MODULES``
in ``test_field_contract_platform_coverage.py`` AND map them to their
Pydantic root + consumers below to inherit these generic checks.

This file is intentionally **module-agnostic** — every assertion runs
once per migrated module, declared via the ``_MODULE_REGISTRY_SPECS``
table. Adding a module is one entry.

Tests are no-ops while only ``offer`` is migrated (still useful: they
exercise the generic API and catch regressions in the platform itself).

refs: docs/refactors/field-contract-platform/DESIGN.md
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pytest
from pydantic import BaseModel

from src.shared.domain.field_contract import (
    FieldContract,
    FieldStatus,
    get_module_contracts,
)


@dataclass(frozen=True)
class _ModuleRegistrySpec:
    """Specifies how to invoke generic checks on a migrated module.

    Attributes:
        name: Module key passed to ``register_module_contracts``.
        root_model: The Pydantic root entity (Offer, BrandSettings, ...).
        ignore_paths: Builder of system paths excluded from coverage.
        composable_handles: Top-level Pydantic fields that are walked
            with a prefix (their bare names don't appear in the registry).
        editable_paths_provider: Callable returning the catalog paths the
            module exposes to the copilot ``editable_fields`` port.
            ``None`` if the module doesn't expose a write-surface.
    """

    name: str
    root_model: type[BaseModel]
    ignore_paths: frozenset[str]
    composable_handles: frozenset[str]
    editable_paths_provider: Callable[[], frozenset[str]] | None


def _offer_spec() -> _ModuleRegistrySpec:
    """Offer module spec. Always present (Fase 04 pilot)."""
    from src.modules.offer.domain.field_contract import OFFER_IGNORE_PATHS
    from src.modules.offer.domain.offer import Offer
    from src.shared.links.ports.editable_fields import get_paths_for

    return _ModuleRegistrySpec(
        name="offer",
        root_model=Offer,
        ignore_paths=OFFER_IGNORE_PATHS,
        composable_handles=frozenset({"specific_details", "platform_details"}),
        editable_paths_provider=lambda: frozenset(get_paths_for("offer")),
    )


# Register one entry per migrated module. Future phases append here.
def _build_module_registry() -> tuple[_ModuleRegistrySpec, ...]:
    return (_offer_spec(),)


_MIGRATED_SPECS: tuple[_ModuleRegistrySpec, ...] = _build_module_registry()


# ---------------------------------------------------------------------------
# Generic per-module assertions
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("spec", _MIGRATED_SPECS, ids=lambda s: s.name)
def test_module_has_non_empty_registry(spec: _ModuleRegistrySpec) -> None:
    """The platform must report contracts for every migrated module."""
    contracts = get_module_contracts(spec.name)
    assert contracts, (
        f"get_module_contracts('{spec.name}') returned empty. "
        f"Module is in MIGRATED_MODULES but did not register contracts. "
        f"Verify {spec.name}/domain/field_contract.py runs on import."
    )


@pytest.mark.parametrize("spec", _MIGRATED_SPECS, ids=lambda s: s.name)
def test_module_contracts_have_owner_module_set(spec: _ModuleRegistrySpec) -> None:
    """Every contract declares the correct owner_module."""
    for c in get_module_contracts(spec.name):
        assert c.owner_module == spec.name, (
            f"Contract '{c.path}' has owner_module='{c.owner_module}' but lives in '{spec.name}' registry."
        )


@pytest.mark.parametrize("spec", _MIGRATED_SPECS, ids=lambda s: s.name)
def test_module_contracts_have_section(spec: _ModuleRegistrySpec) -> None:
    """Every contract declares a non-empty section."""
    for c in get_module_contracts(spec.name):
        assert c.section, (
            f"Contract '{c.path}' in module '{spec.name}' has empty section. "
            "Add an entry to the module's SECTION_MAP or override.section."
        )


@pytest.mark.parametrize("spec", _MIGRATED_SPECS, ids=lambda s: s.name)
def test_module_contract_paths_unique(spec: _ModuleRegistrySpec) -> None:
    """Two contracts with the same (path, section) pair are forbidden.

    Different sections for the same path ARE allowed (polymorphic e.g.
    ``specific_details.start_date`` in PROGRAMA + EXPERIENCIA), but
    the (path, section) tuple must be unique within a module.
    """
    seen: set[tuple[str, str]] = set()
    duplicates: list[tuple[str, str]] = []
    for c in get_module_contracts(spec.name):
        key = (c.path, c.section)
        if key in seen:
            duplicates.append(key)
        seen.add(key)
    assert not duplicates, (
        f"Module '{spec.name}' has duplicate (path, section) contracts: {duplicates}. "
        f"Polymorphic walker should merge them; investigate."
    )


@pytest.mark.parametrize("spec", _MIGRATED_SPECS, ids=lambda s: s.name)
def test_module_editable_paths_subset_of_registry(spec: _ModuleRegistrySpec) -> None:
    """When the module exposes editable_fields, its paths must be in the registry."""
    if spec.editable_paths_provider is None:
        pytest.skip(f"{spec.name} has no editable_fields catalog")
    editable_paths = spec.editable_paths_provider()
    contract_paths = {c.path for c in get_module_contracts(spec.name)}
    leaks = editable_paths - contract_paths
    assert not leaks, (
        f"Editable paths in module '{spec.name}' missing from FieldContract: {sorted(leaks)}. "
        f"Catalog must project from the registry."
    )


@pytest.mark.parametrize("spec", _MIGRATED_SPECS, ids=lambda s: s.name)
def test_module_pydantic_subset_of_registry(spec: _ModuleRegistrySpec) -> None:
    """Top-level Pydantic fields ⊆ registry paths (modulo IGNORE + composables)."""
    pydantic_top_level = set(spec.root_model.model_fields.keys())
    contract_paths = {c.path for c in get_module_contracts(spec.name)}
    expected = pydantic_top_level - spec.ignore_paths - spec.composable_handles
    missing = expected - contract_paths
    assert not missing, (
        f"Module '{spec.name}' has Pydantic top-level fields without contracts: "
        f"{sorted(missing)}. Add to SECTION_MAP or IGNORE_PATHS."
    )


# ---------------------------------------------------------------------------
# Platform invariants (module-agnostic)
# ---------------------------------------------------------------------------


def test_field_contract_dataclass_is_frozen() -> None:
    """FieldContract instances must be immutable (frozen=True, slots=True)."""
    sample = FieldContract(
        path="x",
        owner_module="test",
        type=FieldStatus.ACTIVE.__class__("active"),  # any FieldType
        is_required_structural=False,
        section="s",
    )  # type: ignore[arg-type]
    # Frozen dataclass raises on mutation.
    with pytest.raises((AttributeError, Exception)):
        sample.path = "y"  # type: ignore[misc]
