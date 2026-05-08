"""Multi-tenant personas YAML loader (Story C / T-3 deliverable).

Resolves ``(tenant_slug, persona_kind) → ActorProfile`` from
``docs/specs/personas/archetype-aware/*.yaml``. Backed by a process-scoped
``lru_cache`` so repeated calls return the SAME ActorProfile instance
(D6 idempotency contract).

Design decisions (per ``03-arch.md`` § §4.1):

- ``D-AG-1`` cross-check: each persona's ``dialect_code`` MUST match
  ``ARCHETYPE_DIALECT_MAP[tenant_slug]`` (Story A loader contract). On
  mismatch the loader raises ``ValueError`` BEFORE Pydantic
  ``model_validate`` so dialect drift surfaces fail-fast instead of
  silently corrupting downstream graders.

- ``D-AG-2`` private surface: this module lives under ``_internal/`` and
  is NOT exported via ``simulator/__init__.py`` (H9 frozen 7-name
  surface). Downstream stories import from this path directly.

- ``D-AG-5`` recursive glob: ``_PERSONAS_ROOT.rglob("*.yaml")`` walks the
  full tree; ``_legacy/`` subdir is excluded by name (D2 — Story I may
  reactivate baseline personas later).

- ``D-AG-6`` apply_migrations chain: every loaded persona walks the
  Story B ``SCHEMA_MIGRATIONS`` registry to ``CURRENT_SCHEMA_VERSIONS``.
  v1 personas are auto-bumped to v2 via the identity migrator (Story C
  T-1).

- ``D-AG-8`` graceful degradation: malformed YAML during the directory
  scan is logged + skipped (``tessl__graceful-degradation`` Rule 2).
  Other personas remain loadable.

- ``D-AG-10`` loader-only kinds: ``edge`` + ``negative`` are diagnostic
  schema slots; ``get_max_turns_for_persona_kind`` raises ``KeyError``
  for them so callers cannot accidentally drive a simulation with an
  unsupported kind.

- ``D5`` strict tenant slug: ``tenant_slug`` not in the 5 valid Story A
  seed slugs raises ``KeyError`` listing the valid set.

- ``D6`` lru_cache identity: ``load_actor_profile_for_tenant`` is
  process-scoped ``lru_cache(maxsize=None)``; two calls with the same
  args return the SAME instance (``is`` identity).

- ``D15`` max_turns matriz: helper exposes the per-kind cap (happy=10,
  nurture=15, unqualified=8, adversarial=5) used by Scenarios 5+6 to
  bound simulation length.

Public surface (consumed via direct import path):

- :data:`PersonaKind` — Literal of 6 values v2.
- :func:`load_actor_profile_for_tenant` — main resolver.
- :func:`get_max_turns_for_persona_kind` — D15 helper.

# voseo-allowed: docstring cita es-AR archetype + magic comment escape
# rule en YAMLs (referencia técnica del glosario, no string user-facing)
"""

# ``from __future__ import annotations`` PERMITTED here per
# 05-guidelines.md line 14: this module is NOT part of the LangGraph
# runtime introspection chain (it returns a Pydantic ActorProfile
# instance directly, never participates in StateGraph compose).
from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import Final, Literal

import structlog
import yaml  # type: ignore[import-untyped]

from tests.agentic_evals.sales_agent.simulator._internal.schema_migrations import (
    CURRENT_SCHEMA_VERSIONS,
    apply_migrations,
)
from tests.agentic_evals.sales_agent.simulator.actor_profile import ActorProfile

logger = structlog.get_logger()


# ════════════════════════════════════════════════════════════════════════
# Path anchors — symmetric to ``runner.py::_BACKEND_ROOT`` so test
# invocation from any cwd works the same. Loader file lives at:
#   backend/tests/agentic_evals/sales_agent/simulator/_internal/personas_loader.py
#                                                             ^ this
#
# parents[0] = _internal/
# parents[1] = simulator/
# parents[2] = sales_agent/
# parents[3] = agentic_evals/
# parents[4] = tests/
# parents[5] = backend/
# parent of [5] = repo root → docs/specs/personas/
# ════════════════════════════════════════════════════════════════════════

_BACKEND_ROOT: Final[Path] = Path(__file__).resolve().parents[5]
_PERSONAS_ROOT: Path = _BACKEND_ROOT.parent / "docs" / "specs" / "personas"
"""Anchor for the personas YAML catalog. Mutable at module level (NOT Final)
so tests can monkeypatch with ``tmp_path`` fixtures."""

_LEGACY_DIR_NAME: Final[str] = "_legacy"
"""Subdir name excluded from the recursive glob (D2 — Story I optional
baseline reactivation)."""


# ════════════════════════════════════════════════════════════════════════
# Public constants
# ════════════════════════════════════════════════════════════════════════

