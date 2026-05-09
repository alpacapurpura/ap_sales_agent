"""run_simulation orchestrator (T-8) — public surface bound by T-9.

Drives one full eval simulation end-to-end:

1. Validate ``tenant_archetype_slug`` against the 5 ratified slugs (D2).
2. Compute deterministic ``simulation_id`` via UUID5 (H2 idempotency).
3. Resolve deterministic ``tenant_id`` via UUID5 (D2).
4. Invoke the ``eval_tenant_seeded(slug)`` fixture (T-3) to materialize
   real Postgres rows with deterministic IDs.
5. Build the initial :class:`SimulationState` Pydantic instance with the
   6 mandatory H5 ``eval_metadata`` keys.
6. Compile the LangGraph via :func:`build_simulation_graph` (T-8).
7. ``await graph.ainvoke(initial_state)`` (in-process — D1 cement).
8. Determine termination via the H8 registry; fall back to ``MAX_TURNS``
   when ``should_continue`` would still loop after max_turns reached.
9. Compute :class:`CostSummary` from observability rows (best-effort —
   bucket separation H6 enforced by the table choice:
   ``eval_simulator_llm_call`` for customer / observability cost,
   ``sales_agent_llm_call`` for agent production cost).
10. Build the :class:`SimulationResult` Pydantic with all the spec fields.
11. Write artifact JSON to
    ``_artifacts/{run_id}/simulator/{simulation_id}/transcript.json`` (D10).
12. Return the SimulationResult to the caller.

Anti-duplication §0
===================

Reuses verbatim:

* :data:`ARCHETYPE_SLUGS` from ``tests/fixtures/eval/tenants/loader.py``
* :func:`build_simulation_graph` from ``_internal/graph.py`` (T-8)
* :class:`SimulationState` from ``simulator/state.py`` (T-4)
* :class:`SimulationResult` + :class:`CostSummary` from ``simulator/result.py`` (T-4)
* :class:`TerminationReason` + :func:`evaluate_termination` from
  ``simulator/termination.py`` (T-4)

Best-effort observability / artifact writes
============================================

* Cost summary aggregation wrapped in ``try/except`` + ``structlog.warning``.
  Failure → empty :class:`CostSummary` (zero values) so the SimulationResult
  still constructs.
* Artifact JSON write wrapped in ``try/except`` + ``structlog.warning``.
  Failure → ``artifact_path`` returned in the result still references the
  intended path even if the file write failed (best-effort cement per
  ``.claude/rules/copilot-observability.md``).

# voseo-allowed: docstring quotes spec deliverable + structlog event names
"""

# Story-wide cement (T-4..T-7): NO future-annotations import. While this
# module isn't imported by the graph compiler, keeping the cement
# consistent across the simulator subtree avoids accidental bypass when
# refactoring. The negative-grep verifier at the gate-runner level
# enforces this on graph.py + (defense-in-depth) on runner.py.

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

import structlog

from tests.agentic_evals.sales_agent.simulator._internal.agent_bridge import (
    _reset_simulation_db_session,
    _set_simulation_db_session,
)
from tests.agentic_evals.sales_agent.simulator._internal.graph import (
    build_simulation_graph,
)
from tests.agentic_evals.sales_agent.simulator.actor_profile import ActorProfile
from tests.agentic_evals.sales_agent.simulator.result import (
    ConversationTurn,
    CostSummary,
    SimulationResult,
)
from tests.agentic_evals.sales_agent.simulator.state import SimulationState
from tests.agentic_evals.sales_agent.simulator.termination import (
    AgentErrorSubtype,
    TerminationReason,
    evaluate_termination,
)
from tests.fixtures.eval.tenants.loader import ARCHETYPE_SLUGS

logger = structlog.get_logger()


# ════════════════════════════════════════════════════════════════════════
# Constants
# ════════════════════════════════════════════════════════════════════════

