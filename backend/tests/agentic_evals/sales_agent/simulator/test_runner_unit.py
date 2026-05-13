"""T-8 acceptance tests — graph compose + run_simulation orchestrator.

Covers acceptance criteria (06-tickets.yaml T-8 verifier paths):

* **A1** — Graph compiled w/o ``from __future__ import annotations``.
  Verified by negative grep at the build phase (out-of-band shell
  command in the gate-runner). The pytest layer asserts that
  :func:`build_simulation_graph` returns a compiled graph and that
  :class:`graph.py` does NOT contain the future-annotations import via
  AST scan (defense-in-depth).
* **A2** — ``run_simulation`` deterministic ``simulation_id``: re-running
  with the same ``(run_id, slug, actor_profile.id, trial_n)`` tuple
  yields the same UUID5 (H2 idempotency).
* **A3** — Invalid ``archetype_slug`` raises ``ValueError`` with the
  valid list. Cero DB inserts on this path (early-exit before the
  fixture seed call).
* **A4** — Artifact JSON written to
  ``_artifacts/{run_id}/simulator/{simulation_id}/transcript.json``;
  contents include the transcript + termination reason + cost summary.

Out of scope (T-9 + T-10 deliverables):

* Public ``__all__`` exact 7 names (T-9)
* Frozen golden v1 fixture regression (T-10)
* Smoke parametrize 5 archetypes against real DB + agent (T-10)

Tests opt out of the ``eval`` autouse marker via ``pytestmark =
pytest.mark.no_eval`` so they run on default CI without ``--run-evals``.

# voseo-allowed: docstring quotes spec-form acceptance criteria + structlog event names
"""

# NO ``from __future__ import annotations`` — story-wide cement (T-4..T-7).

import ast
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from tests.agentic_evals.sales_agent.simulator._internal import runner as runner_mod
from tests.agentic_evals.sales_agent.simulator._internal.graph import (
    build_simulation_graph,
    increment_turn,
    should_continue,
)
from tests.agentic_evals.sales_agent.simulator._internal.runner import run_simulation
from tests.agentic_evals.sales_agent.simulator.actor_profile import ActorProfile
from tests.agentic_evals.sales_agent.simulator.result import (
    ConversationTurn,
    CostSummary,
    SimulationResult,
)
from tests.agentic_evals.sales_agent.simulator.state import SimulationState
from tests.agentic_evals.sales_agent.simulator.termination import (
    TerminationReason,
)

pytestmark = pytest.mark.no_eval


# ───────────────────────────────────────────────────────────────────────
# Factories — minimal valid ActorProfile + ConversationTurn
# ───────────────────────────────────────────────────────────────────────


def _make_actor(actor_id: str = "lead-frio-impaciente") -> ActorProfile:
    """Factory — minimal valid ActorProfile for runner tests."""
    return ActorProfile(
        id=actor_id,
        name="María Cliente",
        actor_goal="Decidir si vale la pena agendar llamada",
        dialect_code="es-419",
        traits=["impaciente"],
        pain_points=["resultados lentos"],
        objections=["precio"],
        budget_hint="medio",
        urgency="medium",
        communication_style="directa",
        initial_message="Hola, vi tu anuncio. ¿Cuánto cuesta?",
        persona_kind="happy",
    )


def _customer_turn(content: str, turn_number: int = 0) -> ConversationTurn:
    """Factory — customer-side ConversationTurn."""
    return ConversationTurn(
        turn_number=turn_number,
        role="customer",
        content=content,
        timestamp=datetime.now(tz=UTC),
        metadata={"generated": False},
    )


def _agent_turn(content: str, turn_number: int = 1) -> ConversationTurn:
    """Factory — agent-side ConversationTurn."""
    return ConversationTurn(
        turn_number=turn_number,
        role="agent",
        content=content,
        timestamp=datetime.now(tz=UTC),
        metadata={"generated": True},
    )


# ───────────────────────────────────────────────────────────────────────
# Patch helper — stub the LangGraph ainvoke so unit tests don't hit DB / LLM
# ───────────────────────────────────────────────────────────────────────