_VALID_TENANT_SLUGS: Final[frozenset[str]] = frozenset(
    {
        "tenant_coach_lat",
        "tenant_medicina_estetica",
        "tenant_clinica_dental",
        "tenant_agencia_growth_video",
        "tenant_agencia_automatizacion_ia",
    }
)
"""Story A seed tenant slugs — locked to ``ARCHETYPE_DIALECT_MAP`` keys."""

_MAX_TURNS_BY_PERSONA_KIND: Final[dict[str, int]] = {
    "happy": 10,
    "nurture": 15,
    "unqualified": 8,
    "adversarial": 5,
    # `edge` + `negative` intentionally absent — D-AG-10 loader-only kinds.
}
"""D15 matriz — max_turns cap per persona_kind for Scenarios 5+6 routing."""


PersonaKind = Literal["happy", "nurture", "unqualified", "adversarial", "edge", "negative"]
"""6-value Literal mirroring :class:`ActorProfile.persona_kind` post v2 (D13)."""


# ════════════════════════════════════════════════════════════════════════
# Internal — recursive YAML directory scan (lru_cache)
# ════════════════════════════════════════════════════════════════════════


@cache
def _scan_personas_directory() -> dict[tuple[str, str], Path]:
    """Recursive glob ``docs/specs/personas/**/*.yaml`` excluding ``_legacy/``.

    Returns a map ``(tenant_slug, persona_kind) → Path`` for O(1) lookup
    in :func:`load_actor_profile_for_tenant`.

    Resilience contract (``tessl__graceful-degradation`` Rule 2): a single
    malformed YAML is logged at WARNING level and skipped; the scan
    continues. Other personas remain loadable. The error class is captured
    in the structured log event so debug + alerting downstream can detect
    parse-error spikes.

    Cache: process-scoped ``functools.cache`` (alias of ``lru_cache(maxsize=None)``)
    per D6. Tests that mutate ``_PERSONAS_ROOT`` MUST call
    ``_scan_personas_directory.cache_clear()`` before exercising the loader
    (the conftest autouse fixture does so).
    """
    index: dict[tuple[str, str], Path] = {}
    if not _PERSONAS_ROOT.exists():
        # Defensive — if the catalog directory is absent (e.g., partial
        # clone, test fixture pointing to non-existent path) return an
        # empty index. The loader will then raise FileNotFoundError on
        # any (slug, kind) lookup, which is the right behavior.
        logger.warning(
            "personas_loader.root_missing",
            personas_root=str(_PERSONAS_ROOT),
        )
        return index

    for path in _PERSONAS_ROOT.rglob("*.yaml"):
        # Skip the legacy preserved subdir (D2).
        if _LEGACY_DIR_NAME in path.parts:
            continue
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            logger.warning(
                "personas_loader.yaml_parse_skipped",
                path=str(path),
                error_class=type(exc).__name__,
            )
            continue
        except OSError as exc:
            # File became unreadable mid-scan — log + skip.
            logger.warning(
                "personas_loader.yaml_read_failed",
                path=str(path),
                error_class=type(exc).__name__,
            )
            continue
        if not isinstance(raw, dict):
            # Empty / list-rooted / scalar YAML — not a persona entry.
            continue
        metadata = raw.get("metadata", {})
        slug = metadata.get("tenant_slug") if isinstance(metadata, dict) else None
        kind = raw.get("persona_kind")
        if slug is None or kind is None:
            continue
        index[(str(slug), str(kind))] = path
    return index


# ════════════════════════════════════════════════════════════════════════
# Public — main loader
# ════════════════════════════════════════════════════════════════════════


