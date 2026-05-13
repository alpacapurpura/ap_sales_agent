"""Arch test: ``offer.X`` paths in ``agent_identity.j2`` ⊆ FieldContract.

Parses the sales-agent identity template, extracts every ``offer.X``
reference, and asserts that each path either exists in the offer
FieldContract registry (with status ACTIVE) or is whitelisted as a
template-injected enrichment field (preset_label, preset_description,
preset_flags, type — all populated by ``knowledge_builder._enrich_with_preset_metadata``).

Drift cause: someone references ``offer.<new_field>`` in the template
but forgets to add the field to ``OFFER_SECTION_MAP`` /
``OFFER_FIELD_OVERRIDES``. This test detects that early.

Workspace: ``docs/refactors/field-contract-platform/`` Fase 05.
"""

from __future__ import annotations

import re
from pathlib import Path

from luana_core_platform.domain.field_contract import FieldStatus, get_module_contracts

TEMPLATE_PATH = (
    Path(__file__).parent
    / ".."
    / ".."
    / "src"
    / "modules"
    / "sales_agent"
    / "infrastructure"
    / "prompts"
    / "templates"
    / "agent_identity.j2"
).resolve()

# Enrichment / fallback fields injected at render time, NOT persisted on
# the Offer Pydantic model. Out of scope for FieldContract by design.
ENRICHMENT_PATHS: frozenset[str] = frozenset(
    {
        "preset_label",
        "preset_description",
        "preset_flags",
        "type",  # legacy fallback after preset_label / archetype / format_hint
    }
)

# ``offer.X`` references where X may be followed by ``.`` or end of token.
_OFFER_REF_RE = re.compile(r"\boffer\.([a-zA-Z_][a-zA-Z_0-9]*)")


def _template_offer_paths() -> set[str]:
    template_text = TEMPLATE_PATH.read_text(encoding="utf-8")
    return set(_OFFER_REF_RE.findall(template_text))


def test_template_offer_paths_subset_of_field_contract() -> None:
    """Every ``offer.X`` in the template is either ACTIVE in the contract
    or part of the enrichment allowlist.
    """
    template_paths = _template_offer_paths()
    contract = {c.path: c for c in get_module_contracts("offer")}

    unknown: list[str] = []
    deprecated: list[str] = []
    for path in template_paths - ENRICHMENT_PATHS:
        spec = contract.get(path)
        if spec is None:
            unknown.append(path)
            continue
        if spec.status != FieldStatus.ACTIVE:
            deprecated.append(f"{path} (status={spec.status.value})")

    assert not unknown, (
        f"agent_identity.j2 references offer paths absent from FieldContract: {sorted(unknown)}.\n"
        f"Either add them to OFFER_SECTION_MAP / OFFER_FIELD_OVERRIDES in "
        f"offer/domain/field_contract.py, or whitelist them in ENRICHMENT_PATHS "
        f"({TEMPLATE_PATH.name}-only)."
    )
    assert not deprecated, (
        f"agent_identity.j2 still references DEPRECATED/REMOVED contract paths: {sorted(deprecated)}.\n"
        f"Remove the references from the template now that the contract has retired them."
    )


def test_template_offer_paths_have_no_typos() -> None:
    """Sanity: regex actually finds *something*. Catches accidental rename."""
    paths = _template_offer_paths()
    assert paths, f"No offer.X references found in {TEMPLATE_PATH}. Template signature changed?"
    # Anchor: at minimum these high-signal fields must be referenced.
    expected_min = {"public_name", "headline_promise", "primary_outcome"}
    missing = expected_min - paths
    assert not missing, (
        f"Template missing high-signal offer paths: {sorted(missing)}. Likely a regression in template structure."
    )
