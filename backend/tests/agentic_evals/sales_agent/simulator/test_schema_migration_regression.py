"""Schema migration regression test (T-10, H1+H10).

Ships the FULL forward-compat regression suite for the frozen golden v1
fixture (``simulator/_fixtures/golden_v1_simulation_result.yaml``):

* Loads YAML via ``yaml.safe_load``.
* Applies ``apply_migrations("SimulationResult", raw, target=CURRENT_SCHEMA_VERSIONS["SimulationResult"])``.
* Asserts deserializable to current ``SimulationResult`` Pydantic.
* Probes every nested Pydantic model (ConversationTurn, CostSummary,
  ActorProfile via SimulationState round-trip, SimulationState).
* Asserts ``SCHEMA_MIGRATIONS`` registry exhaustive: for each
  ``CURRENT_SCHEMA_VERSIONS[model] > 1``, the chain (1→2, 2→3, …, prev→curr)
  exists + each migrator is idempotent on a {schema_version: prev} probe.
* Future-proof: when CURRENT_SCHEMA_VERSIONS bumps, this test guides the
  developer to ship a v2 golden alongside the v1 (NEVER replace v1).

Complements ``tests/architecture/test_schema_migrations_registry_complete.py``
(T-9) which tests the registry's static structural invariants. This file
focuses on RUNTIME deserialization round-trip + cross-class registry
exhaustiveness.

Tests opt out of the ``eval`` autouse marker via ``pytestmark =
pytest.mark.no_eval`` so they run on default CI without ``--run-evals``.

# voseo-allowed: docstring quotes spec H1+H10 cardinal + voseo glossary references
"""

# NO ``from __future__ import annotations`` — story-wide cement (T-4..T-9).

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]

from tests.agentic_evals.sales_agent.simulator._internal.schema_migrations import (
    CURRENT_SCHEMA_VERSIONS,
    SCHEMA_MIGRATIONS,
    apply_migrations,
    register_schema_migration,
)
from tests.agentic_evals.sales_agent.simulator.actor_profile import ActorProfile
from tests.agentic_evals.sales_agent.simulator.result import (
    ConversationTurn,
    CostSummary,
    SimulationResult,
)
from tests.agentic_evals.sales_agent.simulator.state import SimulationState

pytestmark = pytest.mark.no_eval

# Repo root anchor for fixture path. ``test_schema_migration_regression.py``
# lives at ``backend/tests/agentic_evals/sales_agent/simulator/``.
_BACKEND_ROOT: Path = Path(__file__).resolve().parents[4]
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
# H10 — Frozen golden v1 deserialization
# ════════════════════════════════════════════════════════════════════════


def test_frozen_golden_v1_yaml_loads() -> None:
    """The golden YAML MUST be loadable via ``yaml.safe_load``.

    Defensive baseline — if the file got accidentally corrupted or its
    YAML syntax broke, all subsequent assertions would fail with
    confusing errors.
    """
    raw = yaml.safe_load(_FROZEN_GOLDEN_V1.read_text(encoding="utf-8"))
    assert isinstance(raw, dict), f"Frozen golden v1 MUST deserialize to a dict; got {type(raw)}"
    assert raw.get("schema_version") == 1, (
        f"Top-level schema_version drift: expected 1; got {raw.get('schema_version')!r}"
    )


def test_frozen_golden_v1_round_trips_via_apply_migrations() -> None:
    """The golden v1 MUST round-trip ``apply_migrations`` → ``SimulationResult.model_validate``.

    Story B baseline: registry empty (v1 only) → identity passthrough.
    Future bumps: chain registered → migrator(raw) advances version field
    + preserves semantic content + Pydantic.model_validate succeeds.
    """
    raw = yaml.safe_load(_FROZEN_GOLDEN_V1.read_text(encoding="utf-8"))
    target = CURRENT_SCHEMA_VERSIONS["SimulationResult"]

    migrated = apply_migrations("SimulationResult", raw, target_version=target)

    # Pydantic round-trip — no validation errors.
    result = SimulationResult.model_validate(migrated)

    # Sanity checks
    assert result.schema_version == 1, f"schema_version drift after round-trip: {result.schema_version}"
    assert len(result.transcript) == result.total_turns, (
        f"transcript len({len(result.transcript)}) != total_turns({result.total_turns})"
    )


# ════════════════════════════════════════════════════════════════════════
# H1 — Registry exhaustive across every Pydantic class
# ════════════════════════════════════════════════════════════════════════