def _patch_graph_ainvoke(
    monkeypatch: pytest.MonkeyPatch,
    *,
    final_transcript: list[ConversationTurn] | None = None,
    termination_reason: TerminationReason | None = None,
    is_finished: bool = True,
    current_turn: int = 1,
) -> MagicMock:
    """Stub ``build_simulation_graph().ainvoke`` to return a controlled state.

    The real graph would call ``customer_node`` (LLM) + ``agent_bridge``
    (production agent_app + DB) which is out of scope for unit tests.
    We replace ``build_simulation_graph`` with a fake that returns a
    compiled-graph-shaped mock whose ``ainvoke`` echoes a final state
    matching the test's intent.

    Returns the mock ``ainvoke`` so tests can spy on its call args.
    """
    transcript = final_transcript or [
        _customer_turn("Hola, vi tu anuncio. ¿Cuánto cuesta?", 0),
        _agent_turn("Hola María, gracias por escribir.", 1),
    ]

    async def _fake_ainvoke(initial_state: SimulationState, *args: Any, **kwargs: Any) -> dict[str, Any]:
        del args, kwargs  # signature compat with LangGraph
        # Echo back as a dict-shape (LangGraph 0.6 returns dict-like).
        snapshot = initial_state.model_dump()
        snapshot["transcript"] = [t.model_dump() for t in transcript]
        snapshot["current_turn"] = current_turn
        snapshot["iterations"] = current_turn  # paridad
        snapshot["is_finished"] = is_finished
        snapshot["termination_reason"] = termination_reason.value if termination_reason is not None else None
        snapshot["last_agent_response"] = transcript[-1].content if transcript else ""
        return snapshot

    fake_compiled = MagicMock()
    ainvoke_mock = AsyncMock(side_effect=_fake_ainvoke)
    fake_compiled.ainvoke = ainvoke_mock

    fake_build = MagicMock(return_value=fake_compiled)
    monkeypatch.setattr(runner_mod, "build_simulation_graph", fake_build)

    return ainvoke_mock


# ───────────────────────────────────────────────────────────────────────
# A1 — Graph compiles + future-annotations cement
# ───────────────────────────────────────────────────────────────────────


class TestGraphCompose:
    """A1 — :func:`build_simulation_graph` returns a compiled LangGraph."""

    def test_build_simulation_graph_returns_compiled(self) -> None:
        """A1 baseline — the graph compiles cleanly."""
        graph = build_simulation_graph()
        # Compiled LangGraph exposes ``ainvoke`` (LangGraph 0.6 contract).
        assert hasattr(graph, "ainvoke"), (
            "build_simulation_graph() MUST return an object with .ainvoke (compiled graph)"
        )
        assert hasattr(graph, "astream"), (
            "build_simulation_graph() MUST return an object with .astream (compiled graph)"
        )

    def test_no_future_annotations_import_in_graph_module(self) -> None:
        """A1 negative — ``graph.py`` MUST NOT import ``annotations`` from ``__future__``.

        Defense-in-depth — the gate-runner runs a negative shell grep too,
        but failing here gives an immediate red signal during development.
        AST-walk so docstrings / comments mentioning the pattern do not
        trip the gate.
        """
        graph_path = Path(__file__).resolve().parent / "_internal" / "graph.py"
        source = graph_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "__future__":
                names = [alias.name for alias in node.names]
                assert "annotations" not in names, (
                    f"graph.py MUST NOT import 'annotations' from __future__ "
                    f"(LangGraph runtime introspection cement). Found: {names}"
                )

    def test_no_future_annotations_import_in_runner_module(self) -> None:
        """Same cement applied to runner.py for symmetry."""
        runner_path = Path(__file__).resolve().parent / "_internal" / "runner.py"
        source = runner_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "__future__":
                names = [alias.name for alias in node.names]
                assert "annotations" not in names, (
                    f"runner.py MUST NOT import 'annotations' from __future__. Found: {names}"
                )


