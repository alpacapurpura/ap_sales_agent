"""Cross-module port for the copilot's editable-field catalog.

The copilot needs to know *which fields the user can actually edit from the
UI* so that ``propose_field_updates`` and the system prompt stay honest:
no hallucinated ``field_id``s, no legacy fields that the FE no longer
renders, no cross-module surprises.

This port is the **single source of truth** that copilot uses to validate
and enumerate editable fields. Each business module (brand, offer, …)
registers its catalog via ``register_catalog`` at import time.

Bounded-context contract
------------------------
* Owner modules declare their catalogs in their own ``domain/`` layer
  (e.g. ``brand/domain/copilot_editable_fields.py``).
* The copilot reads **only** through the ``get_catalog(domain)`` function
  here — it never imports ``brand``/``offer``/etc. directly.
* Lazy registration prevents circular imports and keeps ``shared/`` free
  from module-level dependencies on ``modules/``.

See ``.claude/rules/copilot-resilience.md`` and the anchor
``[COPILOT-EDITABLE-FIELDS-SSOT]`` in each module's catalog file.
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
        label: Human-readable label (matches the FE form label in español).
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
# ``_CATALOGS`` is populated at import time by each module's
# ``copilot_editable_fields.py``.  Readers must go through the public
# ``get_catalog`` / ``get_registered_domains`` accessors; direct access is
# discouraged so the contract stays enforceable.
_CATALOGS: dict[str, tuple[FieldSpec, ...]] = {}


def register_catalog(domain: str, fields: tuple[FieldSpec, ...]) -> None:
    """Register (or replace) the editable-field catalog for ``domain``.

    Idempotent: calling twice with the same payload is a no-op; calling
    with a different payload replaces the previous registration (handy
    for tests that stub a domain).
    """
    _CATALOGS[domain] = tuple(fields)


def get_catalog(domain: str) -> tuple[FieldSpec, ...]:
    """Return the frozen tuple of editable fields for ``domain``.

    Triggers lazy registration by importing the module's catalog file on
    first access, so callers don't have to manage import ordering.
    """
    if domain not in _CATALOGS:
        _lazy_register(domain)
    return _CATALOGS.get(domain, ())


def get_registered_domains() -> tuple[str, ...]:
    """Return all domains that have registered a catalog.

    Useful for enumerating the full editable surface in the system prompt.
    """
    # Force lazy registration for known-owner modules so the first call is
    # authoritative even before any other consumer imports them.
    for domain in _KNOWN_DOMAINS:
        if domain not in _CATALOGS:
            _lazy_register(domain)
    return tuple(sorted(_CATALOGS.keys()))


def get_paths_for(domain: str) -> frozenset[str]:
    """Return the set of valid dot-notation paths for ``domain``.

    Consumers use this as a validator:
    ``path in get_paths_for("brand")`` → True iff the field is editable.
    """
    return frozenset(f.path for f in get_catalog(domain))


# ── Lazy registration dispatch ───────────────────────────────────────────
# Known owner modules per domain.  Adding a new domain here + the matching
# ``copilot_editable_fields.py`` in its module is the only change needed.
_KNOWN_DOMAINS: dict[str, str] = {
    "brand": "src.modules.brand.domain.copilot_editable_fields",
    "offer": "src.modules.offer.domain.copilot_editable_fields",
}


def _lazy_register(domain: str) -> None:
    """Import the owner module's catalog file, which registers itself."""
    module_path = _KNOWN_DOMAINS.get(domain)
    if module_path is None:
        return
    try:
        __import__(module_path)
    except ImportError:
        # An owner module without a catalog yet is a config gap, not a
        # fatal error — the copilot will see an empty catalog and refuse
        # to propose fields for that domain, which is the safe default.
        return
