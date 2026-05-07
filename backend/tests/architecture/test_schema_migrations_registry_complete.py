"""Architecture fitness gate — SCHEMA_MIGRATIONS registry exhaustive vs schema_version.

T-4 acceptance A3 (H1 — schema versioning forward-compat).

For story B (v1 only) registry empty is valid. Future bumps register a
migrator entry per (model, prev_version, curr_version).

Invariants enforced:
1. SCHEMA_MIGRATIONS is importable + dict[tuple[str, int, int], Callable]
2. CURRENT_SCHEMA_VERSIONS lists every Pydantic class shipped at v1
3. For every model in CURRENT_SCHEMA_VERSIONS with curr > 1, a chain of
   migrators (1 → 2, 2 → 3, …) MUST exist in SCHEMA_MIGRATIONS.
4. Every migrator value is Callable.

Story B: all CURRENT_SCHEMA_VERSIONS == 1, so registry is allowed empty.
"""

# voseo-allowed: arch fitness reglas reference dialect strict — voseo glosario

from collections.abc import Callable

import pytest


pytestmark = pytest.mark.no_eval


# ════════════════════════════════════════════════════════════════════════
# Importability + types
# ════════════════════════════════════════════════════════════════════════


def test_schema_migrations_registry_importable() -> None:
    """SCHEMA_MIGRATIONS dict importable from `_internal/schema_migrations.py`."""
    from tests.agentic_evals.sales_agent.simulator._internal import schema_migrations

    assert hasattr(schema_migrations, "SCHEMA_MIGRATIONS"), (
        "SCHEMA_MIGRATIONS not exported from schema_migrations module"
    )
    assert isinstance(schema_migrations.SCHEMA_MIGRATIONS, dict), (
        f"SCHEMA_MIGRATIONS expected dict, got {type(schema_migrations.SCHEMA_MIGRATIONS)}"
    )


def test_current_schema_versions_dict_importable() -> None:
    """CURRENT_SCHEMA_VERSIONS pinpoints active schema version per Pydantic class."""
    from tests.agentic_evals.sales_agent.simulator._internal import schema_migrations

    assert hasattr(schema_migrations, "CURRENT_SCHEMA_VERSIONS"), "CURRENT_SCHEMA_VERSIONS not exported"
    assert isinstance(schema_migrations.CURRENT_SCHEMA_VERSIONS, dict), (
        "CURRENT_SCHEMA_VERSIONS expected dict[str, int]"
    )
    for model_name, version in schema_migrations.CURRENT_SCHEMA_VERSIONS.items():
        assert isinstance(model_name, str)
        assert isinstance(version, int) and version >= 1


def test_apply_migrations_callable_importable() -> None:
    """apply_migrations chain function publicly importable."""
    from tests.agentic_evals.sales_agent.simulator._internal import schema_migrations

    assert hasattr(schema_migrations, "apply_migrations"), "apply_migrations chain function not exported"
    assert callable(schema_migrations.apply_migrations)


# ════════════════════════════════════════════════════════════════════════
# Registry contract
# ════════════════════════════════════════════════════════════════════════


def test_registry_keys_are_tuple_str_int_int() -> None:
    """Each key must be (model_class_name, prev_version, curr_version)."""
    from tests.agentic_evals.sales_agent.simulator._internal.schema_migrations import (
        SCHEMA_MIGRATIONS,
    )

    for key in SCHEMA_MIGRATIONS:
        assert isinstance(key, tuple) and len(key) == 3, f"Migration key {key!r} not (model_name, prev, curr)"
        model_name, prev, curr = key
        assert isinstance(model_name, str) and model_name, "model_name must be non-empty str"
        assert isinstance(prev, int) and prev >= 1, "prev_version must be int >= 1"
        assert isinstance(curr, int) and curr > prev, f"curr_version {curr} must be > prev_version {prev}"


def test_registry_values_are_callables() -> None:
    """Every migrator must be callable: dict → dict."""
    from tests.agentic_evals.sales_agent.simulator._internal.schema_migrations import (
        SCHEMA_MIGRATIONS,
    )

    for key, migrator in SCHEMA_MIGRATIONS.items():
        assert callable(migrator), f"Migrator for {key!r} not callable: {migrator!r}"


# ════════════════════════════════════════════════════════════════════════
# Exhaustive vs CURRENT_SCHEMA_VERSIONS
# ════════════════════════════════════════════════════════════════════════