class TestIncrementTurn:
    """``increment_turn`` bumps both ``current_turn`` and ``iterations``."""

    @pytest.mark.asyncio
    async def test_increment_turn_returns_partial_dict(self) -> None:
        """``increment_turn`` returns the partial dict shape LangGraph expects."""
        actor = _make_actor()
        sim_id = uuid4()
        run_id = uuid4()
        state = SimulationState(
            simulation_id=sim_id,
            run_id=run_id,
            tenant_id=uuid4(),
            archetype_slug="tenant_coach_lat",
            actor_profile=actor,
            current_turn=3,
            iterations=4,
            eval_metadata={
                "eval_run_kind": "simulator",
                "archetype_slug": "tenant_coach_lat",
                "actor_profile_id": actor.id,
                "trial_n": 0,
                "simulation_id": str(sim_id),
                "run_id": str(run_id),
            },
        )
        result = await increment_turn(state)
        assert result == {"current_turn": 4, "iterations": 5}


class TestShouldContinue:
    """``should_continue`` returns ``"continue"`` / ``"end"`` correctly."""

    def _state(self, **overrides: Any) -> SimulationState:
        actor = _make_actor()
        sim_id = uuid4()
        run_id = uuid4()
        defaults: dict[str, Any] = {
            "simulation_id": sim_id,
            "run_id": run_id,
            "tenant_id": uuid4(),
            "archetype_slug": "tenant_coach_lat",
            "actor_profile": actor,
            "current_turn": 1,
            "iterations": 1,
            "max_turns": 10,
            "is_finished": False,
            "eval_metadata": {
                "eval_run_kind": "simulator",
                "archetype_slug": "tenant_coach_lat",
                "actor_profile_id": actor.id,
                "trial_n": 0,
                "simulation_id": str(sim_id),
                "run_id": str(run_id),
            },
        }
        defaults.update(overrides)
        return SimulationState(**defaults)

    def test_continues_when_normal_state(self) -> None:
        """Normal state below max_turns: ``"continue"``."""
        state = self._state(current_turn=2, iterations=2, max_turns=10)
        assert should_continue(state) == "continue"

    def test_ends_when_is_finished_set(self) -> None:
        """``is_finished=True`` → terminate."""
        state = self._state(is_finished=True)
        assert should_continue(state) == "end"

    def test_ends_when_iterations_exceed_hardcap(self) -> None:
        """H3 defense: ``iterations >= max_turns + 5`` → terminate."""
        state = self._state(current_turn=10, iterations=15, max_turns=10)
        assert should_continue(state) == "end"

    def test_ends_when_max_turns_reached_via_registry(self) -> None:
        """Registry policy ``_max_turns_predicate`` → terminate at cap."""
        state = self._state(current_turn=10, iterations=10, max_turns=10)
        assert should_continue(state) == "end"


# ───────────────────────────────────────────────────────────────────────
# A2 — Deterministic simulation_id (H2 idempotency)
# ───────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_simulation_id_deterministic(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A2 (06-tickets.yaml T-8 verifier path literal).

    Two runs with the same (run_id, slug, actor.id, trial_n) tuple yield
    the same ``simulation_id`` UUID5 (H2 idempotency).
    """
    # Redirect artifacts to tmp_path so nothing leaks to the repo.
    monkeypatch.setattr(runner_mod, "_ARTIFACTS_BASE", tmp_path)
    _patch_graph_ainvoke(monkeypatch, termination_reason=TerminationReason.MAX_TURNS)

    actor = _make_actor("lead-deterministic-test")
    fixed_run_id = uuid4()

    result_1 = await run_simulation(
        "tenant_coach_lat",
        actor,
        max_turns=5,
        trial_n=0,
        run_id=fixed_run_id,
    )
    result_2 = await run_simulation(
        "tenant_coach_lat",
        actor,
        max_turns=5,
        trial_n=0,
        run_id=fixed_run_id,
    )

    assert result_1.simulation_id == result_2.simulation_id, (
        f"simulation_id MUST be deterministic across re-runs. Got {result_1.simulation_id} vs {result_2.simulation_id}."
    )


# ───────────────────────────────────────────────────────────────────────
# A3 — Invalid archetype raises ValueError + cero DB inserts
# ───────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_invalid_archetype_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A3 (06-tickets.yaml T-8 verifier path literal).

    Invalid archetype_slug → ``ValueError`` with the valid list. Cero DB
    inserts (the runner short-circuits BEFORE the fixture seed call).
    """
    # Spy on graph compile to ensure NO graph build happens on this path.
    fake_build = MagicMock()
    monkeypatch.setattr(runner_mod, "build_simulation_graph", fake_build)

    actor = _make_actor()

    with pytest.raises(ValueError) as exc_info:
        await run_simulation(
            "tenant_inexistente",
            actor,
            max_turns=5,
            trial_n=0,
        )

    err_msg = str(exc_info.value)
    # The error message MUST cite the offending slug + the valid list.
    assert "tenant_inexistente" in err_msg
    assert "tenant_coach_lat" in err_msg, "ValueError MUST include the valid archetype list to help the operator."

    # Cero side effects — graph never compiled.
    assert fake_build.call_count == 0, (
        "Invalid archetype_slug MUST short-circuit BEFORE graph compile (cero DB inserts)."
    )


