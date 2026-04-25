"""Cross-module port for the copilot's editable-field catalog.

The copilot needs to know *which fields the user can actually edit from the
UI* so that ``propose_field_updates`` and the system prompt stay honest:
no hallucinated ``field_id``s, no legacy fields that the FE no longer
renders, no cross-module surprises.

This port is the **single source of truth** that copilot uses to validate
and enumerate editable fields.

Post field-contract-platform refactor (Fase 08), the catalog for any module
that has registered :class:`FieldContract` (offer / brand / buyer_persona)
is **derived automatically** from
:func:`src.shared.domain.field_contract.get_module_contracts` with filters
``can_propose=True`` + ``status=ACTIVE`` and dedupe by ``path``. The 3
``copilot_editable_fields*.py`` projection files (offer / brand /
buyer_persona) were dropped — boilerplate idéntico al helper
:func:`_derive_from_contracts` aquí.

Test stubs and custom catalogs may still call :func:`register_catalog`
explicitly; the explicit registration takes precedence over derivation.

Bounded-context contract
------------------------
* Owner modules declare their FieldContract registries in their own
  ``domain/field_contract.py`` (or ``buyer_persona_field_contract.py``).
* The port reads the registry **only** through
  :func:`get_module_contracts` — no direct module imports.
* Lazy registration of the FieldContract registry triggers transitively
  on the first ``get_catalog`` call per domain.

See ``.claude/rules/copilot-resilience.md`` and the anchor
``[COPILOT-EDITABLE-FIELDS-SSOT]`` in ``docs/domains/copilot/editable-fields.md``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FieldSpec:
    """Metadata for one editable field exposed to the copilot.

    Attributes:
        path: Canonical dot-notation path as the frontend persists it.
              For nested models it is ``section.subfield``
              (e.g. ``"identity.brand_name"``); for flat aggregates it is
              just the field name (e.g. ``"public_name"`` for offer).
        label: Human-readable label (matches the FE form label en español).
        section: Logical UI section / form-runtime key fragment
              (e.g. ``"identity"``, ``"personality"``).  Used to group
              fields when the copilot renders its catalog hint.
        description: Optional short hint shown with the field in the
              prompt catalog. Mirrors the FE ``hint`` when informative.
    """

    path: str
    label: str
    section: str
    description: str | None = None


# ── Internal registry ────────────────────────────────────────────────────
# ``_CATALOGS`` holds explicit registrations (test stubs, custom catalogs).
# Modules with a FieldContract registry do NOT need to register — derivation
# happens lazy on ``get_catalog`` call.
_CATALOGS: dict[str, tuple[FieldSpec, ...]] = {}


def register_catalog(domain: str, fields: tuple[FieldSpec, ...]) -> None:
    """Register (or replace) the editable-field catalog for ``domain``.

    Most modules don't need this — :func:`get_catalog` derives from the
    FieldContract platform automatically. Use this when:

    1. Tests want to stub a domain's catalog deterministically.
    2. A non-Pydantic module wants to expose an editable surface (rare).

    Idempotent: calling twice with the same payload is a no-op; calling
    with a different payload replaces the previous registration.
    """
    _CATALOGS[domain] = tuple(fields)


def get_catalog(domain: str) -> tuple[FieldSpec, ...]:
    """Return the frozen tuple of editable fields for ``domain``.

    Resolution order:
      1. Explicit registration via :func:`register_catalog` (test stubs).
      2. Derived from :func:`get_module_contracts` lazily (default for
         every module that registered a FieldContract registry).

    Returns ``()`` when neither source has data for ``domain``.
    """
    if domain in _CATALOGS:
        return _CATALOGS[domain]
    derived = _derive_from_contracts(domain)
    if derived:
        # Cache the projection so repeated calls don't re-walk the registry.
        # The FieldContract registry is immutable post-bootstrap, so the
        # cached projection is also immutable.
        _CATALOGS[domain] = derived
    return derived


def get_registered_domains() -> tuple[str, ...]:
    """Return all domains for which a non-empty catalog is available.

    Includes domains explicitly registered via :func:`register_catalog`
    and domains with a FieldContract registry. Empty catalogs (no
    proposable fields) are excluded.
    """
    from src.shared.domain.field_contract import get_all_modules

    domains = set(_CATALOGS.keys()) | set(get_all_modules())
    return tuple(sorted(d for d in domains if get_catalog(d)))


def get_paths_for(domain: str) -> frozenset[str]:
    """Return the set of valid dot-notation paths for ``domain``.

    Consumers use this as a validator:
    ``path in get_paths_for("brand")`` → True iff the field is editable.
    """
    return frozenset(f.path for f in get_catalog(domain))


# ── Derivation helpers ───────────────────────────────────────────────────


def _humanize(name: str) -> str:
    """Convert dotted snake_case to a Title-cased label fallback."""
    last = name.rsplit(".", 1)[-1]
    return last.replace("_", " ").title()


def _derive_from_contracts(domain: str) -> tuple[FieldSpec, ...]:
    """Project the FieldContract registry for ``domain`` to FieldSpec tuple.

    Filters:
      - ``can_propose=True`` (the field is writable from the copilot).
      - ``status=ACTIVE`` (deprecated/removed fields never proposed).

    Dedupes by ``path``: when a path appears in multiple contracts (e.g.
    polymorphic ``specific_details.start_date`` in PROGRAMA + EXPERIENCIA),
    only one ``FieldSpec`` is emitted — the section of the first
    encountered contract wins. The copilot surface is archetype-agnostic:
    each path has exactly one entry.

    Label resolution: ``override.label_es`` first, else humanize the
    last segment of ``path`` (arch test enforces ``spec.label`` truthy).

    Description: ``human_question_es`` (preferred for conversational
    enumeration) falls back to ``notes`` (Pydantic ``Field(description=...)``
    populated by the walker).
    """
    from src.shared.domain.field_contract import (
        FieldStatus,
        get_module_contracts,
    )

    contracts = get_module_contracts(domain)
    if not contracts:
        return ()

    seen_paths: set[str] = set()
    specs: list[FieldSpec] = []
    for c in contracts:
        if not c.can_propose:
            continue
        if c.status != FieldStatus.ACTIVE:
            continue
        if c.path in seen_paths:
            continue
        seen_paths.add(c.path)
        specs.append(
            FieldSpec(
                path=c.path,
                label=c.label_es or _humanize(c.path),
                section=c.section,
                description=c.human_question_es or c.notes,
            ),
        )
    return tuple(specs)