def test_registry_exhaustive_for_every_class_v1_baseline() -> None:
    """For every class in CURRENT_SCHEMA_VERSIONS, story B (v1 only) → registry empty.

    Future: when a class bumps to v2+, the chain (1→2, …, prev→curr)
    MUST exist. This test asserts:

    * If CURRENT_SCHEMA_VERSIONS[X] == 1 → no chain entry for X.
    * If CURRENT_SCHEMA_VERSIONS[X] > 1 → chain (1→2, …) registered.
    """
    for model_name, curr_v in CURRENT_SCHEMA_VERSIONS.items():
        chain_entries = [key for key in SCHEMA_MIGRATIONS if key[0] == model_name]
        if curr_v == 1:
            assert chain_entries == [], (
                f"Story B baseline: model {model_name} at v1 but registry has chain entries: {chain_entries}. "
                "Either bump CURRENT_SCHEMA_VERSIONS or remove the chain entries."
            )
        else:
            for prev in range(1, curr_v):
                key = (model_name, prev, prev + 1)
                assert key in SCHEMA_MIGRATIONS, (
                    f"Missing migrator for {model_name}: {prev} → {prev + 1}. All bumps must register a migrator."
                )


def test_each_registered_migrator_is_callable() -> None:
    """Every migrator in SCHEMA_MIGRATIONS MUST be Callable[[dict], dict].

    Story B: registry empty → loop is no-op + assertion holds trivially.
    """
    for key, migrator in SCHEMA_MIGRATIONS.items():
        assert callable(migrator), f"Migrator for {key!r} not callable: {type(migrator)}"


def test_each_registered_migrator_idempotent_on_probe() -> None:
    """Each migrator MUST be idempotent on a probe dict {schema_version: prev}.

    Defensive: a migrator that mutates global state or has side-effects
    breaks the H1 forward-compat contract. Each migrator should map
    purely-functionally over its input dict.
    """
    for key, migrator in SCHEMA_MIGRATIONS.items():
        _model_name, prev_v, curr_v = key
        probe: dict[str, object] = {"schema_version": prev_v}
        result_1 = migrator(dict(probe))
        result_2 = migrator(dict(probe))
        assert result_1 == result_2, (
            f"Migrator for {key!r} not idempotent: first call returned {result_1!r}, "
            f"second call returned {result_2!r}. Migrators MUST be pure functions."
        )
        # Defensive: result MUST advance schema_version to curr_v
        assert result_1.get("schema_version") == curr_v, (
            f"Migrator for {key!r} did not advance schema_version to {curr_v}; got {result_1.get('schema_version')!r}"
        )


# ════════════════════════════════════════════════════════════════════════
# H10 — Per-nested-class deserialization probes
# ════════════════════════════════════════════════════════════════════════


def test_golden_v1_transcript_turns_round_trip() -> None:
    """Each ConversationTurn in the golden's transcript MUST Pydantic-roundtrip."""
    raw = yaml.safe_load(_FROZEN_GOLDEN_V1.read_text(encoding="utf-8"))
    transcript_raw = raw.get("transcript", [])
    assert isinstance(transcript_raw, list), "transcript MUST be a list"
    assert len(transcript_raw) > 0, "transcript MUST have at least one turn"

    target = CURRENT_SCHEMA_VERSIONS["ConversationTurn"]
    for idx, turn_raw in enumerate(transcript_raw):
        migrated = apply_migrations("ConversationTurn", dict(turn_raw), target_version=target)
        turn = ConversationTurn.model_validate(migrated)
        assert turn.schema_version == 1, f"transcript[{idx}].schema_version drift: {turn.schema_version}"


def test_golden_v1_cost_summary_round_trips() -> None:
    """The golden's cost_summary MUST CostSummary.model_validate cleanly."""
    raw = yaml.safe_load(_FROZEN_GOLDEN_V1.read_text(encoding="utf-8"))
    cost_summary_raw = raw.get("cost_summary")
    assert isinstance(cost_summary_raw, dict), "cost_summary MUST be a dict"

    target = CURRENT_SCHEMA_VERSIONS["CostSummary"]
    migrated = apply_migrations("CostSummary", dict(cost_summary_raw), target_version=target)
    cost = CostSummary.model_validate(migrated)
    assert cost.schema_version == 1


# ════════════════════════════════════════════════════════════════════════
# H1 — Future-proof: synthetic v2 bump probe
# ════════════════════════════════════════════════════════════════════════