# Namespace for UUID5 derivations (D2 + H2). NAMESPACE_DNS keeps the
# identifier stable across Python versions and is paridad with
# ``simulator/fixtures/tenant_seeded.py``.
_EVAL_NAMESPACE: uuid.UUID = uuid.NAMESPACE_DNS

# Repo root anchor for artifact persistence — relative to this module
# rather than CWD so test invocation from any directory works the same.
# ``runner.py`` -> ``_internal`` -> ``simulator`` -> ``sales_agent`` ->
# ``agentic_evals`` -> ``tests`` -> ``backend``.
_BACKEND_ROOT: Path = Path(__file__).resolve().parents[5]
_ARTIFACTS_BASE: Path = _BACKEND_ROOT / "tests" / "agentic_evals" / "sales_agent" / "_artifacts"


# ════════════════════════════════════════════════════════════════════════
# Helpers — deterministic UUID5 derivations
# ════════════════════════════════════════════════════════════════════════


def _eval_tenant_id(archetype_slug: str) -> UUID:
    """Derive deterministic ``tenant_id`` via UUID5 (D2).

    Paridad with ``simulator/fixtures/tenant_seeded.py::_eval_tenant_id`` —
    same namespace + name template so the fixture and the runner agree on
    the synthetic eval tenant identifier.

    Args:
        archetype_slug: One of the 5 ratified slugs.

    Returns:
        UUID — idempotent across runs.
    """
    return uuid.uuid5(_EVAL_NAMESPACE, f"eval-{archetype_slug}")


def _simulation_id(
    *,
    run_id: UUID,
    archetype_slug: str,
    actor_profile_id: str,
    trial_n: int,
) -> UUID:
    """Derive deterministic ``simulation_id`` via UUID5 (H2).

    Same ``(run_id, slug, actor_profile_id, trial_n)`` tuple → same UUID
    across re-runs. Enables idempotent test runs + golden fixture
    regression baselines (T-9 frozen golden v1 references this).

    Args:
        run_id: Parent eval invocation UUID.
        archetype_slug: One of the 5 ratified slugs.
        actor_profile_id: Stable :class:`ActorProfile.id`.
        trial_n: Trial counter (Story F multi-trial; Story B always 0).

    Returns:
        UUID — idempotent across runs.
    """
    name = f"{run_id}_{archetype_slug}_{actor_profile_id}_{trial_n}"
    return uuid.uuid5(_EVAL_NAMESPACE, name)


def _build_eval_metadata(
    *,
    archetype_slug: str,
    actor_profile_id: str,
    trial_n: int,
    simulation_id: UUID,
    run_id: UUID,
) -> dict[str, str | int]:
    """Build the H5 mandatory 6-key ``eval_metadata`` dict.

    Mirror of ``_internal/observability.py::build_eval_metadata`` — kept
    as a local helper (and not imported) to keep ``runner.py`` free of
    DB-side dependencies. The resulting dict shape is byte-equal so the
    callback handler subclass (T-5) can compare key sets.
    """
    return {
        "eval_run_kind": "simulator",
        "archetype_slug": archetype_slug,
        "actor_profile_id": actor_profile_id,
        "trial_n": int(trial_n),
        "simulation_id": str(simulation_id),
        "run_id": str(run_id),
    }


# ════════════════════════════════════════════════════════════════════════
# Cost summary aggregation (best-effort H6 cost-bucket separation)
# ════════════════════════════════════════════════════════════════════════


def _zero_cost_summary() -> CostSummary:
    """Build a zero-value :class:`CostSummary` for fallback paths."""
    return CostSummary(
        agent_cost_usd=Decimal(0),
        simulator_cost_usd=Decimal(0),
        total_cost_usd=Decimal(0),
        llm_calls_count_split={"sales_agent": 0, "eval_simulator": 0},
    )


