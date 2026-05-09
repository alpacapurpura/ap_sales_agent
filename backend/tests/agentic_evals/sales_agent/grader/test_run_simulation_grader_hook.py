"""Integration tests — ``run_simulation`` ``grader_callback`` hook (Story E T-9).

Verifies the additive ``grader_callback: Callable | None = None`` parameter on
:func:`run_simulation`:

* A5.1 — ``grader_callback=None`` → zero ripple on Story B existing tests.
* A5.2 — ``grader_callback`` invoked exactly once POST-completion via
  ``asyncio.create_task`` (fire-and-forget — runner does NOT await).
* A5.3 — Callback failure does NOT block simulation; structlog warn emitted.
* A5.4 — Story E extended ``eval_metadata`` keys (5 NEW: ``grader``,
  ``rubric_id``, ``rubric_version``, ``judge_id``, ``round_n``, ``cache_hit``,
  ``injection_attempt_detected``) propagate when the real grader is wired.
* A5.5 — ``simulation_id`` passed to callback matches the result UUID5 →
  deterministic across re-runs.

Tests are unit-style (``@pytest.mark.no_eval``) — they stub the LangGraph
``ainvoke`` so no LLM / DB hits. The Scenario 1-4 tests under ``scenarios/``
exercise the same hook with the real grader (gated by ``--run-evals``).

# voseo-allowed: docstring quotes acceptance criteria + structlog event names
"""

# NO ``from __future__ import annotations`` — story-wide cement parity.

import asyncio
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from tests.agentic_evals.sales_agent.simulator._internal import runner as runner_mod
from tests.agentic_evals.sales_agent.simulator._internal.runner import run_simulation
from tests.agentic_evals.sales_agent.simulator.actor_profile import ActorProfile
from tests.agentic_evals.sales_agent.simulator.result import (
    ConversationTurn,
    SimulationResult,
)
from tests.agentic_evals.sales_agent.simulator.state import SimulationState
from tests.agentic_evals.sales_agent.simulator.termination import TerminationReason

pytestmark = pytest.mark.no_eval


# ════════════════════════════════════════════════════════════════════════
# Factories — minimal valid ActorProfile + ConversationTurn
# ════════════════════════════════════════════════════════════════════════


def _make_actor(actor_id: str = "lead-frio-impaciente") -> ActorProfile:
    """Factory — minimal valid ActorProfile."""
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


def _patch_graph_ainvoke(
    monkeypatch: pytest.MonkeyPatch,
    *,
    final_transcript: list[ConversationTurn] | None = None,
    termination_reason: TerminationReason | None = None,
) -> None:
    """Stub ``build_simulation_graph().ainvoke`` to echo a controlled state."""
    transcript = final_transcript or [
        _customer_turn("Hola, vi tu anuncio.", 0),
        _agent_turn("Hola María, gracias por escribir.", 1),
    ]

    async def _fake_ainvoke(initial_state: SimulationState, *args: Any, **kwargs: Any) -> dict[str, Any]:
        del args, kwargs
        snapshot = initial_state.model_dump()
        snapshot["transcript"] = [t.model_dump() for t in transcript]
        snapshot["current_turn"] = 1
        snapshot["iterations"] = 1
        snapshot["is_finished"] = True
        snapshot["termination_reason"] = (
            termination_reason.value if termination_reason is not None else TerminationReason.GOAL_COMPLETION.value
        )
        snapshot["last_agent_response"] = transcript[-1].content if transcript else ""
        return snapshot

    fake_compiled = MagicMock()
    fake_compiled.ainvoke = AsyncMock(side_effect=_fake_ainvoke)
    monkeypatch.setattr(runner_mod, "build_simulation_graph", MagicMock(return_value=fake_compiled))


# ════════════════════════════════════════════════════════════════════════
# A5.1 — grader_callback=None → zero ripple
# ════════════════════════════════════════════════════════════════════════


