"""Forward-compat schema migration registry for GoldenScenarioModel.

Pattern PARALLEL to Story B `simulator/_internal/schema_migrations.py` —
distinct namespace, distinct lifecycle:
    - Goldens bumps = YAML data format changes (triggered by Chris manual
      refresh per D15 when Story C personas bump schema or grader saturates)
    - Simulator bumps = Pydantic code state machine changes (story-driven)

This module does NOT import from `simulator/_internal/schema_migrations.py`.
Arch fitness gate `test_goldens_no_mirror_simulator_schema.py` enforces this.

Story D v1 cement: registry intentionally empty. First future bump registers
an identity-or-transform migrator in the SAME COMMIT that bumps
CURRENT_GOLDEN_SCHEMA_VERSIONS. Arch fitness gate
`test_goldens_schema_completeness.py` verifies exhaustiveness.

Public API:
    - GOLDEN_SCHEMA_MIGRATIONS  — registry dict
    - CURRENT_GOLDEN_SCHEMA_VERSIONS — active version per class
    - GoldenMigrator            — type alias for migrator callables
    - register_golden_migration — decorator helper
    - apply_golden_migrations   — chain applier

# voseo-allowed: docstring cites pre-commit hook escape rule regional patterns
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Final

# ── Type alias ───────────────────────────────────────────────────────────────
GoldenMigrator = Callable[[dict[str, object]], dict[str, object]]
"""Migrator callable: receives a raw dict at `from_version` and returns migrated dict."""

# ── Active schema versions per Pydantic class (D6 cement) ────────────────────
#
# Story D ships at v1 only — all classes at v1.
# Future bumps: update version here AND register migrators below.
# Arch gate `test_goldens_schema_completeness.py::test_golden_schema_migrations_registry_exhaustive_if_bumped`
# verifies exhaustiveness.
CURRENT_GOLDEN_SCHEMA_VERSIONS: Final[dict[str, int]] = {
    "GoldenScenarioModel": 1,
}

GOLDEN_SCHEMA_MIGRATIONS: Final[dict[tuple[str, int, int], GoldenMigrator]] = {}
"""Registry of forward-compat YAML migrators for golden scenario format.

Add an entry on schema bump using @register_golden_migration decorator.
Never delete a migrator that has shipped — frozen golden YAMLs rely on
the chain to deserialize older format on schema bumps.
"""


def register_golden_migration(
    class_name: str,
    from_version: int,
    to_version: int,
) -> Callable[[GoldenMigrator], GoldenMigrator]:
    """Decorator — register a golden YAML migrator for (class_name, from → to).

    Args:
        class_name: Pydantic model class name (e.g. 'GoldenScenarioModel').
        from_version: schema_version of the source format.
        to_version: schema_version of the target format.

    Returns:
        Decorator that registers the migrator and returns it unchanged.

    Raises:
        ValueError: if from_version >= to_version (chain must advance).
        ValueError: if the (class_name, from_version, to_version) key already registered.
    """
    if to_version <= from_version:
        msg = (
            f"register_golden_migration: to_version ({to_version}) must be > "
            f"from_version ({from_version}) for {class_name!r}"
        )
        raise ValueError(msg)

    def _decorator(fn: GoldenMigrator) -> GoldenMigrator:
        key = (class_name, from_version, to_version)
        if key in GOLDEN_SCHEMA_MIGRATIONS:
            msg = f"Duplicate golden migration registration: {key}"
            raise ValueError(msg)
        GOLDEN_SCHEMA_MIGRATIONS[key] = fn  # Final dict — writing is safe at module init time
        return fn

    return _decorator


def apply_golden_migrations(
    class_name: str,
    raw: dict[str, object],
    target_version: int,
) -> dict[str, object]:
    """Apply chain of goldens migrators from raw['schema_version'] to target_version.

    Args:
        class_name: must be a key of CURRENT_GOLDEN_SCHEMA_VERSIONS.
            Unregistered models pass through as no-op (defensive).
        raw: deserialized dict (e.g. loaded from YAML golden file).
        target_version: desired schema_version for caller.

    Returns:
        Migrated dict (or raw itself if already at target_version).

    Raises:
        KeyError: when target_version > current version and a chain step
            (prev → prev+1) has no registered migrator. Error message
            includes class_name + missing step for diagnostics.
    """
    if class_name not in CURRENT_GOLDEN_SCHEMA_VERSIONS:
        # Unregistered class — pass through (defensive no-op)
        return raw

    current_version_obj = raw.get("schema_version", 1)
    current_version = int(current_version_obj) if isinstance(current_version_obj, (int, str)) else 1
    if current_version >= target_version:
        return raw

    data = raw
    for prev in range(current_version, target_version):
        curr = prev + 1
        key = (class_name, prev, curr)
        migrator = GOLDEN_SCHEMA_MIGRATIONS.get(key)
        if migrator is None:
            msg = (
                f"Missing golden migration for {class_name}: {prev} → {curr}. "
                f"Register a migrator via @register_golden_migration in "
                f"`goldens/_schema_migrations.py::GOLDEN_SCHEMA_MIGRATIONS` to "
                f"unblock forward-compat for this golden YAML format."
            )
            raise KeyError(msg)
        data = migrator(data)
        # Defensive: ensure migrator advanced version field
        if isinstance(data, dict) and "schema_version" not in data:
            data = {**data, "schema_version": curr}
    return data


__all__ = [
    "CURRENT_GOLDEN_SCHEMA_VERSIONS",
    "GOLDEN_SCHEMA_MIGRATIONS",
    "GoldenMigrator",
    "apply_golden_migrations",
    "register_golden_migration",
]
