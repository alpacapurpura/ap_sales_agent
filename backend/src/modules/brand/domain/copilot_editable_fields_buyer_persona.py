"""Buyer-persona editable-field catalog — projection of the FieldContract platform.

Post field-contract-platform refactor (Fase 07), this catalog is
**derived** from :data:`BUYER_PERSONA_FIELD_CONTRACTS` in
``src.modules.brand.domain.buyer_persona_field_contract``. NO MORE
manual tuples — every field reachable here came from the BuyerPersona
Pydantic + dict_subkeys + section map + override metadata. Adding a
new editable field requires zero changes here: edit the contract
overrides and the catalog updates automatically.

[COPILOT-EDITABLE-FIELDS-SSOT] → docs/domains/copilot/editable-fields.md

Backwards-compat:
- ``register_catalog("buyer_persona", BUYER_PERSONA_EDITABLE_FIELDS)``
  is invoked at import as before — copilot consumers see the same
  shape via ``shared.links.ports.editable_fields``.
- :data:`BUYER_PERSONA_EDITABLE_FIELDS` exposes the same ``FieldSpec``
  tuple shape (path/label/section/description) as the legacy hand-
  written catalog, so all existing tests + system prompt enumeration
  stay byte-identical.
- Filtered to ``can_propose=True`` + ``status=ACTIVE`` so list fields
  managed via form-runtime CRUD (``pain_points``/``desires``/
  ``objections``/``preferred_channels``) and contract-only paths
  (``purchase_triggers``/``anti_patterns``) never reach the LLM.
"""

from __future__ import annotations

from src.modules.brand.domain.buyer_persona_field_contract import (
    BUYER_PERSONA_FIELD_CONTRACTS,
)
from src.shared.domain.field_contract import FieldContract, FieldStatus
from src.shared.links.ports.editable_fields import FieldSpec, register_catalog


def _humanize(name: str) -> str:
    """Convert dotted snake_case to a Title-cased label fallback."""
    last = name.rsplit(".", 1)[-1]
    return last.replace("_", " ").title()


def _to_field_spec(c: FieldContract) -> FieldSpec:
    """Project a ``FieldContract`` to a copilot ``FieldSpec``.

    Label resolution: ``override.label_es`` first, else humanize the
    last segment of ``path`` so labels remain non-empty.

    Description: ``human_question_es`` (preferred for conversational
    enumeration) falls back to ``notes`` (curated short prompt).
    """
    label = c.label_es or _humanize(c.path)
    description = c.human_question_es or c.notes
    return FieldSpec(
        path=c.path,
        label=label,
        section=c.section,
        description=description,
    )


def _build_editable_fields() -> tuple[FieldSpec, ...]:
    """Project the FieldContract registry to the copilot editable surface.

    Filters:
      - ``can_propose=True`` (the field is writable from the copilot).
      - ``status=ACTIVE`` (deprecated/removed fields never proposed).

    Buyer-persona contracts are not archetype-filtered (no polymorphic
    unions), so each path appears at most once in the registry — no
    dedupe needed.
    """
    specs: list[FieldSpec] = []
    for c in BUYER_PERSONA_FIELD_CONTRACTS:
        if not c.can_propose:
            continue
        if c.status != FieldStatus.ACTIVE:
            continue
        specs.append(_to_field_spec(c))
    return tuple(specs)


BUYER_PERSONA_EDITABLE_FIELDS: tuple[FieldSpec, ...] = _build_editable_fields()


# Register at import time so the copilot sees the catalog via the port
# without importing this module directly.
register_catalog("buyer_persona", BUYER_PERSONA_EDITABLE_FIELDS)


__all__ = ["BUYER_PERSONA_EDITABLE_FIELDS"]