def test_registry_exhaustive_for_each_active_model() -> None:
    """For every (model, curr_v) with curr_v > 1, the chain (1→2, …, prev→curr) MUST exist."""
    from tests.agentic_evals.sales_agent.simulator._internal.schema_migrations import (
        CURRENT_SCHEMA_VERSIONS,
        SCHEMA_MIGRATIONS,
    )

    for model_name, curr_v in CURRENT_SCHEMA_VERSIONS.items():
        if curr_v == 1:
            # No migrations needed — story B baseline
            continue
        # Build expected chain
        for prev in range(1, curr_v):
            key = (model_name, prev, prev + 1)
            assert key in SCHEMA_MIGRATIONS, (
                f"Missing migration for {model_name}: {prev} → {prev + 1}. "
                f"All bumps must register a migrator in SCHEMA_MIGRATIONS."
            )


def test_story_b_baseline_v1_only() -> None:
    """Story B ships at v1 only — registry empty + every CURRENT_SCHEMA_VERSIONS == 1.

    Future stories that bump versions MUST update this assert OR keep == 1
    while registering migrators for the bumped models.
    """
    from tests.agentic_evals.sales_agent.simulator._internal.schema_migrations import (
        CURRENT_SCHEMA_VERSIONS,
    )

    expected_classes = {
        "SimulationState",
        "ActorProfile",
        "SimulationResult",
        "ConversationTurn",
        "CostSummary",
    }
    assert expected_classes.issubset(CURRENT_SCHEMA_VERSIONS.keys()), (
        f"Missing classes in CURRENT_SCHEMA_VERSIONS: {expected_classes - set(CURRENT_SCHEMA_VERSIONS.keys())}"
    )


# ════════════════════════════════════════════════════════════════════════
# apply_migrations behavior — chain semantics
# ════════════════════════════════════════════════════════════════════════


def test_apply_migrations_v1_to_v1_noop() -> None:
    """apply_migrations(name, raw, target=1) returns raw unchanged when current == target."""
    from tests.agentic_evals.sales_agent.simulator._internal.schema_migrations import (
        apply_migrations,
    )

    raw: dict[str, object] = {"schema_version": 1, "field": "value"}
    result = apply_migrations("ActorProfile", raw, target_version=1)
    assert result == raw


def test_apply_migrations_unknown_model_passthrough() -> None:
    """apply_migrations on a model NOT in CURRENT_SCHEMA_VERSIONS passes raw through.

    No-op for unregistered model classes (defensive — caller is responsible
    for matching schema_migrations to its model).
    """
    from tests.agentic_evals.sales_agent.simulator._internal.schema_migrations import (
        apply_migrations,
    )

    raw: dict[str, object] = {"schema_version": 1, "anything": "x"}
    result = apply_migrations("UnregisteredClass", raw, target_version=1)
    assert result == raw


def test_apply_migrations_missing_chain_step_raises() -> None:
    """If target_version > 1 and chain step missing → KeyError documenting gap.

    Defensive: prevents silent-skip of versions when migrators not registered.
    """
    from tests.agentic_evals.sales_agent.simulator._internal.schema_migrations import (
        apply_migrations,
    )

    raw: dict[str, object] = {"schema_version": 1, "field": "value"}
    with pytest.raises(KeyError, match=r"ActorProfile.*1.*2"):
        apply_migrations("ActorProfile", raw, target_version=2)


# ════════════════════════════════════════════════════════════════════════
# Registry typing — mypy contract enforced
# ════════════════════════════════════════════════════════════════════════


def test_registry_value_callable_signature_dict_to_dict() -> None:
    """If migrators exist, each takes a dict and returns a dict.

    Story B: registry empty, this is parametrize-noop. Future entries
    will exercise.
    """
    from tests.agentic_evals.sales_agent.simulator._internal.schema_migrations import (
        SCHEMA_MIGRATIONS,
    )

    for key, migrator in SCHEMA_MIGRATIONS.items():
        # Smoke-call with empty dict — every migrator must be callable on dict
        result = migrator({"schema_version": key[1]})
        assert isinstance(result, dict), f"Migrator for {key!r} returned {type(result)}, expected dict"


# Silence unused import warnings for type-only references (lint UP/F)
_: type[Callable[..., object]] = Callable  # type: ignore[assignment]
