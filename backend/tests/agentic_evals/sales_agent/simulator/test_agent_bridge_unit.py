"""T-7 acceptance tests — agent_bridge in-process invocation + H7 taxonomy.

Covers acceptance criteria:

* **A1** — Agent bridge invokes ``agent_app.ainvoke`` in-process (NO HTTP webhook).
  Verified by mocking ``agent_app`` at the module level and asserting
  ``ainvoke`` was called with the expected initial_state shape; additionally
  asserting that ``httpx.AsyncClient`` was NEVER instantiated during the
  bridge call (paridad with legacy ``client_simulator/agent_bridge.py``
  which DID use httpx — D1 spec ratifies in-process replacement).
* **A2** — Failure modes mapped to :class:`AgentErrorSubtype` taxonomy
  (TIMEOUT / EMPTY_RESPONSE / HTTP_ERROR / INVALID_STATE) + structured
  ``structlog.warning`` event emitted per failure path.

Out of scope (T-8 deliverables):

* Graph compose (``_internal/graph.py``)
* run_simulation orchestrator (``_internal/runner.py``)
* End-to-end smoke against real agent runtime (T-10)

Tests opt out of the ``eval`` autouse marker via ``pytestmark =
pytest.mark.no_eval`` so they run on default CI without ``--run-evals``.

# voseo-allowed: docstring quotes spec-form acceptance criteria + structlog event names
"""

# NO ``from __future__ import annotations`` — story-wide cement (T-4).

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from tests.agentic_evals.sales_agent.simulator.actor_profile import ActorProfile
from tests.agentic_evals.sales_agent.simulator.result import ConversationTurn
from tests.agentic_evals.sales_agent.simulator.state import SimulationState
from tests.agentic_evals.sales_agent.simulator.termination import (
    AgentErrorSubtype,
    TerminationReason,
)

pytestmark = pytest.mark.no_eval


# ───────────────────────────────────────────────────────────────────────
# Factories — minimal valid ActorProfile + SimulationState
# ───────────────────────────────────────────────────────────────────────