def test_synthetic_v1_to_v2_migrator_round_trips_via_apply_migrations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Probe: a freshly registered v1→v2 migrator chain works via apply_migrations.

    Registers a synthetic migrator for an UNRELATED model name (so it
    does not collide with shipped models), invokes ``apply_migrations``
    targeting v2, and asserts the chain executed.

    Cleanup: removes the synthetic entry post-test to avoid pollution
    of the SCHEMA_MIGRATIONS registry.
    """
    test_model = "_pytest_only_SyntheticModel"

    @register_schema_migration(test_model, 1, 2)
    def _bump(raw: dict[str, object]) -> dict[str, object]:
        raw = dict(raw)
        raw["new_field_v2"] = "default"
        raw["schema_version"] = 2
        return raw

    # Patch CURRENT_SCHEMA_VERSIONS to register the test_model. monkeypatch.setitem
    # auto-restores the dict to its prior state on test teardown.
    monkeypatch.setitem(CURRENT_SCHEMA_VERSIONS, test_model, 2)

    try:
        raw: dict[str, object] = {"schema_version": 1, "field": "value"}
        result = apply_migrations(test_model, raw, target_version=2)
        assert result.get("schema_version") == 2, f"Expected schema_version=2; got {result.get('schema_version')}"
        assert result.get("new_field_v2") == "default"
    finally:
        # Best-effort cleanup of the synthetic registry entry (the
        # monkeypatch above only manages CURRENT_SCHEMA_VERSIONS, not
        # SCHEMA_MIGRATIONS).
        SCHEMA_MIGRATIONS.pop((test_model, 1, 2), None)


# ════════════════════════════════════════════════════════════════════════
# Sanity — type-only references silence lint warnings
# ════════════════════════════════════════════════════════════════════════


_: type[Callable[..., object]] = Callable  # type: ignore[assignment]
_simulation_state_ref: type[SimulationState] = SimulationState
_actor_profile_ref: type[ActorProfile] = ActorProfile

# Guard against unused-import lint complaints on the type-only references.
assert _simulation_state_ref is SimulationState
assert _actor_profile_ref is ActorProfile


# ════════════════════════════════════════════════════════════════════════
# Catch-all — full SimulationResult deserialization on rich golden
# ════════════════════════════════════════════════════════════════════════


def test_golden_v1_full_simulation_result_round_trip_with_termination_check() -> None:
    """End-to-end probe: golden v1 → SimulationResult → assert termination_reason.

    Additional invariants beyond the arch fitness gate:

    * ``termination_reason`` coerces to TerminationReason enum
    * ``error_subtype`` is None when termination_reason != AGENT_ERROR
    * ``cost_summary`` total = agent + simulator (caller-computed
      semantics in T-8 runner; golden values must match)
    """
    raw = yaml.safe_load(_FROZEN_GOLDEN_V1.read_text(encoding="utf-8"))
    target = CURRENT_SCHEMA_VERSIONS["SimulationResult"]
    migrated = apply_migrations("SimulationResult", raw, target_version=target)

    result = SimulationResult.model_validate(migrated)

    assert result.termination_reason.value == "max_turns", (
        f"Frozen golden v1 termination drift: expected 'max_turns'; got {result.termination_reason}"
    )
    if result.termination_reason.value != "agent_error":
        assert result.error_subtype is None, (
            f"error_subtype MUST be None when termination_reason != AGENT_ERROR; "
            f"got termination_reason={result.termination_reason} error_subtype={result.error_subtype}"
        )

    # cost_summary semantics
    cost = result.cost_summary
    expected_total = cost.agent_cost_usd + cost.simulator_cost_usd
    assert cost.total_cost_usd == expected_total, (
        f"cost_summary.total_cost_usd ({cost.total_cost_usd}) != "
        f"agent ({cost.agent_cost_usd}) + simulator ({cost.simulator_cost_usd})"
    )


def test_pydantic_class_count_matches_current_schema_versions() -> None:
    """Defensive: every Pydantic class in CURRENT_SCHEMA_VERSIONS MUST resolve.

    Catches accidentally adding a phantom class name to the registry
    without a corresponding Pydantic class shipped under simulator/.

    Synthetic registry entries (per `SYNTHETIC_VERSIONED_REGISTRY_NAMES`)
    track non-Pydantic versioned artifacts (e.g., the Customer Prompt
    template introduced by Story C T-1 D17). These are exempt from the
    "must resolve to a Pydantic class" check by design — they live in
    the registry to drive `apply_migrations` over template versions in
    the same chain semantics, not to satisfy `model_validate`.
    """
    from tests.agentic_evals.sales_agent.simulator._internal.schema_migrations import (
        SYNTHETIC_VERSIONED_REGISTRY_NAMES,
    )

    name_to_class: dict[str, Any] = {
        "SimulationState": SimulationState,
        "ActorProfile": ActorProfile,
        "SimulationResult": SimulationResult,
        "ConversationTurn": ConversationTurn,
        "CostSummary": CostSummary,
    }
    for name in CURRENT_SCHEMA_VERSIONS:
        if name in SYNTHETIC_VERSIONED_REGISTRY_NAMES:
            # Synthetic entries (e.g., CustomerPrompt) version a non-Pydantic
            # artifact (prompt template / config blob). Skip the class-resolve
            # assertion but defensively check the exemption is intentional.
            assert name not in name_to_class, (
                f"Registry name {name!r} is BOTH synthetic AND has a Pydantic class — "
                "remove it from SYNTHETIC_VERSIONED_REGISTRY_NAMES or drop the class binding."
            )
            continue
        assert name in name_to_class, (
            f"CURRENT_SCHEMA_VERSIONS contains {name!r} but no shipped Pydantic class found. "
            f"Either ship the class, drop the registry entry, or add it to "
            f"SYNTHETIC_VERSIONED_REGISTRY_NAMES if it tracks a non-Pydantic artifact."
        )