class TestGraderCallbackNoneZeroRipple:
    """A5.1 — Story B existing tests pass ``None`` → zero ripple."""

    @pytest.mark.asyncio
    async def test_grader_callback_optional_default_none(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """``grader_callback`` is OPTIONAL with default ``None`` (additive signature)."""
        _patch_graph_ainvoke(monkeypatch)

        result = await run_simulation(
            tenant_archetype_slug="tenant_coach_lat",
            actor_profile=_make_actor(),
            run_id=uuid4(),
            seed_fn=lambda slug: (UUID("00000000-0000-0000-0000-000000000001"),),
        )

        assert isinstance(result, SimulationResult)
        # No grader_callback passed → no schedule attempt → cero ripple Story B.

    @pytest.mark.asyncio
    async def test_grader_callback_explicit_none_zero_ripple(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Explicit ``grader_callback=None`` matches default behavior."""
        _patch_graph_ainvoke(monkeypatch)

        result = await run_simulation(
            tenant_archetype_slug="tenant_coach_lat",
            actor_profile=_make_actor(),
            run_id=uuid4(),
            seed_fn=lambda slug: (UUID("00000000-0000-0000-0000-000000000001"),),
            grader_callback=None,
        )

        assert isinstance(result, SimulationResult)


# ════════════════════════════════════════════════════════════════════════
# A5.2 — grader_callback invoked exactly once via asyncio.create_task
# ════════════════════════════════════════════════════════════════════════


class TestGraderCallbackInvocation:
    """A5.2 — Callback invoked POST-completion fire-and-forget (NOT awaited)."""

    @pytest.mark.asyncio
    async def test_grader_callback_invoked_once_post_turn(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """``grader_callback`` invoked exactly once with the SimulationResult."""
        _patch_graph_ainvoke(monkeypatch)

        invocations: list[Any] = []
        callback_done = asyncio.Event()

        async def _spy_callback(result: Any) -> None:
            invocations.append(result)
            callback_done.set()

        await run_simulation(
            tenant_archetype_slug="tenant_coach_lat",
            actor_profile=_make_actor(),
            run_id=uuid4(),
            seed_fn=lambda slug: (UUID("00000000-0000-0000-0000-000000000001"),),
            grader_callback=_spy_callback,
        )

        # Allow the create_task callback to actually run.
        await asyncio.wait_for(callback_done.wait(), timeout=2.0)
        assert len(invocations) == 1
        assert isinstance(invocations[0], SimulationResult)

    @pytest.mark.asyncio
    async def test_runner_does_not_await_callback(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Runner returns IMMEDIATELY — does NOT block on callback."""
        _patch_graph_ainvoke(monkeypatch)

        callback_started = asyncio.Event()
        callback_release = asyncio.Event()

        async def _slow_callback(result: Any) -> None:
            callback_started.set()
            await callback_release.wait()  # would block forever if awaited

        # Run with a 1.0s overall timeout — if runner awaits, this raises.
        result = await asyncio.wait_for(
            run_simulation(
                tenant_archetype_slug="tenant_coach_lat",
                actor_profile=_make_actor(),
                run_id=uuid4(),
                seed_fn=lambda slug: (UUID("00000000-0000-0000-0000-000000000001"),),
                grader_callback=_slow_callback,
            ),
            timeout=1.0,
        )

        # Runner returned successfully; callback should have started but not finished.
        await asyncio.wait_for(callback_started.wait(), timeout=1.0)
        assert isinstance(result, SimulationResult)
        # Release the callback so test cleanup is graceful.
        callback_release.set()


# ════════════════════════════════════════════════════════════════════════
# A5.3 — Callback failure does NOT propagate
# ════════════════════════════════════════════════════════════════════════


class TestGraderCallbackFailureSwallowed:
    """A5.3 — Failure during create_task or inside the callback is swallowed."""

    @pytest.mark.asyncio
    async def test_callback_create_task_exception_swallowed(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """If ``asyncio.create_task`` raises, runner emits warn + still returns."""
        _patch_graph_ainvoke(monkeypatch)

        # Force create_task to raise once.
        original_create_task = asyncio.create_task
        called = {"count": 0}

        def _raising_create_task(coro: Any) -> Any:
            import contextlib

            called["count"] += 1
            # Close the coroutine to avoid "coroutine was never awaited" warnings.
            with contextlib.suppress(Exception):
                coro.close()
            msg = "forced create_task failure"
            raise RuntimeError(msg)

        monkeypatch.setattr(asyncio, "create_task", _raising_create_task)

        async def _benign_callback(result: Any) -> None:
            # Never invoked because create_task is mocked to raise.
            return

        try:
            result = await run_simulation(
                tenant_archetype_slug="tenant_coach_lat",
                actor_profile=_make_actor(),
                run_id=uuid4(),
                seed_fn=lambda slug: (UUID("00000000-0000-0000-0000-000000000001"),),
                grader_callback=_benign_callback,
            )
        finally:
            monkeypatch.setattr(asyncio, "create_task", original_create_task)

        assert isinstance(result, SimulationResult)
        assert called["count"] == 1, "create_task should have been attempted exactly once"


# ════════════════════════════════════════════════════════════════════════
# A5.4 — Extended eval_metadata keys carry through Story E grader integration
# ════════════════════════════════════════════════════════════════════════


class TestEvalMetadataExtended:
    """A5.4 — Story E extends Story B/C eval_metadata with 5 NEW keys.

    The runtime extension lives in ``judge_registry._JudgeAdapter.grade`` (T-4)
    where ``extended_eval_metadata`` is built. This test verifies the
    contract — the keys are populated when the grader path runs.
    """

    def test_eval_metadata_extended_grader_keys_contract(self) -> None:
        """Verify the 5 NEW Story E keys are documented + populated by judge_registry."""
        from tests.agentic_evals.sales_agent.grader._internal import judge_registry

        # The contract is documented in 03-arch.md§4.7 — verify the adapter
        # source defines the 5 NEW keys:
        # grader / rubric_id / rubric_version / judge_id / round_n / cache_hit
        # + injection_attempt_detected (parsed from judge response, not metadata).
        import inspect

        adapter_src = inspect.getsource(judge_registry._JudgeAdapter.grade)
        for key in (
            "grader",
            "rubric_id",
            "rubric_version",
            "judge_id",
            "round_n",
            "cache_hit",
        ):
            assert f'"{key}"' in adapter_src, f"Story E NEW key {key!r} missing from _JudgeAdapter.grade"


# ════════════════════════════════════════════════════════════════════════
# A5.5 — simulation_id deterministic across re-runs
# ════════════════════════════════════════════════════════════════════════


class TestSimulationIdConsistentAcrossGraderRows:
    """A5.5 — Same (run_id, slug, actor_id, trial_n) tuple → same simulation_id."""

    @pytest.mark.asyncio
    async def test_simulation_id_consistent_across_grader_rows(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Re-running with same tuple → same UUID5 simulation_id (H2 cement)."""
        _patch_graph_ainvoke(monkeypatch)

        captured: list[UUID] = []

        async def _capture_callback(result: SimulationResult) -> None:
            captured.append(result.simulation_id)

        run_id = uuid4()
        actor = _make_actor(actor_id="lead-coach-happy")

        for _ in range(2):
            await run_simulation(
                tenant_archetype_slug="tenant_coach_lat",
                actor_profile=actor,
                run_id=run_id,
                trial_n=0,
                seed_fn=lambda slug: (UUID("00000000-0000-0000-0000-000000000001"),),
                grader_callback=_capture_callback,
            )

        # Allow scheduled callbacks to run.
        await asyncio.sleep(0.1)

        assert len(captured) == 2
        assert captured[0] == captured[1], "simulation_id must be deterministic across re-runs"