def _make_actor() -> ActorProfile:
    """Factory — minimal valid ActorProfile for agent_bridge tests."""
    return ActorProfile(
        id="lead-frio-impaciente",
        name="María Cliente Fría",
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
    """Factory — customer-side ConversationTurn for transcript history."""
    return ConversationTurn(
        turn_number=turn_number,
        role="customer",
        content=content,
        timestamp=datetime.now(tz=UTC),
        metadata={"generated": False},
    )


def _agent_turn(content: str, turn_number: int = 1) -> ConversationTurn:
    """Factory — agent-side ConversationTurn for transcript history."""
    return ConversationTurn(
        turn_number=turn_number,
        role="agent",
        content=content,
        timestamp=datetime.now(tz=UTC),
        metadata={"generated": True},
    )


def _make_state(
    *,
    transcript: list[ConversationTurn] | None = None,
    current_turn: int = 1,
    actor: ActorProfile | None = None,
) -> SimulationState:
    """Factory — minimal valid SimulationState with field override hooks."""
    actor = actor or _make_actor()
    sim_id = uuid4()
    run_id = uuid4()
    return SimulationState(
        simulation_id=sim_id,
        run_id=run_id,
        tenant_id=uuid4(),
        archetype_slug="ecommerce-fashion-beauty",
        actor_profile=actor,
        trial_n=0,
        transcript=transcript or [_customer_turn("Hola, vi tu anuncio.", 0)],
        current_turn=current_turn,
        max_turns=10,
        eval_metadata={
            "eval_run_kind": "simulator",
            "archetype_slug": "ecommerce-fashion-beauty",
            "actor_profile_id": actor.id,
            "trial_n": 0,
            "simulation_id": str(sim_id),
            "run_id": str(run_id),
        },
    )


# ───────────────────────────────────────────────────────────────────────
# Agent runtime mocks — patches the lazy imports inside agent_bridge
# ───────────────────────────────────────────────────────────────────────


def _mock_agent_app(response_text: str) -> MagicMock:
    """Build a mock ``agent_app`` whose ``ainvoke`` returns the given response.

    The agent_app contract (production graph.py) returns a dict with
    ``messages`` containing AIMessage-like dicts; the bridge extracts the
    last message's content. We use a plain dict shape here — paridad
    with how outbound_orchestrator + chat orchestrator consume the result.
    """
    result_dict = {
        "messages": [
            {"role": "user", "content": "echo input"},
            {"role": "assistant", "content": response_text},
        ],
    }
    mock_app = MagicMock()
    mock_app.ainvoke = AsyncMock(return_value=result_dict)
    return mock_app


def _patch_bridge_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    *,
    agent_app_mock: MagicMock | None = None,
    obs_ctx: object | None = None,
    db_session: object | None = None,
    knowledge_builder_mock: MagicMock | None = None,
) -> dict[str, Any]:
    """Patch the lazy-imported dependencies inside agent_bridge.

    ``agent_bridge`` lazy-imports ``agent_app``, ``create_initial_state``,
    ``TenantKnowledgeBuilder``, and ``build_eval_simulator_observability_context``
    inside the function body. We patch the canonical module symbols those
    imports resolve to, so the bridge's lazy load picks the mocks up.

    Returns a handle dict with the patched objects so tests can assert on
    them after invocation.
    """
    from luana_core_sales_agent.application.orchestrator import (
        graph as graph_mod,
    )
    from luana_core_sales_agent.application.services import (
        knowledge_builder as kb_mod,
    )
    from tests.agentic_evals.sales_agent.simulator._internal import (
        agent_bridge as bridge_mod,
    )
    from tests.agentic_evals.sales_agent.simulator._internal import (
        observability as obs_mod,
    )

    handle: dict[str, Any] = {}

    # 1. Patch agent_app — production graph entrypoint.
    app_mock = agent_app_mock or _mock_agent_app("Respuesta del agente.")
    monkeypatch.setattr(graph_mod, "agent_app", app_mock)
    handle["agent_app"] = app_mock

    # 2. Patch TenantKnowledgeBuilder constructor — return a mock with build_*.
    kb_instance = knowledge_builder_mock or MagicMock()
    kb_instance.build_identity = MagicMock(return_value="mock_identity_slot4")
    kb_instance.build_brand_voice = MagicMock(return_value="mock_brand_voice_slot5")
    monkeypatch.setattr(
        kb_mod,
        "TenantKnowledgeBuilder",
        MagicMock(return_value=kb_instance),
    )
    handle["knowledge_builder"] = kb_instance

    # 3. Patch the eval-simulator observability factory — return obs_ctx or None.
    monkeypatch.setattr(
        obs_mod,
        "build_eval_simulator_observability_context",
        MagicMock(return_value=obs_ctx),
    )
    handle["build_obs_ctx"] = obs_mod.build_eval_simulator_observability_context

    # 4. Patch ``_resolve_session_for_simulation`` — return the supplied stub session.
    sess = db_session if db_session is not None else MagicMock()
    monkeypatch.setattr(bridge_mod, "_resolve_session_for_simulation", lambda _state: sess)
    handle["db_session"] = sess

    return handle


# ───────────────────────────────────────────────────────────────────────
# A1 — In-process invocation (NO HTTP)
# ───────────────────────────────────────────────────────────────────────