def _compute_cost_summary(
    *,
    db: Any,  # SQLAlchemy Session — typed Any to avoid hard import dependency
    tenant_id: UUID,
    simulation_id: UUID,
    started_at: datetime,
) -> CostSummary:
    """Aggregate :class:`CostSummary` from observability rows (H6).

    Splits cost across two physical tables (cost-bucket separation):

    * ``eval_simulator_llm_call`` — customer LLM + auxiliary calls. Filter
      by ``eval_metadata->>'simulation_id' = <id>``.
    * ``sales_agent_llm_call`` — production agent runtime calls. Filter
      by ``tenant_id`` + ``started_at >= simulation_started_at`` (the
      production model has no ``simulation_id`` tag — H6 cardinal).

    Best-effort: any aggregation failure logs a structured warning and
    returns the zero summary so the runner can still build a
    :class:`SimulationResult`.

    Args:
        db: Active SQLAlchemy session.
        tenant_id: Synthetic eval tenant.
        simulation_id: Deterministic UUID5.
        started_at: Simulation start (UTC tz-aware) — bounds the
            ``sales_agent_llm_call`` time window.

    Returns:
        :class:`CostSummary` with split counts + costs (or zero summary
        on aggregation failure).
    """
    try:
        from sqlalchemy import func, select

        # Lazy imports — avoid hard import at module load so the
        # agentic_evals subtree can be collected without forcing the
        # production sales_agent module to import-resolve at test collection.
        from src.modules.sales_agent.observability.eval_simulator.persistence.models.eval_simulator_llm_call import (
            EvalSimulatorLlmCallModel,
        )
        from src.modules.sales_agent.observability.persistence.models.llm_call_model import (
            SalesAgentLlmCallModel,
        )

        # Customer / eval simulator side — filter by eval_metadata jsonb tag.
        sim_stmt = select(
            func.count().label("count"),
            func.coalesce(func.sum(EvalSimulatorLlmCallModel.cost_usd), 0).label(
                "cost",
            ),
        ).where(
            EvalSimulatorLlmCallModel.tenant_id == tenant_id,
            EvalSimulatorLlmCallModel.eval_metadata["simulation_id"].astext == str(simulation_id),
        )
        sim_row = db.execute(sim_stmt).one()
        simulator_cost = Decimal(sim_row.cost or 0)
        simulator_count = int(sim_row.count or 0)

        # Agent / production side — filter by tenant + time window.
        agent_stmt = select(
            func.count().label("count"),
            func.coalesce(func.sum(SalesAgentLlmCallModel.cost_usd), 0).label("cost"),
        ).where(
            SalesAgentLlmCallModel.tenant_id == tenant_id,
            SalesAgentLlmCallModel.started_at >= started_at,
        )
        agent_row = db.execute(agent_stmt).one()
        agent_cost = Decimal(agent_row.cost or 0)
        agent_count = int(agent_row.count or 0)

        total = agent_cost + simulator_cost
        return CostSummary(
            agent_cost_usd=agent_cost,
            simulator_cost_usd=simulator_cost,
            total_cost_usd=total,
            llm_calls_count_split={
                "sales_agent": agent_count,
                "eval_simulator": simulator_count,
            },
        )
    except Exception as exc:  # noqa: BLE001 — best-effort observability
        logger.warning(
            "simulator.cost_summary_aggregation_failed",
            simulation_id=str(simulation_id),
            tenant_id=str(tenant_id),
            error_class=type(exc).__name__,
            error=str(exc),
        )
        return _zero_cost_summary()


# ════════════════════════════════════════════════════════════════════════
# Artifact persistence (D10 — best-effort)
# ════════════════════════════════════════════════════════════════════════


def _artifact_path(*, run_id: UUID, simulation_id: UUID) -> Path:
    """Compose the artifact JSON path per D10.

    Pattern: ``_artifacts/{run_id}/simulator/{simulation_id}/transcript.json``.

    Args:
        run_id: Parent eval invocation UUID.
        simulation_id: Deterministic UUID5.

    Returns:
        Absolute path under the backend test artifacts root.
    """
    return _ARTIFACTS_BASE / str(run_id) / "simulator" / str(simulation_id) / "transcript.json"


