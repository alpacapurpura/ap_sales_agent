"""Arch test: landing content builders ⊆ FieldContract.

Asserts every offer path read by ``landing_content_builders`` resolves
to an ACTIVE entry in the offer FieldContract registry, modulo a
documented legacy allowlist for raw-SQL aliases / JSONB columns that
predate the Offer Pydantic model.

Workspace: ``docs/refactors/field-contract-platform/`` Fase 05.
"""

from __future__ import annotations

import re
from pathlib import Path

from src.shared.domain.field_contract import FieldStatus, get_module_contracts

BUILDERS_PATH = (
    Path(__file__).parent / ".." / ".." / "src" / "modules" / "landing" / "application" / "landing_content_builders.py"
).resolve()

# Legacy raw-SQL columns / aliases not present in the Offer Pydantic
# model. ``name`` is the products-table column corresponding to
# ``Offer.public_name``; ``pricing`` is the legacy JSONB column with
# ``pay_in_full`` / ``original_price`` / ``discounted_price`` keys
# that predates ``pricing_options``. Both surface to the landing
# pipeline through ``landing_service.generate_landing_for_offer``
# raw-SQL projection — out of scope for FieldContract until the
# pipeline migrates to the Offer aggregate (deferred).
LEGACY_SQL_ALIASES: frozenset[str] = frozenset({"name", "pricing"})

_DATA_GET_RE = re.compile(r'data\.get\(\s*"([a-zA-Z_][a-zA-Z_0-9]*)"')


def _builder_offer_paths() -> set[str]:
    text = BUILDERS_PATH.read_text(encoding="utf-8")
    return set(_DATA_GET_RE.findall(text))


def test_landing_builder_paths_subset_of_field_contract() -> None:
    builder_paths = _builder_offer_paths() - LEGACY_SQL_ALIASES
    contract = {c.path: c for c in get_module_contracts("offer")}

    unknown: list[str] = []
    deprecated: list[str] = []
    for path in builder_paths:
        spec = contract.get(path)
        if spec is None:
            unknown.append(path)
            continue
        if spec.status != FieldStatus.ACTIVE:
            deprecated.append(f"{path} (status={spec.status.value})")

    assert not unknown, (
        f"landing_content_builders references offer paths absent from FieldContract: "
        f"{sorted(unknown)}.\nEither add them to OFFER_SECTION_MAP / OFFER_FIELD_OVERRIDES "
        f"or whitelist as legacy SQL aliases in this test."
    )
    assert not deprecated, (
        f"landing_content_builders still reads DEPRECATED/REMOVED contract paths: "
        f"{sorted(deprecated)}.\nUpdate the builder to drop the deprecated reads."
    )