class TestInProcessInvocation:
    """A1 — agent_bridge invokes ``agent_app.ainvoke`` in-process, never via HTTP."""

    @pytest.mark.asyncio
    async def test_in_process_invocation(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A1 headline (06-tickets.yaml T-7 verifier path literal).

        Asserts:

        1. ``agent_app.ainvoke`` was awaited at least once.
        2. NO ``httpx.AsyncClient`` was instantiated during the bridge call
           (legacy ``client_simulator/agent_bridge.py`` used httpx — D1 spec
           replaces with in-process; the simulator must NOT regress).
        """
        handle = _patch_bridge_dependencies(monkeypatch)

        # Spy httpx.AsyncClient — fail loudly if instantiated.
        import httpx

        instantiations = 0
        original_init = httpx.AsyncClient.__init__

        def spy_init(self: httpx.AsyncClient, *args: Any, **kwargs: Any) -> None:
            nonlocal instantiations
            instantiations += 1
            original_init(self, *args, **kwargs)

        monkeypatch.setattr(httpx.AsyncClient, "__init__", spy_init)

        from tests.agentic_evals.sales_agent.simulator._internal.agent_bridge import (
            agent_bridge,
        )

        state = _make_state(
            transcript=[_customer_turn("Hola, ¿en cuánto sale?", 0)],
            current_turn=1,
        )
        result = await agent_bridge(state)

        # The lazy-imported agent_app.ainvoke was called exactly once
        assert handle["agent_app"].ainvoke.await_count == 1, (
            "agent_bridge MUST invoke agent_app.ainvoke exactly once per turn (in-process — D1 spec)"
        )

        # NO httpx.AsyncClient instantiated — proves zero HTTP webhook usage
        assert instantiations == 0, (
            "agent_bridge MUST NOT instantiate httpx.AsyncClient — D1 spec "
            "replaces the legacy webhook path with in-process invocation. "
            f"Got {instantiations} httpx.AsyncClient instantiations."
        )

        # Result shape — transcript-append partial state
        assert "transcript" in result
        new_turns: list[ConversationTurn] = result["transcript"]
        assert len(new_turns) == 1
        agent_turn = new_turns[0]
        assert agent_turn.role == "agent"
        assert agent_turn.content == "Respuesta del agente."

    @pytest.mark.asyncio
    async def test_eval_metadata_injected_into_observability_factory(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The factory call carries the 6 H5-mandatory keys from state.eval_metadata."""
        handle = _patch_bridge_dependencies(monkeypatch)

        from tests.agentic_evals.sales_agent.simulator._internal.agent_bridge import (
            agent_bridge,
        )

        state = _make_state(current_turn=1)
        await agent_bridge(state)

        factory_mock = handle["build_obs_ctx"]
        assert factory_mock.called
        kwargs = factory_mock.call_args.kwargs

        # Each H5 key MUST be supplied to the factory by name
        assert kwargs.get("tenant_id") == state.tenant_id
        assert kwargs.get("simulation_id") == state.simulation_id
        assert kwargs.get("run_id") == state.run_id
        assert kwargs.get("archetype_slug") == state.archetype_slug
        assert kwargs.get("actor_profile_id") == state.actor_profile.id
        assert kwargs.get("trial_n") == state.trial_n

    @pytest.mark.asyncio
    async def test_observability_context_wired_when_present(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When the obs context factory returns a non-None ctx, agent_app.ainvoke
        is called inside ``async with ctx.observe_turn(...)`` and uses
        ``ctx.langchain_config()``."""
        # Build a fake obs_ctx with the right async-context-manager protocol
        observe_turn_call: dict[str, Any] = {"called": False, "kwargs": {}}

        from typing import Self

        class FakeObserveTurnCM:
            async def __aenter__(self) -> Self:
                observe_turn_call["called"] = True
                return self

            async def __aexit__(self, *args: object) -> None:
                return None

        fake_obs = MagicMock()
        fake_obs.observe_turn = MagicMock(
            side_effect=lambda **kwargs: (
                observe_turn_call.update({"kwargs": kwargs}),
                FakeObserveTurnCM(),
            )[-1],
        )
        fake_obs.langchain_config = MagicMock(
            return_value={"callbacks": [MagicMock()]},
        )

        handle = _patch_bridge_dependencies(monkeypatch, obs_ctx=fake_obs)

        from tests.agentic_evals.sales_agent.simulator._internal.agent_bridge import (
            agent_bridge,
        )

        state = _make_state(current_turn=1)
        await agent_bridge(state)

        # The observe_turn context manager was entered
        assert observe_turn_call["called"], (
            "When obs_ctx is non-None, agent_app.ainvoke MUST run inside async with obs_ctx.observe_turn(...)"
        )

        # langchain_config() supplies the callback list to ainvoke
        ainvoke_kwargs = handle["agent_app"].ainvoke.await_args.kwargs
        assert "config" in ainvoke_kwargs
        # The bridge passes the obs context's langchain_config() return value
        # straight through to ainvoke. Pattern matches outbound_orchestrator.py
        # and fixtures/entrypoint.py.
        assert ainvoke_kwargs["config"] == fake_obs.langchain_config.return_value

    @pytest.mark.asyncio
    async def test_invokes_without_observability_when_factory_returns_none(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Best-effort fallback — if the obs factory returns None, the bridge still
        invokes ``agent_app.ainvoke`` (with empty config) so the simulation
        can continue without observability rows."""
        handle = _patch_bridge_dependencies(monkeypatch, obs_ctx=None)

        from tests.agentic_evals.sales_agent.simulator._internal.agent_bridge import (
            agent_bridge,
        )

        state = _make_state(current_turn=1)
        result = await agent_bridge(state)

        # ainvoke called even without obs context
        assert handle["agent_app"].ainvoke.await_count == 1
        # Bridge produced a valid agent turn (no termination)
        assert "transcript" in result
        assert "is_finished" not in result


# ───────────────────────────────────────────────────────────────────────
# A2 — Failure mode taxonomy + structured structlog
# ───────────────────────────────────────────────────────────────────────


class TestFailureModesTaxonomy:
    """A2 — every failure path maps to AgentErrorSubtype + emits canonical structlog event."""

    @pytest.fixture
    def captured_warnings(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> list[tuple[str, dict[str, Any]]]:
        """Capture structlog warnings emitted by the agent_bridge module."""
        from tests.agentic_evals.sales_agent.simulator._internal import (
            agent_bridge as bridge_mod,
        )

        captured: list[tuple[str, dict[str, Any]]] = []

        def fake_warning(event_name: str, **kwargs: object) -> None:
            captured.append((event_name, dict(kwargs)))

        monkeypatch.setattr(bridge_mod.logger, "warning", fake_warning)
        return captured

    @pytest.mark.asyncio
    async def test_failure_modes_taxonomy(
        self,
        monkeypatch: pytest.MonkeyPatch,
        captured_warnings: list[tuple[str, dict[str, Any]]],
    ) -> None:
        """A2 headline (06-tickets.yaml T-7 verifier path literal).

        Parametrize-style assertion across the 4 failure modes:

        +----------------------+---------------------------------+----------------------------------+
        | Trigger              | Expected error_subtype          | Expected structlog event_name    |
        +======================+=================================+==================================+
        | asyncio.TimeoutError | AgentErrorSubtype.TIMEOUT       | simulator.agent_timeout          |
        | empty response       | AgentErrorSubtype.EMPTY_RESPONSE| simulator.agent_empty_response   |
        | httpx.HTTPStatusError| AgentErrorSubtype.HTTP_ERROR    | simulator.agent_http_error       |
        | last_customer_turn   | AgentErrorSubtype.INVALID_STATE | simulator.agent_invalid_state    |
        | missing              |                                 |                                  |
        +----------------------+---------------------------------+----------------------------------+
        """
        # Run all 4 sub-cases inside a single test to satisfy the spec's
        # ``test_failure_modes_taxonomy`` literal verifier path. Each sub-case
        # patches a distinct failure trigger and asserts on the result + warnings.
        from tests.agentic_evals.sales_agent.simulator._internal.agent_bridge import (
            agent_bridge,
        )

        # ── Sub-case 1: TimeoutError ─────────────────────────────────────
        captured_warnings.clear()
        timeout_app = MagicMock()
        # Note: asyncio.TimeoutError is an alias for the builtin TimeoutError
        # (Python 3.11+). We use the builtin form per ruff UP041.
        timeout_app.ainvoke = AsyncMock(side_effect=TimeoutError("simulated"))
        _patch_bridge_dependencies(monkeypatch, agent_app_mock=timeout_app)

        result = await agent_bridge(_make_state(current_turn=1))
        assert result["is_finished"] is True
        assert result["termination_reason"] == TerminationReason.AGENT_ERROR
        assert result["error_subtype"] == AgentErrorSubtype.TIMEOUT
        timeout_events = [ev for ev, _ in captured_warnings if ev == "simulator.agent_timeout"]
        assert len(timeout_events) == 1, (
            f"Expected exactly one 'simulator.agent_timeout' event, got events: {[ev for ev, _ in captured_warnings]}"
        )

        # ── Sub-case 2: empty response ───────────────────────────────────
        captured_warnings.clear()
        empty_app = _mock_agent_app("")  # blank content
        _patch_bridge_dependencies(monkeypatch, agent_app_mock=empty_app)

        result = await agent_bridge(_make_state(current_turn=1))
        assert result["is_finished"] is True
        assert result["termination_reason"] == TerminationReason.AGENT_ERROR
        assert result["error_subtype"] == AgentErrorSubtype.EMPTY_RESPONSE
        empty_events = [ev for ev, _ in captured_warnings if ev == "simulator.agent_empty_response"]
        assert len(empty_events) == 1

        # ── Sub-case 3: httpx.HTTPStatusError (wrapped) ──────────────────
        captured_warnings.clear()
        import httpx

        def make_http_error() -> httpx.HTTPStatusError:
            req = httpx.Request("POST", "http://example.com")
            resp = httpx.Response(status_code=503, request=req)
            return httpx.HTTPStatusError(
                "5xx upstream",
                request=req,
                response=resp,
            )

        http_app = MagicMock()
        http_app.ainvoke = AsyncMock(side_effect=make_http_error())
        _patch_bridge_dependencies(monkeypatch, agent_app_mock=http_app)

        result = await agent_bridge(_make_state(current_turn=1))
        assert result["is_finished"] is True
        assert result["termination_reason"] == TerminationReason.AGENT_ERROR
        assert result["error_subtype"] == AgentErrorSubtype.HTTP_ERROR
        http_events = [ev for ev, _ in captured_warnings if ev == "simulator.agent_http_error"]
        assert len(http_events) == 1

        # ── Sub-case 4: invalid state (no customer turn) ─────────────────
        captured_warnings.clear()
        # Build a state with NO customer turns in transcript
        actor = _make_actor()
        sim_id = uuid4()
        run_id = uuid4()
        invalid_state = SimulationState(
            simulation_id=sim_id,
            run_id=run_id,
            tenant_id=uuid4(),
            archetype_slug="ecommerce-fashion-beauty",
            actor_profile=actor,
            trial_n=0,
            transcript=[],  # empty — no customer turn to extract
            current_turn=1,
            max_turns=10,
            eval_metadata={
                "eval_run_kind": "simulator",
                "archetype_slug": "ecommerce-fashion-beauty",
                "actor_profile_id": actor.id,
                "trial_n": 0,
                "simulation_id": str(sim_id),
                "run_id": str(run_id),
            },
        )
        # No need to patch the agent_app here — early-return before invocation.
        # But still patch the helper that resolves the session, so the function
        # can be safely imported.
        _patch_bridge_dependencies(monkeypatch)

        result = await agent_bridge(invalid_state)
        assert result["is_finished"] is True
        assert result["termination_reason"] == TerminationReason.AGENT_ERROR
        assert result["error_subtype"] == AgentErrorSubtype.INVALID_STATE
        invalid_events = [ev for ev, _ in captured_warnings if ev == "simulator.agent_invalid_state"]
        assert len(invalid_events) == 1

    @pytest.mark.asyncio
    async def test_no_last_customer_turn_raises_invalid_state(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A2 — Empty transcript triggers INVALID_STATE BEFORE any LLM dispatch.

        The bridge should NOT invoke agent_app.ainvoke when there is nothing
        to send (no customer turn) — it terminates the simulation cleanly.
        """
        handle = _patch_bridge_dependencies(monkeypatch)

        from tests.agentic_evals.sales_agent.simulator._internal.agent_bridge import (
            agent_bridge,
        )

        actor = _make_actor()
        sim_id = uuid4()
        run_id = uuid4()
        state = SimulationState(
            simulation_id=sim_id,
            run_id=run_id,
            tenant_id=uuid4(),
            archetype_slug="ecommerce-fashion-beauty",
            actor_profile=actor,
            trial_n=0,
            transcript=[
                # Only an agent turn — no customer turn to extract
                _agent_turn("Bienvenido al programa", 0),
            ],
            current_turn=1,
            max_turns=10,
            eval_metadata={
                "eval_run_kind": "simulator",
                "archetype_slug": "ecommerce-fashion-beauty",
                "actor_profile_id": actor.id,
                "trial_n": 0,
                "simulation_id": str(sim_id),
                "run_id": str(run_id),
            },
        )

        result = await agent_bridge(state)

        # Failure mode INVALID_STATE
        assert result["is_finished"] is True
        assert result["termination_reason"] == TerminationReason.AGENT_ERROR
        assert result["error_subtype"] == AgentErrorSubtype.INVALID_STATE

        # NO ainvoke called — early return
        assert handle["agent_app"].ainvoke.await_count == 0


# ───────────────────────────────────────────────────────────────────────
# Defense in depth — assert_no_leak applied to agent response
# ───────────────────────────────────────────────────────────────────────


class TestLeakDefenseInDepth:
    """The bridge applies ``assert_no_leak`` post-extract — warning only, no raise.

    The leak gate inside the bridge logs a structured warning if the agent
    response leaked a forbidden token. The bridge does NOT raise — that
    decision is left to T-10 adversarial smoke tests which call
    ``assert_no_leak`` directly post-run with raise enabled.
    """

    @pytest.mark.asyncio
    async def test_leak_in_agent_response_logs_warning_no_raise(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When the agent response contains a forbidden token, the bridge logs
        ``simulator.system_prompt_leak_detected`` but does NOT raise — the turn
        completes successfully and the smoke test can decide whether to fail.

        Implementation detail: the warning is emitted by ``assert_no_leak``
        (which lives in ``leak_assertions.py``), so we patch that module's
        logger — not ``agent_bridge.logger``. The bridge swallows the
        ``AssertionError`` after the warning is emitted (intentional swallow
        per H10 design).
        """
        # Agent response leaks "compiler v2" — mark as forbidden token presence
        leaky_app = _mock_agent_app("Te cuento, mi compiler v2 dice que...")
        _patch_bridge_dependencies(monkeypatch, agent_app_mock=leaky_app)

        from tests.agentic_evals.sales_agent.simulator._internal import (
            agent_bridge as bridge_mod,
        )
        from tests.agentic_evals.sales_agent.simulator._internal import (
            leak_assertions as leak_mod,
        )

        captured: list[tuple[str, dict[str, Any]]] = []

        def fake_warning(event_name: str, **kwargs: object) -> None:
            captured.append((event_name, dict(kwargs)))

        # The ``simulator.system_prompt_leak_detected`` event is emitted by
        # the ``leak_assertions`` module's logger (the bridge calls
        # ``assert_no_leak`` which logs + raises; the bridge swallows the
        # raise). We patch leak_assertions.logger AND bridge.logger to be
        # safe (different modules might log the same canonical event in
        # the future).
        monkeypatch.setattr(leak_mod.logger, "warning", fake_warning)
        monkeypatch.setattr(bridge_mod.logger, "warning", fake_warning)

        state = _make_state(current_turn=1)
        # Should NOT raise even though the response leaks a forbidden token
        result = await bridge_mod.agent_bridge(state)

        # Turn completed normally
        assert "transcript" in result
        assert "is_finished" not in result

        # Defense in depth — warning event emitted with leak breadcrumb
        leak_events = [ev for ev, _ in captured if ev == "simulator.system_prompt_leak_detected"]
        assert len(leak_events) == 1, (
            f"Expected exactly one 'simulator.system_prompt_leak_detected' event "
            f"when agent response leaked. Captured events: "
            f"{[ev for ev, _ in captured]}"
        )

    @pytest.mark.asyncio
    async def test_clean_agent_response_no_leak_warning(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A clean response → no leak warning emitted."""
        clean_app = _mock_agent_app("Hola, te explico el programa de coaching.")
        _patch_bridge_dependencies(monkeypatch, agent_app_mock=clean_app)

        from tests.agentic_evals.sales_agent.simulator._internal import (
            agent_bridge as bridge_mod,
        )
        from tests.agentic_evals.sales_agent.simulator._internal import (
            leak_assertions as leak_mod,
        )

        captured: list[tuple[str, dict[str, Any]]] = []

        def fake_warning(event_name: str, **kwargs: object) -> None:
            captured.append((event_name, dict(kwargs)))

        monkeypatch.setattr(leak_mod.logger, "warning", fake_warning)
        monkeypatch.setattr(bridge_mod.logger, "warning", fake_warning)

        state = _make_state(current_turn=1)
        await bridge_mod.agent_bridge(state)

        leak_events = [ev for ev, _ in captured if ev == "simulator.system_prompt_leak_detected"]
        assert len(leak_events) == 0


# ───────────────────────────────────────────────────────────────────────
# Public surface — module exports the canonical function
# ───────────────────────────────────────────────────────────────────────


def test_module_exports_agent_bridge() -> None:
    """``agent_bridge.py`` exports the canonical ``agent_bridge`` async function."""
    from tests.agentic_evals.sales_agent.simulator._internal import (
        agent_bridge as bridge_mod,
    )

    assert hasattr(bridge_mod, "agent_bridge")
    assert hasattr(bridge_mod, "__all__")
    assert "agent_bridge" in bridge_mod.__all__


def test_no_future_annotations_import() -> None:
    """``agent_bridge.py`` MUST NOT use ``from __future__ import annotations``.

    Cement: LangGraph runtime introspection requires resolved annotations
    (the same root cause as ``state.py`` / ``customer_node.py`` / etc.).
    Story-wide cement applied — see CLAUDE.md and 03-arch-agentic.md.

    The check is AST-based so docstrings that quote the canonical pattern
    (for documentation purposes) do not trip it.
    """
    import ast
    from pathlib import Path

    from tests.agentic_evals.sales_agent.simulator._internal import agent_bridge

    src = Path(agent_bridge.__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)

    # Walk top-level nodes looking for a real `from __future__ import annotations`
    # (NOT a string literal in a docstring).
    has_future_annotations = any(
        isinstance(node, ast.ImportFrom)
        and node.module == "__future__"
        and any(alias.name == "annotations" for alias in node.names)
        for node in ast.walk(tree)
    )
    assert not has_future_annotations, (
        "agent_bridge.py MUST NOT use 'from __future__ import annotations' — "
        "story-wide cement (LangGraph runtime introspection requirement)."
    )


def test_module_logger_initialized() -> None:
    """Module exposes ``logger`` for monkeypatch tests."""
    from tests.agentic_evals.sales_agent.simulator._internal import (
        agent_bridge as bridge_mod,
    )

    assert hasattr(bridge_mod, "logger")
    assert callable(bridge_mod.logger.warning)
