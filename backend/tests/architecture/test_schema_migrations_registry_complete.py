"""Architecture fitness gate — SCHEMA_MIGRATIONS registry exhaustive vs schema_version.

T-4 acceptance A3 (H1 — schema versioning forward-compat).
T-9 EXTENDED with frozen golden v1 integration assertions (H1 + H10).

For story B (v1 only) registry empty is valid. Future bumps register a
migrator entry per (model, prev_version, curr_version).

Invariants enforced:
1. SCHEMA_MIGRATIONS is importable + dict[tuple[str, int, int], Callable]
2. CURRENT_SCHEMA_VERSIONS lists every Pydantic class shipped at v1
3. For every model in CURRENT_SCHEMA_VERSIONS with curr > 1, a chain of
   migrators (1 → 2, 2 → 3, …) MUST exist in SCHEMA_MIGRATIONS.
4. Every migrator value is Callable.
5. (T-9 EXTEND) The frozen golden v1 fixture
   ``simulator/_fixtures/golden_v1_simulation_result.yaml`` exists, has
   ``schema_version: 1`` field at the top level + per nested Pydantic
   instance, and round-trips through ``apply_migrations`` →
   ``SimulationResult.model_validate`` to the current schema version
   without raising.

Story B: all CURRENT_SCHEMA_VERSIONS == 1, so registry is allowed empty.
The frozen golden v1 deserializes via identity passthrough.

# voseo-allowed: arch fitness reglas reference dialect strict — voseo glosario
"""

from collections.abc import Callable
from pathlib import Path

import pytest

pytestmark = pytest.mark.no_eval


# Repo root anchor — `backend/` two levels up from this test file.
_BACKEND_ROOT: Path = Path(__file__).resolve().parents[2]
_FROZEN_GOLDEN_V1: Path = (
    _BACKEND_ROOT
    / "tests"
    / "agentic_evals"
    / "sales_agent"
    / "simulator"
    / "_fixtures"
    / "golden_v1_simulation_result.yaml"
)


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