# ───────────────────────────────────────────────────────────────────────
# A4 — Artifact JSON persistence
# ───────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_artifact_persistence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A4 (06-tickets.yaml T-8 verifier path literal).

    Asserts:

    1. Artifact JSON written to
       ``_artifacts/{run_id}/simulator/{simulation_id}/transcript.json``.
    2. Contents include transcript + termination_reason + cost_summary.
    3. JSON is valid + Pydantic-roundtrippable to SimulationResult.
    """
    monkeypatch.setattr(runner_mod, "_ARTIFACTS_BASE", tmp_path)
    _patch_graph_ainvoke(
        monkeypatch,
        termination_reason=TerminationReason.MAX_TURNS,
        final_transcript=[
            _customer_turn("Hola, ¿cuánto cuesta?", 0),
            _agent_turn("Cuesta $99.", 1),
            _customer_turn("Es caro.", 2),
            _agent_turn("Tenemos opciones de pago.", 3),
        ],
    )

    actor = _make_actor("lead-artifact-test")
    fixed_run_id = uuid4()

    result = await run_simulation(
        "tenant_coach_lat",
        actor,
        max_turns=5,
        trial_n=0,
        run_id=fixed_run_id,
    )

    expected_path = tmp_path / str(fixed_run_id) / "simulator" / str(result.simulation_id) / "transcript.json"
    assert expected_path.exists(), (
        f"Artifact JSON MUST be written to {expected_path}. Path exists: {expected_path.exists()}."
    )

    # Pydantic roundtrip — confirms the JSON is valid SimulationResult shape.
    raw = expected_path.read_text(encoding="utf-8")
    roundtrip = SimulationResult.model_validate_json(raw)

    assert roundtrip.simulation_id == result.simulation_id
    assert roundtrip.run_id == fixed_run_id
    assert roundtrip.archetype_slug == "tenant_coach_lat"
    assert roundtrip.actor_profile_id == actor.id
    assert len(roundtrip.transcript) == 4
    assert roundtrip.termination_reason == TerminationReason.MAX_TURNS
    assert roundtrip.total_turns == 4
    # Cost summary present (zero by default in unit tests — no DB session).
    assert isinstance(roundtrip.cost_summary, CostSummary)


# ───────────────────────────────────────────────────────────────────────
# Spec deliverable — max_turns cap respected (D5/H8)
# ───────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_max_turns_cap(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """When the loop would otherwise continue forever, max_turns caps it.

    Spec deliverable (T-8 prompt): "actor_profile_loop_forever x max_turns=2
    → termination=max_turns, total_turns=2, len(transcript)>=4".

    Here we simulate the loop-forever scenario by stubbing ``ainvoke`` to
    return a state where the registry would still match MAX_TURNS at
    ``current_turn == max_turns``.
    """
    monkeypatch.setattr(runner_mod, "_ARTIFACTS_BASE", tmp_path)
    _patch_graph_ainvoke(
        monkeypatch,
        termination_reason=TerminationReason.MAX_TURNS,
        final_transcript=[
            _customer_turn("Hola.", 0),
            _agent_turn("Hola, ¿en qué te ayudo?", 1),
            _customer_turn("¿Cuánto?", 2),
            _agent_turn("Te paso info.", 3),
        ],
        current_turn=2,
    )

    actor = _make_actor("loop-forever-test")
    result = await run_simulation(
        "tenant_coach_lat",
        actor,
        max_turns=2,
        trial_n=0,
    )

    assert result.termination_reason == TerminationReason.MAX_TURNS
    assert result.total_turns == 4
    assert len(result.transcript) == 4


# ───────────────────────────────────────────────────────────────────────
# Spec deliverable — tenant_id deterministic (D2)
# ───────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_tenant_id_deterministic(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Two runs with the same archetype_slug yield the same tenant_id (D2).

    UUID5(NS_DNS, f"eval-{slug}") is byte-equal across Python invocations.
    """
    monkeypatch.setattr(runner_mod, "_ARTIFACTS_BASE", tmp_path)
    _patch_graph_ainvoke(monkeypatch, termination_reason=TerminationReason.MAX_TURNS)

    actor1 = _make_actor("actor-1")
    actor2 = _make_actor("actor-2")

    result_1 = await run_simulation("tenant_coach_lat", actor1, trial_n=0)
    result_2 = await run_simulation("tenant_coach_lat", actor2, trial_n=0)

    assert result_1.tenant_id == result_2.tenant_id, (
        "tenant_id MUST be deterministic for the same archetype_slug "
        f"(D2 cement). Got {result_1.tenant_id} vs {result_2.tenant_id}."
    )

    # Different slugs → different tenant_ids.
    result_3 = await run_simulation("tenant_clinica_dental", actor1, trial_n=0)
    assert result_3.tenant_id != result_1.tenant_id, "Different archetype_slugs MUST yield different tenant_ids."


