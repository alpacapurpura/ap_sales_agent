"""Arch test: ``OfferCompletionService`` validators ⊆ FieldContract.

Asserts every offer path referenced by the legacy ``_SECTION_VALIDATORS``
dict in :mod:`offer_completion_service` resolves to an ACTIVE entry in
the offer FieldContract registry. Failing this check means either:

- The completion validator points at a typo / removed Pydantic field.
- A FieldContract entry was deprecated without updating the validator.

Note: this test does NOT yet enforce that ``is_required_semantic=True``
in the contract is a *superset* of the validator's required-fields list.
Aligning the two is deferred — the completion service uses its own
"completion section" taxonomy (e.g. ``promise`` validates only
``headline_promise`` while the contract section ``promise`` covers
``before_state`` / ``after_state`` / ``why_now`` / etc.). Consolidating
that taxonomy is tracked in LEARNINGS for a follow-up phase.

Workspace: ``docs/refactors/field-contract-platform/`` Fase 05.
"""

from __future__ import annotations

from src.modules.offer.application.services.offer_completion_service import (
    _SECTION_NARRATIVE_FIELDS,
    _SECTION_VALIDATORS,
)
from src.shared.domain.field_contract import FieldStatus, get_module_contracts


def _active_contract_paths() -> set[str]:
    return {c.path for c in get_module_contracts("offer") if c.status == FieldStatus.ACTIVE}


def test_section_validator_paths_subset_of_field_contract() -> None:
    paths: set[str] = set()
    for _mode, fields in _SECTION_VALIDATORS.values():
        paths.update(fields)

    contract_paths = _active_contract_paths()
    missing = paths - contract_paths
    assert not missing, (
        f"OfferCompletionService validators reference paths absent from FieldContract: "
        f"{sorted(missing)}.\nEither add them to OFFER_SECTION_MAP / OFFER_FIELD_OVERRIDES "
        f"in offer/domain/field_contract.py, or remove them from _SECTION_VALIDATORS."
    )


def test_narrative_field_paths_subset_of_field_contract() -> None:
    paths: set[str] = set()
    for fields in _SECTION_NARRATIVE_FIELDS.values():
        paths.update(fields)

    contract_paths = _active_contract_paths()
    missing = paths - contract_paths
    assert not missing, f"_SECTION_NARRATIVE_FIELDS references paths absent from FieldContract: {sorted(missing)}."