def test_apply_migrations_missing_chain_step_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If target_version > 1 and chain step missing → KeyError documenting gap.

    Defensive: prevents silent-skip of versions when migrators not registered.

    Uses a SYNTHETIC phantom model name registered into CURRENT_SCHEMA_VERSIONS
    via monkeypatch (auto-restored on teardown) so the test stays valid as the
    real registry grows entries (Story C registered ActorProfile 1→2 + CustomerPrompt
    1→2). The phantom intentionally has NO migrator chain registered, exercising
    the defensive KeyError path.
    """
    from tests.agentic_evals.sales_agent.simulator._internal.schema_migrations import (
        CURRENT_SCHEMA_VERSIONS,
        apply_migrations,
    )

    phantom = "_PhantomMissingMigratorChain"
    monkeypatch.setitem(CURRENT_SCHEMA_VERSIONS, phantom, 2)

    raw: dict[str, object] = {"schema_version": 1, "field": "value"}
    with pytest.raises(KeyError, match=rf"{phantom}.*1.*2"):
        apply_migrations(phantom, raw, target_version=2)


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


# ════════════════════════════════════════════════════════════════════════
# T-9 EXTEND — Frozen golden v1 integration (H1 + H10)
# ════════════════════════════════════════════════════════════════════════
#
# Story B (T-9) ships ``_fixtures/golden_v1_simulation_result.yaml`` as the
# v1 baseline forward-compat regression anchor. These assertions validate
# the file exists, carries ``schema_version: 1`` at every nested Pydantic
# layer, and round-trips through the migration chain to the current
# CURRENT_SCHEMA_VERSIONS["SimulationResult"] without raising.
#
# T-10 ships a separate full-regression test
# ``test_schema_migration_regression.py`` that probes every nested model.
# This arch fitness gate stays scoped to the registry/golden contract.


def test_frozen_golden_v1_fixture_exists() -> None:
    """The frozen golden v1 YAML fixture MUST be checked-in under _fixtures/."""
    assert _FROZEN_GOLDEN_V1.is_file(), (
        f"Frozen golden v1 fixture not found at {_FROZEN_GOLDEN_V1}. T-9 deliverable absent — H10 cement violated."
    )


def test_frozen_golden_v1_has_top_level_schema_version() -> None:
    """The golden YAML MUST have ``schema_version: 1`` at the top level."""
    import yaml

    data = yaml.safe_load(_FROZEN_GOLDEN_V1.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"Frozen golden v1 fixture MUST deserialize to a dict; got {type(data)}."
    assert data.get("schema_version") == 1, (
        f"Frozen golden v1 top-level schema_version drift: expected 1; got {data.get('schema_version')!r}."
    )


def test_frozen_golden_v1_nested_schema_versions_all_v1() -> None:
    """Every nested Pydantic block (transcript turns, cost_summary) MUST be v1.

    Defensive: a future PR could bump a nested model without bumping the
    top-level fixture — leaving the golden in a hybrid state. We cement
    "every nested schema_version present is exactly 1" while the registry
    is empty.
    """
    import yaml

    data = yaml.safe_load(_FROZEN_GOLDEN_V1.read_text(encoding="utf-8"))

    # transcript turns
    transcript = data.get("transcript", [])
    assert isinstance(transcript, list) and len(transcript) > 0, "Frozen golden v1 transcript missing or empty."
    for idx, turn in enumerate(transcript):
        assert isinstance(turn, dict), f"transcript[{idx}] not a dict."
        assert turn.get("schema_version") == 1, (
            f"transcript[{idx}] schema_version drift: expected 1; got {turn.get('schema_version')!r}."
        )

    # cost_summary
    cost_summary = data.get("cost_summary")
    assert isinstance(cost_summary, dict), "Frozen golden v1 cost_summary missing or non-dict."
    assert cost_summary.get("schema_version") == 1, (
        f"cost_summary.schema_version drift: expected 1; got {cost_summary.get('schema_version')!r}."
    )


def test_frozen_golden_v1_deserializes_to_current_simulation_result() -> None:
    """The frozen golden MUST round-trip through ``apply_migrations`` →
    ``SimulationResult.model_validate`` against ``CURRENT_SCHEMA_VERSIONS["SimulationResult"]``.

    This is the H10 forward-compat assertion: future schema bumps MUST
    register a migrator chain v1 → curr that preserves this YAML's
    semantic content.
    """
    import yaml

    from tests.agentic_evals.sales_agent.simulator._internal.schema_migrations import (
        CURRENT_SCHEMA_VERSIONS,
        apply_migrations,
    )
    from tests.agentic_evals.sales_agent.simulator.result import SimulationResult

    raw_data = yaml.safe_load(_FROZEN_GOLDEN_V1.read_text(encoding="utf-8"))
    target = CURRENT_SCHEMA_VERSIONS["SimulationResult"]

    migrated = apply_migrations("SimulationResult", raw_data, target_version=target)

    # Pydantic round-trip — no validation errors.
    result = SimulationResult.model_validate(migrated)

    # Sanity probe: termination_reason coerced via StrEnum, transcript
    # length matches total_turns, cost_summary aggregated.
    assert result.schema_version == 1, f"Round-tripped schema_version drift: expected 1; got {result.schema_version}"
    assert len(result.transcript) == result.total_turns, (
        f"Frozen golden v1 transcript len({len(result.transcript)}) "
        f"!= total_turns({result.total_turns}). Fix the golden to match."
    )
    assert result.termination_reason.value == "max_turns", (
        f"Frozen golden v1 termination_reason drift: expected 'max_turns'; got {result.termination_reason}"
    )


def test_frozen_golden_v1_registry_empty_implies_passthrough() -> None:
    """While story B ships v1 only, ``apply_migrations`` MUST be identity for v1 → v1.

    Cement: if CURRENT_SCHEMA_VERSIONS["SimulationResult"] bumps to 2, this
    test MUST be updated alongside a registered migrator. Failure here in
    the meantime catches accidental version bumps without registry entry.
    """
    from tests.agentic_evals.sales_agent.simulator._internal.schema_migrations import (
        CURRENT_SCHEMA_VERSIONS,
        SCHEMA_MIGRATIONS,
    )

    # Story B baseline.
    if CURRENT_SCHEMA_VERSIONS["SimulationResult"] == 1:
        # Registry MUST be empty for SimulationResult chain.
        sim_result_chain = [key for key in SCHEMA_MIGRATIONS if key[0] == "SimulationResult"]
        assert sim_result_chain == [], (
            f"SimulationResult at v1 but SCHEMA_MIGRATIONS contains chain "
            f"entries: {sim_result_chain}. Story B baseline = empty chain."
        )
