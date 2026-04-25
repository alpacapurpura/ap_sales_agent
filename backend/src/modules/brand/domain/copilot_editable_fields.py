"""Brand editable-field catalog — projection of the FieldContract platform.

Post field-contract-platform refactor (Fase 06), this catalog is
**derived** from :data:`BRAND_FIELD_CONTRACTS` in
``src.modules.brand.domain.field_contract``. NO MORE manual tuple — every
field reachable here came from the BrandSettings Pydantic model + section
map + override metadata. Adding a new editable field requires zero changes
here: edit the contract overrides and the catalog updates automatically.

[COPILOT-EDITABLE-FIELDS-SSOT] → docs/domains/copilot/editable-fields.md

Backwards-compat:
- ``register_catalog("brand", BRAND_EDITABLE_FIELDS)`` is invoked at
  import as before — copilot consumers see the same shape.
- :data:`BRAND_EDITABLE_FIELDS` exposes the same ``FieldSpec`` tuple
  shape (path/label/section/description) as the legacy hand-written
  catalog, so all existing tests + system prompt enumeration are
  unaffected.
- Filtered to ``can_propose=True`` + ``status=ACTIVE`` so deprecated
  fields never reach the LLM.

Drift cerrado en Fase 06:
- Drift A (17 shorthand 2-level paths broken): ya no aparecen — el walker
  emite los sub-objects como OBJECT contracts marcados can_propose=False.
- Drift B (23 paths bajo wrong section ``contact.legal_*``): ahora aparecen
  bajo el path real ``identity.legal_*`` con la misma label curada.
- Drift C (~48 Pydantic fields sin entry catalog): ahora cubiertos por
  derivación. Etiquetas humanizadas para los nuevos paths.
"""

from __future__ import annotations

from src.modules.brand.domain.field_contract import BRAND_FIELD_CONTRACTS
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
    enumeration) falls back to ``notes`` (Pydantic ``Field(description=...)``
    populated by the walker).
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

    Brand contracts are not archetype-filtered (no polymorphic unions),
    so each path appears at most once in the registry — no dedupe needed.
    """
    specs: list[FieldSpec] = []
    for c in BRAND_FIELD_CONTRACTS:
        if not c.can_propose:
            continue
        if c.status != FieldStatus.ACTIVE:
            continue
        specs.append(_to_field_spec(c))
    return tuple(specs)


BRAND_EDITABLE_FIELDS: tuple[FieldSpec, ...] = _build_editable_fields()


# Register at import time so the copilot sees the catalog via the port
# without importing this module directly.
register_catalog("brand", BRAND_EDITABLE_FIELDS)


__all__ = ["BRAND_EDITABLE_FIELDS"]