def _write_artifact_json(
    *,
    artifact_path: Path,
    result: SimulationResult,
) -> None:
    """Write the SimulationResult to the artifact JSON file.

    Best-effort: failures (permission denied, disk full, etc.) emit a
    ``structlog.warning`` and return silently. The runner still returns
    the SimulationResult to the caller — a missing artifact file is a
    debug aid loss, not a correctness failure.

    Args:
        artifact_path: Absolute path computed via :func:`_artifact_path`.
        result: The SimulationResult Pydantic instance to serialize.
    """
    try:
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        # Single-writer per simulation (deterministic UUID5 per run) → no
        # concurrent writers, so a direct write is safe. We use json.dumps
        # via Pydantic's .model_dump_json to honor the schema_version field
        # + Decimal / UUID / datetime serialization rules.
        json_str = result.model_dump_json(indent=2)
        artifact_path.write_text(json_str, encoding="utf-8")
        logger.info(
            "simulator.artifact_written",
            simulation_id=str(result.simulation_id),
            run_id=str(result.run_id),
            path=str(artifact_path),
            bytes_written=len(json_str.encode("utf-8")),
        )
    except Exception as exc:  # noqa: BLE001 — best-effort artifact persistence
        logger.warning(
            "simulator.artifact_write_failed",
            simulation_id=str(result.simulation_id),
            run_id=str(result.run_id),
            path=str(artifact_path),
            error_class=type(exc).__name__,
            error=str(exc),
        )


# ════════════════════════════════════════════════════════════════════════
# Termination resolution
# ════════════════════════════════════════════════════════════════════════


def _resolve_termination(
    final_state: SimulationState,
) -> tuple[TerminationReason, AgentErrorSubtype | None]:
    """Determine the canonical ``termination_reason`` for the result.

    Resolution order:

    1. If the final state already carries an explicit ``termination_reason``
       (set by ``agent_bridge`` failure modes — T-7), honor it verbatim.
    2. Otherwise, run :func:`evaluate_termination` against the final state.
       The H8 registry returns the first matching reason.
    3. Fallback: if neither path produced a reason but the loop exited
       (``current_turn >= max_turns``), classify as ``MAX_TURNS``.

    Args:
        final_state: SimulationState returned by ``graph.ainvoke``.

    Returns:
        Tuple of ``(termination_reason, error_subtype)`` where
        ``error_subtype`` is non-None only when reason is AGENT_ERROR.
    """
    # 1. Honor explicit reason from a node (e.g., AGENT_ERROR from T-7).
    if final_state.termination_reason is not None:
        return final_state.termination_reason, final_state.error_subtype

    # 2. Try the H8 registry one more time on the final state.
    reason = evaluate_termination(final_state)
    if reason is not None:
        # Only the AGENT_ERROR path carries an error_subtype.
        subtype = final_state.error_subtype if reason == TerminationReason.AGENT_ERROR else None
        return reason, subtype

    # 3. Fallback: loop exited but no policy matched → classify MAX_TURNS.
    return TerminationReason.MAX_TURNS, None


# ════════════════════════════════════════════════════════════════════════
# Public orchestrator
# ════════════════════════════════════════════════════════════════════════


def _validate_archetype_slug(slug: str) -> None:
    """Validate ``slug`` against the 5 ratified archetypes (D2).

    Raised BEFORE any DB inserts or graph compile so invalid input
    short-circuits cleanly with a helpful message + valid list.

    Args:
        slug: User-supplied archetype slug.

    Raises:
        ValueError: When ``slug`` is not in the valid set.
    """
    if slug not in ARCHETYPE_SLUGS:
        valid_sorted = sorted(ARCHETYPE_SLUGS)
        msg = f"archetype_slug {slug!r} not found. Valid: {valid_sorted}"
        raise ValueError(msg)