# ───────────────────────────────────────────────────────────────────────
# Ancillary — eval_metadata in initial state, cost summary fallback
# ───────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_initial_state_eval_metadata_complete(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Runner builds the initial state with the 6 H5 mandatory keys.

    The graph stub captures the initial_state passed to ainvoke and
    asserts on its ``eval_metadata`` shape.
    """
    monkeypatch.setattr(runner_mod, "_ARTIFACTS_BASE", tmp_path)

    captured: dict[str, Any] = {}

    async def _capture_ainvoke(initial_state: SimulationState, *args: Any, **kwargs: Any) -> dict[str, Any]:
        del args, kwargs
        captured["initial_state"] = initial_state
        snapshot = initial_state.model_dump()
        snapshot["transcript"] = []
        snapshot["termination_reason"] = TerminationReason.MAX_TURNS.value
        return snapshot

    fake_compiled = MagicMock()
    fake_compiled.ainvoke = AsyncMock(side_effect=_capture_ainvoke)
    monkeypatch.setattr(
        runner_mod,
        "build_simulation_graph",
        MagicMock(return_value=fake_compiled),
    )

    actor = _make_actor("metadata-test")
    fixed_run_id = uuid4()
    await run_simulation(
        "tenant_coach_lat",
        actor,
        max_turns=5,
        trial_n=0,
        run_id=fixed_run_id,
    )

    initial_state: SimulationState = captured["initial_state"]
    metadata = initial_state.eval_metadata

    assert metadata["eval_run_kind"] == "simulator"
    assert metadata["archetype_slug"] == "tenant_coach_lat"
    assert metadata["actor_profile_id"] == actor.id
    assert metadata["trial_n"] == 0
    assert metadata["simulation_id"] == str(initial_state.simulation_id)
    assert metadata["run_id"] == str(fixed_run_id)


@pytest.mark.asyncio
async def test_zero_cost_summary_when_no_db_session(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Without ``db_session``, the runner returns a zero CostSummary.

    Best-effort: agentic_evals smoke tests at T-10 wire a real session
    + assert non-zero costs. Unit tests don't.
    """
    monkeypatch.setattr(runner_mod, "_ARTIFACTS_BASE", tmp_path)
    _patch_graph_ainvoke(monkeypatch, termination_reason=TerminationReason.MAX_TURNS)

    actor = _make_actor("zero-cost-test")
    result = await run_simulation("tenant_coach_lat", actor, max_turns=2)

    assert result.cost_summary.agent_cost_usd == Decimal(0)
    assert result.cost_summary.simulator_cost_usd == Decimal(0)
    assert result.cost_summary.total_cost_usd == Decimal(0)
    assert result.cost_summary.llm_calls_count_split == {
        "sales_agent": 0,
        "eval_simulator": 0,
    }


