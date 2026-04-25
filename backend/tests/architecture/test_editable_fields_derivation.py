"""Anti-regression: editable_fields port deriva idéntico al projection esperado.

Post-Fase-08 the shared port :mod:`src.shared.links.ports.editable_fields`
deriva ``get_catalog(domain)`` desde ``get_module_contracts(domain)`` con
filtros ``can_propose=True`` + ``status=ACTIVE`` y dedupe por ``path``.

Si alguien rompe el helper interno ``_derive_from_contracts`` o agrega
manual entries via ``register_catalog`` que divergen del registry, estos
tests prenden la alarma.

refs: docs/refactors/field-contract-platform/phases/08-copilot-unification/SPEC.md
"""

from __future__ import annotations

import pytest

from src.shared.domain.field_contract import (
    FieldStatus,
    get_module_contracts,
)
from src.shared.links.ports.editable_fields import FieldSpec, get_catalog, get_paths_for

MIGRATED_DOMAINS: tuple[str, ...] = ("offer", "brand", "buyer_persona")


def _humanize(name: str) -> str:
    """Mirror del helper interno del port (reusado para verificar projection)."""
    last = name.rsplit(".", 1)[-1]
    return last.replace("_", " ").title()


def _expected_projection(domain: str) -> tuple[FieldSpec, ...]:
    """Projection esperada del registry idéntica a la del port.

    Si esta función diverge del helper privado del port, los tests fallan
    — gate explícito contra drift.
    """
    contracts = get_module_contracts(domain)
    seen: set[str] = set()
    specs: list[FieldSpec] = []
    for c in contracts:
        if not c.can_propose:
            continue
        if c.status != FieldStatus.ACTIVE:
            continue
        if c.path in seen:
            continue
        seen.add(c.path)
        specs.append(
            FieldSpec(
                path=c.path,
                label=c.label_es or _humanize(c.path),
                section=c.section,
                description=c.human_question_es or c.notes,
            ),
        )
    return tuple(specs)


class TestEditableFieldsDerivation:
    """``get_catalog(domain)`` proyecta del FieldContract registry."""

    @pytest.mark.parametrize("domain", MIGRATED_DOMAINS)
    def test_get_catalog_matches_expected_projection(self, domain: str) -> None:
        """Catalog del port == projection manual de get_module_contracts."""
        expected = _expected_projection(domain)
        actual = get_catalog(domain)
        assert actual == expected, (
            f"get_catalog('{domain}') diverged from FieldContract projection.\n"
            f"In actual only: {sorted(set(actual) - set(expected), key=lambda s: s.path)}\n"
            f"In expected only: {sorted(set(expected) - set(actual), key=lambda s: s.path)}"
        )

    @pytest.mark.parametrize("domain", MIGRATED_DOMAINS)
    def test_get_paths_for_filters_can_propose_and_active(self, domain: str) -> None:
        """get_paths_for excluye contracts con can_propose=False o status!=ACTIVE."""
        catalog_paths = set(get_paths_for(domain))
        for c in get_module_contracts(domain):
            if not c.can_propose or c.status != FieldStatus.ACTIVE:
                assert c.path not in catalog_paths, (
                    f"{domain}.{c.path} should be excluded (can_propose={c.can_propose}, status={c.status})."
                )

    @pytest.mark.parametrize("domain", MIGRATED_DOMAINS)
    def test_get_catalog_non_empty(self, domain: str) -> None:
        """Cada módulo migrado expone al menos 1 path proposable."""
        catalog = get_catalog(domain)
        assert len(catalog) > 0, f"get_catalog('{domain}') is empty"

    @pytest.mark.parametrize("domain", MIGRATED_DOMAINS)
    def test_get_catalog_paths_unique(self, domain: str) -> None:
        """Dedupe por path: cada path aparece exactamente 1 vez."""
        catalog = get_catalog(domain)
        paths = [f.path for f in catalog]
        assert len(paths) == len(set(paths)), (
            f"get_catalog('{domain}') has duplicate paths: {[p for p in paths if paths.count(p) > 1]}"
        )

    @pytest.mark.parametrize("domain", MIGRATED_DOMAINS)
    def test_get_catalog_label_truthy(self, domain: str) -> None:
        """Cada FieldSpec tiene label no vacío (humanize fallback garantiza)."""
        catalog = get_catalog(domain)
        empty = [f.path for f in catalog if not f.label]
        assert not empty, f"{domain} catalog has empty labels: {empty}"
