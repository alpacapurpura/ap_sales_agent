"""Anti-regression: buyer-persona catalog must stay projected from the registry.

Fase 07 closed the legacy hand-written tuple pattern by deriving
``BUYER_PERSONA_EDITABLE_FIELDS`` from ``BUYER_PERSONA_FIELD_CONTRACTS``.
Re-introducing inline ``FieldSpec`` tuples defeats the migration —
12-entry catalog drift is invisible without a guard, and the buyer-
persona surface ships into the copilot system prompt every turn.

These tests guard the projection so future contributors cannot silently
revert to manual maintenance.

refs: docs/refactors/field-contract-platform/phases/07-buyer-migration/
"""

from __future__ import annotations

from pathlib import Path

from src.modules.brand.domain.buyer_persona_field_contract import (
    BUYER_PERSONA_FIELD_CONTRACTS,
)
from src.modules.brand.domain.copilot_editable_fields_buyer_persona import (
    BUYER_PERSONA_EDITABLE_FIELDS,
)
from src.shared.domain.field_contract import FieldStatus


class TestBuyerPersonaCatalogProjection:
    """``BUYER_PERSONA_EDITABLE_FIELDS`` must project from ``BUYER_PERSONA_FIELD_CONTRACTS``."""

    def test_catalog_equals_proposable_subset_of_registry(self) -> None:
        """Catalog paths == registry paths with can_propose=True + status=ACTIVE."""
        catalog_paths = {f.path for f in BUYER_PERSONA_EDITABLE_FIELDS}
        proposable_paths = {
            c.path for c in BUYER_PERSONA_FIELD_CONTRACTS if c.can_propose and c.status == FieldStatus.ACTIVE
        }
        diff = catalog_paths.symmetric_difference(proposable_paths)
        assert not diff, (
            f"BUYER_PERSONA_EDITABLE_FIELDS diverged from registry projection.\n"
            f"In catalog only: {sorted(catalog_paths - proposable_paths)}\n"
            f"In registry only: {sorted(proposable_paths - catalog_paths)}"
        )

    def test_catalog_section_matches_contract_section(self) -> None:
        """For every catalog path, the section comes from its contract."""
        contract_by_path = {c.path: c for c in BUYER_PERSONA_FIELD_CONTRACTS}
        mismatches: list[str] = []
        for spec in BUYER_PERSONA_EDITABLE_FIELDS:
            contract = contract_by_path.get(spec.path)
            if contract is None:
                mismatches.append(f"{spec.path}: no contract entry")
            elif contract.section != spec.section:
                mismatches.append(
                    f"{spec.path}: contract section={contract.section!r}, catalog section={spec.section!r}"
                )
        assert not mismatches, "Catalog ↔ registry section drift:\n  " + "\n  ".join(mismatches)


class TestNoHandWrittenFieldSpecTuples:
    """Module file must not declare manual ``FieldSpec`` tuples.

    Re-introducing hand-written tuples like ``_IDENTITY = (FieldSpec(...), ...)``
    bypasses the registry derivation and resurrects the catalog drift
    the Fase 07 migration closed.
    """

    def test_buyer_persona_catalog_file_has_no_inline_field_spec_tuples(self) -> None:
        """The buyer-persona catalog source file declares zero inline ``FieldSpec(`` calls.

        The projection helper ``_to_field_spec`` constructs ``FieldSpec``
        instances inside a function body — the test scans for top-level
        / module-scope ``FieldSpec(`` literal calls which are the smell
        of hand-written tuples.
        """
        catalog_file = (
            Path(__file__).parent.parent.parent
            / "src"
            / "modules"
            / "brand"
            / "domain"
            / "copilot_editable_fields_buyer_persona.py"
        )
        content = catalog_file.read_text(encoding="utf-8")

        # Find FieldSpec( calls. The projection helper has exactly one
        # call inside ``_to_field_spec``: ``return FieldSpec(...)``.
        field_spec_calls = [
            (idx + 1, line)
            for idx, line in enumerate(content.splitlines())
            if "FieldSpec(" in line and not line.lstrip().startswith(("#", '"', "'"))
        ]
        # Allow exactly one occurrence — inside the projection helper.
        assert len(field_spec_calls) <= 1, (
            "brand/domain/copilot_editable_fields_buyer_persona.py declares multiple FieldSpec( calls:\n"
            + "\n".join(f"  L{n}: {ln.strip()}" for n, ln in field_spec_calls)
            + "\n\nBuyer-persona catalog must derive from BUYER_PERSONA_FIELD_CONTRACTS via the "
            "projection helper. Hand-written tuples were removed in Fase 07."
        )

    def test_buyer_persona_catalog_file_imports_field_contracts(self) -> None:
        """The catalog file must import ``BUYER_PERSONA_FIELD_CONTRACTS`` (proof of projection)."""
        catalog_file = (
            Path(__file__).parent.parent.parent
            / "src"
            / "modules"
            / "brand"
            / "domain"
            / "copilot_editable_fields_buyer_persona.py"
        )
        content = catalog_file.read_text(encoding="utf-8")
        assert "BUYER_PERSONA_FIELD_CONTRACTS" in content, (
            "brand/domain/copilot_editable_fields_buyer_persona.py must import BUYER_PERSONA_FIELD_CONTRACTS "
            "from brand/domain/buyer_persona_field_contract.py — projection is mandatory post-Fase-07."
        )