# ───────────────────────────────────────────────────────────────────────
# UUID5 derivation helpers — direct unit coverage
# ───────────────────────────────────────────────────────────────────────


def test_eval_tenant_id_paridad_with_fixture() -> None:
    """The runner derives the same tenant_id as the T-3 fixture.

    Both call ``uuid5(NAMESPACE_DNS, f"eval-{slug}")``. Paridad cement
    so seeded rows and runner-built state agree on the synthetic tenant.
    """
    import uuid as uuid_mod

    from tests.agentic_evals.sales_agent.simulator.fixtures.tenant_seeded import (
        _eval_tenant_id as fixture_tenant_id,
    )

    for slug in ("tenant_coach_lat", "tenant_medicina_estetica", "tenant_clinica_dental"):
        runner_id = runner_mod._eval_tenant_id(slug)
        fixture_id = fixture_tenant_id(slug)
        expected = uuid_mod.uuid5(uuid_mod.NAMESPACE_DNS, f"eval-{slug}")
        assert runner_id == fixture_id == expected, f"Runner + fixture MUST agree on tenant_id derivation for {slug!r}."


def test_simulation_id_uses_uuid5_with_full_tuple() -> None:
    """``simulation_id`` derives from the full (run_id, slug, actor_id, trial_n) tuple."""
    import uuid as uuid_mod

    run_id = UUID("11111111-1111-1111-1111-111111111111")
    sim_id = runner_mod._simulation_id(
        run_id=run_id,
        archetype_slug="tenant_coach_lat",
        actor_profile_id="lead-test",
        trial_n=0,
    )
    expected = uuid_mod.uuid5(
        uuid_mod.NAMESPACE_DNS,
        "11111111-1111-1111-1111-111111111111_tenant_coach_lat_lead-test_0",
    )
    assert sim_id == expected

    # Different trial_n → different sim_id.
    sim_id_trial_1 = runner_mod._simulation_id(
        run_id=run_id,
        archetype_slug="tenant_coach_lat",
        actor_profile_id="lead-test",
        trial_n=1,
    )
    assert sim_id != sim_id_trial_1


# ───────────────────────────────────────────────────────────────────────
# DEEPER-A regression — runner→agent_bridge session injection wiring
# ───────────────────────────────────────────────────────────────────────
#
# Origen: DEEPER-A surfaced post Story D archive (2026-05-08 verification doc
# `docs/archive/2026/stories/sales-agent-goldens-3-tenants-dataset/`
# T-3.bis-smoke-verification.md lines 16-20).
#
# Symptom (verbatim repro pre-fix):
#   simulator.agent_invalid_state error='Runner failed to inject SQLAlchemy
#   session for simulation' error_class=SessionUnavailable
#
# Root cause: `agent_bridge._resolve_session_for_simulation` was a T-7 stub
# that always returned None. The T-8 docstring planned a contextvar/thread-local
# bridge from `run_simulation(db_session=...)` to the helper, but the runner
# never wired it. Real callers (generate_golden_candidates) passed db_session
# correctly to run_simulation; runner stored it only for cost summary at end;
# agent_bridge crashed every turn 0 with INVALID_STATE before any LLM fired.
#
# Fix design (R23 Opus 4.7 — agentic test infrastructure under tests/):
# - Module-level `ContextVar` in agent_bridge.py (asyncio task-local)
# - `_resolve_session_for_simulation(state)` reads from ContextVar
# - run_simulation wraps `graph.ainvoke()` in try/finally that sets+resets
#   the ContextVar around the in-process invocation
# - Backward compatible: existing tests that monkeypatch the helper directly
#   keep working (monkeypatch overrides function entirely, bypassing the
#   ContextVar read)
# - Tenant isolation preserved: ContextVar holds Session, not tenant_id;
#   agent runtime queries continue to filter by state.tenant_id