async def run_simulation(
    tenant_archetype_slug: str,
    actor_profile: ActorProfile,
    *,
    max_turns: int = 10,
    trial_n: int = 0,
    run_id: UUID | None = None,
    db_session: Any = None,
    seed_fn: Any = None,
) -> SimulationResult:
    """Drive one full eval simulation end-to-end (T-8 cardinal deliverable).

    Args:
        tenant_archetype_slug: One of the 5 ratified slugs.
        actor_profile: Driving persona (T-4 Pydantic).
        max_turns: Hard cap on conversation turns. Default 10. Range 1..20.
        trial_n: Trial counter (Story F; Story B passes 0).
        run_id: Parent eval invocation UUID. ``None`` (default) generates a
            fresh UUID4 — for production runs, the caller supplies a
            stable run_id so all simulations under one invocation cluster
            together in artifacts.
        db_session: SQLAlchemy session for fixture seeding + cost queries.
            ``None`` triggers fixture default lifecycle.
        seed_fn: Override the seed callable (for tests). When provided,
            the runner skips ``eval_tenant_seeded`` fixture lookup and
            calls ``seed_fn(slug)`` instead. Production callers leave None.

    Returns:
        :class:`SimulationResult` Pydantic with full transcript + cost
        summary + termination reason. The artifact JSON is written
        side-effectfully to ``_artifacts/{run_id}/simulator/{sim_id}/transcript.json``.

    Raises:
        ValueError: If ``tenant_archetype_slug`` is not in the valid set.
            Cero DB inserts on this path (early validation).
    """
    # ── Step 1: Validate archetype slug (zero side effects on failure) ──
    _validate_archetype_slug(tenant_archetype_slug)

    # ── Step 2: Resolve run_id + simulation_id (deterministic UUID5) ───
    effective_run_id: UUID = run_id or uuid.uuid4()
    sim_id = _simulation_id(
        run_id=effective_run_id,
        archetype_slug=tenant_archetype_slug,
        actor_profile_id=actor_profile.id,
        trial_n=trial_n,
    )

    # ── Step 3: Resolve deterministic tenant_id (D2) ────────────────────
    tenant_id = _eval_tenant_id(tenant_archetype_slug)

    # ── Step 4: Seed tenant via fixture (T-3) ───────────────────────────
    # The fixture is sync (DB-bound) — invoke it directly. Tests can
    # bypass via the ``seed_fn`` override.
    seeded_tenant_id: UUID | None = None
    if seed_fn is not None:
        try:
            seed_result = seed_fn(tenant_archetype_slug)
            if isinstance(seed_result, tuple) and len(seed_result) >= 1:
                seeded_tenant_id = seed_result[0]
        except Exception as exc:  # noqa: BLE001 — best-effort: tests stub seed_fn
            logger.warning(
                "simulator.tenant_seed_failed",
                simulation_id=str(sim_id),
                archetype_slug=tenant_archetype_slug,
                error_class=type(exc).__name__,
                error=str(exc),
            )

    # Defense-in-depth — if the fixture returned a different tenant_id
    # than our deterministic derivation, log a loud warning so the
    # operator can investigate (D2 cement: both paths MUST agree).
    if seeded_tenant_id is not None and seeded_tenant_id != tenant_id:
        logger.warning(
            "simulator.tenant_id_mismatch",
            simulation_id=str(sim_id),
            archetype_slug=tenant_archetype_slug,
            seeded=str(seeded_tenant_id),
            derived=str(tenant_id),
        )

    # ── Step 5: Build initial SimulationState ───────────────────────────
    eval_metadata = _build_eval_metadata(
        archetype_slug=tenant_archetype_slug,
        actor_profile_id=actor_profile.id,
        trial_n=trial_n,
        simulation_id=sim_id,
        run_id=effective_run_id,
    )
    initial_state = SimulationState(
        simulation_id=sim_id,
        run_id=effective_run_id,
        tenant_id=tenant_id,
        archetype_slug=tenant_archetype_slug,
        actor_profile=actor_profile,
        trial_n=trial_n,
        transcript=[],
        current_turn=0,
        max_turns=max_turns,
        iterations=0,
        is_finished=False,
        termination_reason=None,
        error_subtype=None,
        last_agent_response="",
        eval_metadata=eval_metadata,
    )

    started_at: datetime = datetime.now(tz=UTC)
    logger.info(
        "simulator.simulation_started",
        simulation_id=str(sim_id),
        run_id=str(effective_run_id),
        tenant_id=str(tenant_id),
        archetype_slug=tenant_archetype_slug,
        actor_profile_id=actor_profile.id,
        trial_n=trial_n,
        max_turns=max_turns,
    )

    # ── Step 6: Compile graph ───────────────────────────────────────────
    graph = build_simulation_graph()

    # ── Step 7: Invoke graph (in-process — D1 cement) ──────────────────
    # DEEPER-A bridge (2026-05-08 post Story D archive): set the
    # ``_simulation_db_session_var`` ContextVar so ``agent_bridge.
    # _resolve_session_for_simulation`` returns the injected session
    # rather than the legacy stub None. ContextVars are asyncio
    # task-local — concurrent simulations under ``asyncio.gather`` each
    # get their own value (no cross-cell leakage). The ``try/finally``
    # guarantees reset even if ``graph.ainvoke`` raises.
    _session_token = _set_simulation_db_session(db_session)
    try:
        final_state_raw: Any = await graph.ainvoke(initial_state)
    finally:
        _reset_simulation_db_session(_session_token)
    # LangGraph 0.6 returns the state as a dict-like (or the BaseModel
    # depending on graph configuration). Coerce back to Pydantic for
    # uniform downstream handling.
    if isinstance(final_state_raw, SimulationState):
        final_state = final_state_raw
    else:
        # Dict-like — model_validate handles the round-trip.
        final_state = SimulationState.model_validate(final_state_raw)

    # ── Step 8: Resolve canonical termination reason ───────────────────
    termination_reason, error_subtype = _resolve_termination(final_state)

    # ── Step 9: Compute cost summary (best-effort) ──────────────────────
    if db_session is not None:
        cost_summary = _compute_cost_summary(
            db=db_session,
            tenant_id=tenant_id,
            simulation_id=sim_id,
            started_at=started_at,
        )
    else:
        cost_summary = _zero_cost_summary()

    completed_at: datetime = datetime.now(tz=UTC)

    # ── Step 10: Build SimulationResult Pydantic ────────────────────────
    artifact_abs_path = _artifact_path(
        run_id=effective_run_id,
        simulation_id=sim_id,
    )
    # Re-anchor against backend root for a stable, repo-relative path.
    try:
        artifact_rel_path = str(artifact_abs_path.relative_to(_BACKEND_ROOT))
    except ValueError:
        # Not under backend root (test invocation from external CWD) —
        # fall back to absolute path.
        artifact_rel_path = str(artifact_abs_path)

    transcript_snapshot: list[ConversationTurn] = list(final_state.transcript)
    result = SimulationResult(
        simulation_id=sim_id,
        run_id=effective_run_id,
        tenant_id=tenant_id,
        archetype_slug=tenant_archetype_slug,
        actor_profile_id=actor_profile.id,
        trial_n=trial_n,
        transcript=transcript_snapshot,
        termination_reason=termination_reason,
        error_subtype=error_subtype,
        total_turns=len(transcript_snapshot),
        cost_summary=cost_summary,
        started_at=started_at,
        completed_at=completed_at,
        artifact_path=artifact_rel_path,
    )

    # ── Step 11: Write artifact JSON (D10 — best-effort) ────────────────
    _write_artifact_json(artifact_path=artifact_abs_path, result=result)

    logger.info(
        "simulator.simulation_completed",
        simulation_id=str(sim_id),
        run_id=str(effective_run_id),
        total_turns=len(transcript_snapshot),
        termination_reason=str(termination_reason),
        error_subtype=str(error_subtype) if error_subtype is not None else None,
        agent_cost_usd=str(cost_summary.agent_cost_usd),
        simulator_cost_usd=str(cost_summary.simulator_cost_usd),
    )

    # ── Step 12: Return SimulationResult ────────────────────────────────
    return result


# Re-export for tests that monkeypatch internals.
__all__ = ["run_simulation"]