@cache
def load_actor_profile_for_tenant(
    tenant_slug: str,
    persona_kind: PersonaKind = "happy",
) -> ActorProfile:
    """Resolve ``(tenant_slug, persona_kind) → ActorProfile``.

    Process-scoped ``functools.cache`` (alias of ``lru_cache(maxsize=None)``)
    per D6 — repeat calls with the same args return the SAME instance
    (``is`` identity). The ActorProfile is Pydantic ``frozen=True`` so sharing
    across consumers is safe.

    Validation chain:

    1. ``tenant_slug ∈ _VALID_TENANT_SLUGS`` (D5 fail-fast).
    2. ``(slug, kind)`` exists in the directory index (FileNotFoundError
       lists available kinds for the slug to aid diagnostics).
    3. Story B ``apply_migrations("ActorProfile", raw, target_version)``
       runs the registered migrator chain (v1 → v2 identity for now).
    4. ``D-AG-1`` cross-check: ``raw["dialect_code"] == ARCHETYPE_DIALECT_MAP[slug]``
       — mismatch raises ``ValueError`` BEFORE Pydantic validate.
    5. ``ActorProfile.model_validate(raw)`` — Pydantic ConfigDict
       ``extra="forbid"`` catches schema drift.

    Args:
        tenant_slug: One of 5 Story A seed slugs.
        persona_kind: One of 6 D13 v2 Literal values. Defaults to ``"happy"``.

    Returns:
        Frozen ActorProfile (Pydantic v2 ``ConfigDict(frozen=True)``).

    Raises:
        KeyError: ``tenant_slug`` not in valid 5 OR
            ``persona_kind`` not in matriz (helper-only callers).
        FileNotFoundError: ``(slug, kind)`` has no YAML in
            ``archetype-aware/``. Available kinds for the slug listed
            in the message.
        TypeError: target YAML root is not a mapping (e.g., scalar or
            list). Schema requires a top-level dict.
        ValueError: Persona's ``dialect_code`` mismatches
            ``ARCHETYPE_DIALECT_MAP[tenant_slug]`` (D-AG-1).
        pydantic.ValidationError: YAML schema invalid (missing required
            fields, type mismatches, etc.).
        yaml.YAMLError: target YAML is malformed (the directory scan
            skips malformed siblings, but if the TARGET file itself is
            malformed we surface the error rather than guessing).
    """
    if tenant_slug not in _VALID_TENANT_SLUGS:
        valid = sorted(_VALID_TENANT_SLUGS)
        msg = f"tenant_slug {tenant_slug!r} not in valid eval seed slugs. Valid: {valid}"
        raise KeyError(msg)

    index = _scan_personas_directory()
    key = (tenant_slug, str(persona_kind))
    if key not in index:
        available_kinds = sorted({k for (s, k) in index if s == tenant_slug})
        msg = (
            f"No persona YAML for ({tenant_slug!r}, {persona_kind!r}). Available kinds for this slug: {available_kinds}"
        )
        raise FileNotFoundError(msg)

    yaml_path = index[key]
    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        msg = f"Persona YAML at {yaml_path} did not deserialize to a dict (got {type(raw).__name__})"
        raise TypeError(msg)

    # Apply Story B SCHEMA_MIGRATIONS chain to current ActorProfile schema_version.
    target_version = CURRENT_SCHEMA_VERSIONS.get("ActorProfile", 2)
    migrated = apply_migrations("ActorProfile", raw, target_version)

    # D-AG-1 cross-check — strict ARCHETYPE_DIALECT_MAP match.
    # Imported lazily to avoid pulling Story A loader into module-import
    # graph at collection time (Story A loader has its own side effects
    # we don't want triggered just by importing this module).
    from tests.fixtures.eval.tenants.loader import ARCHETYPE_DIALECT_MAP

    expected_dialect = ARCHETYPE_DIALECT_MAP[tenant_slug]
    actual_dialect = migrated.get("dialect_code")
    if actual_dialect != expected_dialect:
        msg = (
            f"persona {migrated.get('id')!r} declares dialect_code "
            f"{actual_dialect!r} but tenant {tenant_slug!r} requires "
            f"{expected_dialect!r} per ARCHETYPE_DIALECT_MAP (D-AG-1)"
        )
        raise ValueError(msg)

    return ActorProfile.model_validate(migrated)


# ════════════════════════════════════════════════════════════════════════
# Public — max_turns matriz helper
# ════════════════════════════════════════════════════════════════════════


def get_max_turns_for_persona_kind(persona_kind: PersonaKind) -> int:
    """Resolve the ``max_turns`` cap for a given persona kind (D15 matriz).

    Used by Scenarios 5+6 (`test_simulator_smoke.py`) to bound simulation
    length. Loader-only kinds (`edge`, `negative`) raise ``KeyError`` per
    D-AG-10 — they are diagnostic schema slots, not runtime persona kinds.

    Args:
        persona_kind: One of 6 D13 v2 Literal values, but only 4 are
            valid here (happy, nurture, unqualified, adversarial).

    Returns:
        Integer turn cap per matriz.

    Raises:
        KeyError: ``persona_kind`` not in matriz (e.g., ``edge``,
            ``negative``, or any unknown value). Error message lists
            valid matriz keys.
    """
    if persona_kind not in _MAX_TURNS_BY_PERSONA_KIND:
        valid = sorted(_MAX_TURNS_BY_PERSONA_KIND.keys())
        msg = (
            f"persona_kind {persona_kind!r} has no max_turns matriz entry. "
            f"Loader-only kinds (edge, negative) do not invoke graph. "
            f"Valid: {valid}"
        )
        raise KeyError(msg)
    return _MAX_TURNS_BY_PERSONA_KIND[persona_kind]


__all__ = [
    "PersonaKind",
    "get_max_turns_for_persona_kind",
    "load_actor_profile_for_tenant",
]
