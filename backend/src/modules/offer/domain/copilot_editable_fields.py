"""Offer editable-field catalog — projection of the FieldContract platform.

Post field-contract-platform refactor (Fase 04), this catalog is
**derived** from :data:`OFFER_FIELD_CONTRACTS` in
``src.modules.offer.domain.field_contract``. NO MORE manual tuple — every
field reachable here came from the Pydantic ``Offer`` model + section map +
override metadata. Adding a new editable field requires zero changes here:
edit the contract overrides and the catalog updates automatically.

[COPILOT-EDITABLE-FIELDS-SSOT] → docs/domains/copilot/editable-fields.md

Backwards-compat:
- ``register_catalog("offer", OFFER_EDITABLE_FIELDS)`` is invoked at
  import as before — copilot consumers see the same shape.
- :data:`OFFER_EDITABLE_FIELDS` exposes the same ``FieldSpec`` tuple
  shape (path/label/section/description) as the legacy hand-written
  catalog, so all existing tests + system prompt enumeration are
  unaffected.
- Filtered to ``can_propose=True`` + ``status=ACTIVE`` so deprecated
  fields never reach the LLM.
"""

from __future__ import annotations

from src.modules.offer.domain.field_contract import OFFER_FIELD_CONTRACTS
from src.shared.domain.field_contract import FieldContract, FieldStatus
from src.shared.links.ports.editable_fields import FieldSpec, register_catalog


def _humanize(name: str) -> str:
    """Convert dotted snake_case to a Title-cased label fallback."""
    last = name.rsplit(".", 1)[-1]
    return last.replace("_", " ").title()


def _to_field_spec(c: FieldContract) -> FieldSpec:
    """Project a ``FieldContract`` to a copilot ``FieldSpec``.

    Label resolution: ``override.label_es`` first, else humanize the
    last segment of ``path`` so labels remain non-empty (arch test
    enforces ``spec.label`` truthy).

    Description: ``human_question_es`` (preferred for conversational
    enumeration) falls back to ``notes``. Empty when both are None.
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

    Dedupes by path: when a path appears in multiple contracts (e.g.
    polymorphic specific_details.start_date in PROGRAMA + EXPERIENCIA),
    only one ``FieldSpec`` is emitted — the section of the first
    encountered contract wins. The copilot surface is archetype-agnostic:
    each path has exactly one entry, regardless of which archetype
    filtered contract surfaced it.
    """
    seen_paths: set[str] = set()
    specs: list[FieldSpec] = []
    for c in OFFER_FIELD_CONTRACTS:
        if not c.can_propose:
            continue
        if c.status != FieldStatus.ACTIVE:
            continue
        if c.path in seen_paths:
            continue
        seen_paths.add(c.path)
        specs.append(_to_field_spec(c))
    return tuple(specs)


OFFER_EDITABLE_FIELDS: tuple[FieldSpec, ...] = _build_editable_fields()


# Register at import time so the copilot sees the catalog via the port.
register_catalog("offer", OFFER_EDITABLE_FIELDS)


__all__ = ["OFFER_EDITABLE_FIELDS"]