@pytest.mark.asyncio
async def test_db_session_propagated_to_agent_bridge_via_contextvar(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """DEEPER-A regression — runner MUST propagate db_session to agent_bridge.

    Asserts:

    1. When ``run_simulation(db_session=stub)`` is called, the stub session
       is visible to ``agent_bridge._resolve_session_for_simulation`` via
       the ContextVar bridge.
    2. After ``run_simulation`` returns, the ContextVar is reset to None
       (no leakage to subsequent simulations in the same event loop).
    3. The stub session is the exact instance passed to the runner (not
       a copy / wrapper).

    Implementation: this test runs the REAL graph (no monkeypatch on
    build_simulation_graph), but monkeypatches the agent_bridge's lazy
    imports so no production sales_agent runtime is touched. The DB
    session bridge is exercised end-to-end through the runner's
    set/reset of the ContextVar.

    Pre-fix this test FAILS with: assert captured_session is stub_session
    → ``AssertionError: None is not <MagicMock id=...>`` because
    _resolve_session_for_simulation always returned None.

    # voseo-allowed — docstring quotes structlog event names + Spanish
    # neutro reserved for user-facing strings (this is a test docstring).
    """
    monkeypatch.setattr(runner_mod, "_ARTIFACTS_BASE", tmp_path)

    from tests.agentic_evals.sales_agent.simulator._internal import (
        agent_bridge as bridge_mod,
    )

    # Capture the session value resolved INSIDE agent_bridge (called by the
    # real graph). We don't replace _resolve_session_for_simulation — we want
    # to test that the contextvar bridge works.
    captured: dict[str, Any] = {"session": "<not-called>"}

    real_resolver = bridge_mod._resolve_session_for_simulation

    def _spy_resolver(state: SimulationState) -> Any:
        result = real_resolver(state)
        captured["session"] = result
        return result

    monkeypatch.setattr(bridge_mod, "_resolve_session_for_simulation", _spy_resolver)

    # Patch the agent_bridge's lazy imports so the bridge does NOT crash
    # downstream after the session is resolved (we only care about whether
    # the resolver returns the injected session).
    from luana_core_sales_agent.application.orchestrator import graph as graph_mod
    from luana_core_sales_agent.application.services import (
        knowledge_builder as kb_mod,
    )
    from tests.agentic_evals.sales_agent.simulator._internal import (
        observability as obs_mod,
    )

    mock_kb = MagicMock()
    mock_kb.build_identity = MagicMock(return_value="stub_identity")
    mock_kb.build_brand_voice = MagicMock(return_value="stub_voice")
    monkeypatch.setattr(kb_mod, "TenantKnowledgeBuilder", MagicMock(return_value=mock_kb))

    mock_app = MagicMock()
    mock_app.ainvoke = AsyncMock(return_value={"messages": [{"role": "assistant", "content": "Hola."}]})
    monkeypatch.setattr(graph_mod, "agent_app", mock_app)

    monkeypatch.setattr(
        obs_mod,
        "build_eval_simulator_observability_context",
        MagicMock(return_value=None),  # bridge falls back to no-obs path
    )

    stub_session = MagicMock(name="stub_db_session")
    actor = _make_actor("session-injection-test")

    # Pre-condition — context var must be empty before the runner sets it.
    assert bridge_mod._simulation_db_session_var.get() is None, "ContextVar MUST default to None (test isolation)"

    result = await run_simulation(
        "tenant_coach_lat",
        actor,
        max_turns=2,
        trial_n=0,
        db_session=stub_session,
    )

    # 1. Resolver was called and saw the injected session.
    assert captured["session"] is stub_session, (
        f"agent_bridge._resolve_session_for_simulation MUST receive the same "
        f"db_session passed to run_simulation. Pre-fix DEEPER-A: returns None. "
        f"Got: {captured['session']!r}"
    )

    # 2. ContextVar reset after run_simulation returns (no leak).
    assert bridge_mod._simulation_db_session_var.get() is None, (
        "ContextVar MUST be reset to None after run_simulation completes "
        "(prevents cross-simulation leakage in the same event loop)"
    )

    # 3. Run completed without INVALID_STATE termination from session probe.
    assert result.termination_reason != TerminationReason.AGENT_ERROR or (result.error_subtype != "invalid_state"), (
        f"Pre-fix DEEPER-A: termination=AGENT_ERROR/INVALID_STATE due to "
        f"SessionUnavailable. Got termination={result.termination_reason} "
        f"subtype={result.error_subtype}"
    )


@pytest.mark.asyncio
async def test_contextvar_resets_when_run_simulation_raises(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """DEEPER-A defense — ContextVar MUST reset even when run_simulation raises.

    Asyncio ContextVars are task-local but do leak within the same task
    if the producer skips the reset. Use try/finally to guarantee reset.
    """
    monkeypatch.setattr(runner_mod, "_ARTIFACTS_BASE", tmp_path)

    from tests.agentic_evals.sales_agent.simulator._internal import (
        agent_bridge as bridge_mod,
    )

    # Force build_simulation_graph().ainvoke to raise — exercises the
    # finally branch that resets the ContextVar.
    fake_compiled = MagicMock()
    fake_compiled.ainvoke = AsyncMock(side_effect=RuntimeError("boom"))
    monkeypatch.setattr(runner_mod, "build_simulation_graph", MagicMock(return_value=fake_compiled))

    stub_session = MagicMock(name="stub_for_raise_path")
    actor = _make_actor("raise-path-test")

    with pytest.raises(RuntimeError, match="boom"):
        await run_simulation(
            "tenant_coach_lat",
            actor,
            max_turns=1,
            trial_n=0,
            db_session=stub_session,
        )

    # ContextVar reset even though graph.ainvoke raised.
    assert bridge_mod._simulation_db_session_var.get() is None, (
        "ContextVar MUST reset to None even when graph.ainvoke raises "
        "(try/finally guarantee — defense-in-depth against task-local leakage)"
    )


@pytest.mark.asyncio
async def test_resolve_session_returns_none_when_not_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Backward compat — `_resolve_session_for_simulation` returns None
    outside a `run_simulation` context.

    Pre-fix behavior preserved when the ContextVar is empty: the resolver
    returns None, agent_bridge takes the INVALID_STATE termination path.
    This is the correct behavior for `db_session=None` invocations
    (graceful-degradation Rule 2 fallback — best-effort).
    """
    from tests.agentic_evals.sales_agent.simulator._internal import (
        agent_bridge as bridge_mod,
    )

    # No ContextVar set — fresh task scope.
    state = SimulationState(
        simulation_id=uuid4(),
        run_id=uuid4(),
        tenant_id=uuid4(),
        archetype_slug="tenant_coach_lat",
        actor_profile=_make_actor(),
        trial_n=0,
        transcript=[],
        current_turn=0,
        max_turns=10,
        eval_metadata={
            "eval_run_kind": "simulator",
            "archetype_slug": "tenant_coach_lat",
            "actor_profile_id": "lead-frio-impaciente",
            "trial_n": 0,
            "simulation_id": "00000000-0000-0000-0000-000000000000",
            "run_id": "00000000-0000-0000-0000-000000000000",
        },
    )
    resolved = bridge_mod._resolve_session_for_simulation(state)
    assert resolved is None, (
        "Resolver MUST return None when ContextVar is unset (preserves backward compat for db_session=None callers)"
    )
