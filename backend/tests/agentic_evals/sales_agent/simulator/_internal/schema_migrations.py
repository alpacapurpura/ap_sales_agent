"""Schema migrations registry — H1 forward-compat for Pydantic state machines.

Pattern: ``dict[(model_class_name, prev_version, curr_version), migrator_callable]``.

Each migrator: ``Callable[[dict[str, object]], dict[str, object]]`` — receives a raw dict at version
``prev_version`` and returns the migrated raw dict at version ``curr_version``.

Story B ships at v1 only — registry is intentionally **empty**. Future schema
bumps register a migrator in this file in the SAME COMMIT that bumps
``CURRENT_SCHEMA_VERSIONS``. Arch fitness gate
``test_schema_migrations_registry_complete.py`` verifies exhaustiveness.

Frozen golden v1 fixture (T-9) checked-in at
``simulator/_fixtures/golden_v1_simulation_result.yaml`` — NEVER edit.
Regression test (T-10) loads + asserts deserializable to current schema (with
migration chain applied if needed).

Public API:
    - SCHEMA_MIGRATIONS — registry dict
    - CURRENT_SCHEMA_VERSIONS — pinpoint active version per Pydantic class
    - apply_migrations(model_name, raw_data, target_version) — chain function
    - register_schema_migration — decorator helper

# voseo-allowed: docstring del módulo cita escape rule pre-commit hook regional
"""

from __future__ import annotations

from collections.abc import Callable

# ════════════════════════════════════════════════════════════════════════
# Active schema versions per Pydantic class shipped by Story B
# ════════════════════════════════════════════════════════════════════════
#
# Story B baseline: every class at v1.
# Future stories bump versions here AND register migrators below.

CURRENT_SCHEMA_VERSIONS: dict[str, int] = {
    "SimulationState": 1,
    "ActorProfile": 1,
    "SimulationResult": 1,
    "ConversationTurn": 1,
    "CostSummary": 1,
}


# ════════════════════════════════════════════════════════════════════════
# Migrators registry per hardening invariant H1
# ════════════════════════════════════════════════════════════════════════
#
# Story B: registry intentionally empty. Arch test asserts:
# - For every (model_name, curr_v) with curr_v > 1, chain (1→2, 2→3, …,
#   prev→curr) MUST exist en este dict.
# - Story B: all curr_v == 1, registry empty is valid.
#
# Future schema bump pattern (documented inside the variable docstring
# below to avoid lint ERA001 commented-out-code false positive).

SCHEMA_MIGRATIONS: dict[tuple[str, int, int], Callable[[dict[str, object]], dict[str, object]]] = {}
"""Registry of forward-compat migrators.

Add an entry on schema bump using ``@register_schema_migration``::

    @register_schema_migration("ActorProfile", 1, 2)
    def _bump_actor_profile_v1_to_v2(raw):
        raw.setdefault("new_field", "default_value")
        return raw

Never delete a migrator that has shipped — frozen golden v1 fixture (T-10)
relies on the chain to deserialize older artifacts on schema bumps.
"""


def register_schema_migration(
    model_name: str, prev_version: int, curr_version: int
) -> Callable[[Callable[[dict[str, object]], dict[str, object]]], Callable[[dict[str, object]], dict[str, object]]]:
    """Decorator: register a migrator for ``(model_name, prev → curr)``.

    Idempotent on the triple key — re-registration overrides the previous
    migrator. Use only on schema bumps; never edit a published migrator
    (would invalidate frozen golden assertions in T-10).

    Raises:
        ValueError: when ``curr_version <= prev_version`` (chain must move forward).
    """
    if curr_version <= prev_version:
        msg = (
            f"register_schema_migration: curr_version ({curr_version}) "
            f"must be > prev_version ({prev_version}) for {model_name!r}"
        )
        raise ValueError(msg)

    def _decorator(
        fn: Callable[[dict[str, object]], dict[str, object]],
    ) -> Callable[[dict[str, object]], dict[str, object]]:
        SCHEMA_MIGRATIONS[(model_name, prev_version, curr_version)] = fn
        return fn

    return _decorator


def apply_migrations(model_name: str, raw_data: dict[str, object], target_version: int) -> dict[str, object]:
    """Apply chain of migrators for ``model_name`` from current → target_version.

    Reads ``raw_data["schema_version"]`` (defaults 1) as starting version and
    walks ``(prev → prev+1)`` migrators until reaching ``target_version``.

    Args:
        model_name: must be a key of CURRENT_SCHEMA_VERSIONS — unknown
            models pass-through as no-op (defensive).
        raw_data: deserialized dict (e.g., loaded from YAML golden fixture).
        target_version: desired schema_version for caller.

    Returns:
        New dict (or ``raw_data`` itself when no chain step applies).

    Raises:
        KeyError: when target_version > current_version and a chain step
            (prev → prev+1) has no registered migrator. The error message
            includes model_name + prev → curr to aid diagnostics.
    """
    if model_name not in CURRENT_SCHEMA_VERSIONS:
        # Unregistered model — no migrations to apply, return raw passthrough.
        return raw_data

    current_version_obj = raw_data.get("schema_version", 1)
    current_version = int(current_version_obj) if isinstance(current_version_obj, (int, str)) else 1
    if current_version >= target_version:
        return raw_data

    # Walk chain forward
    data = raw_data
    for prev in range(current_version, target_version):
        curr = prev + 1
        key = (model_name, prev, curr)
        migrator = SCHEMA_MIGRATIONS.get(key)
        if migrator is None:
            msg = (
                f"Missing schema migration for {model_name}: "
                f"{prev} → {curr}. Register a migrator in "
                f"`_internal/schema_migrations.py::SCHEMA_MIGRATIONS` to "
                f"unblock forward-compat regression."
            )
            raise KeyError(msg)
        data = migrator(data)
        # Defensive: ensure migrator advanced version field
        data.setdefault("schema_version", curr)
    return data


__all__ = [
    "CURRENT_SCHEMA_VERSIONS",
    "SCHEMA_MIGRATIONS",
    "apply_migrations",
    "register_schema_migration",
]
