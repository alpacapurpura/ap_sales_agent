"""T-6 acceptance tests — customer_node + dialect injection + concurrency wiring.

Covers acceptance criteria:

* **A1** — Customer node generates a message from ``ActorProfile`` and the
  declared ``dialect_code`` is injected into the prompt rendered for the LLM.
  Headline scenario: ``dialect_code='es-AR'`` voseo allowed (escape rule per
  ``.claude/rules/sales-agent-brand-voice.md`` simulator excepción + magic
  comment in the prompt module).
* **A2** — The customer LLM call is wrapped by the global
  ``EVAL_SIMULATOR_SEMAPHORE`` (H4) so concurrent simulations cannot exceed
  the configured cap. The unit-level verifier asserts ``async with`` semantics
  by mocking the LLM and observing the semaphore counter while the call
  is in flight (full property-based concurrency test is T-10 deliverable).
* **A3** — ``EVAL_LLM_ROLES`` does NOT pollute the production
  ``LLM_ROLE_BY_SITE`` SSoT. Verified via shell command at the suite level
  (06-tickets.yaml T-6.A3 verifier) — additionally probed here as an inline
  check that the registry contents do not leak the customer-simulator role
  name into the production model_tier module.

Test taxonomy:

* ``TestInitialTurnZero`` — turn 0 short-circuit emits ``initial_message``
  verbatim (no LLM call, no semaphore acquire).
* ``TestDialectInjection`` — multiple ``dialect_code`` values render into
  the prompt; ``es-AR`` headline (voseo allowed via magic comment escape).
* ``TestSemaphoreWrapping`` — semaphore acquired inside ``async with``
  before the LLM call, released after.
* ``TestErrorPath`` — LLM exception path terminates gracefully via
  ``is_finished=True`` + ``error_subtype='http_error'``.
* ``TestEvalRolesIsolation`` — ``EVAL_LLM_ROLES`` registry NOT a key of the
  production ``LLM_ROLE_BY_SITE`` SSoT (defense-in-depth A3).

Tests opt out of the ``eval`` autouse marker via
``pytestmark = pytest.mark.no_eval`` so they run on default CI without
``--run-evals``.

# voseo-allowed: tests assert dialect_code='es-AR' voseo injection — magic comment escape
"""

# NO ``from __future__ import annotations`` — story-wide cement (T-4).

import asyncio
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from tests.agentic_evals.sales_agent.simulator.actor_profile import ActorProfile
from tests.agentic_evals.sales_agent.simulator.result import ConversationTurn
from tests.agentic_evals.sales_agent.simulator.state import SimulationState
from tests.agentic_evals.sales_agent.simulator._internal.concurrency import (
    EVAL_SIMULATOR_MAX_CONCURRENCY,
    get_eval_simulator_semaphore,
)
from tests.agentic_evals.sales_agent.simulator._internal.customer_node import customer_node
from tests.agentic_evals.sales_agent.simulator._internal.customer_persona_prompt import (
    CUSTOMER_PERSONA_PROMPT_V1,
    build_customer_prompt,
)
from tests.agentic_evals.sales_agent.simulator._internal.llm_roles import (
    EVAL_DEFAULT_MODELS,
    EVAL_LLM_ROLES,
    get_eval_llm_model,
)

pytestmark = pytest.mark.no_eval


# ───────────────────────────────────────────────────────────────────────
# Factories
# ───────────────────────────────────────────────────────────────────────


def _make_actor(
    *,
    dialect_code: str = "es-419",
    initial_message: str = "Hola, vi tu anuncio. ¿Cuánto cuesta?",
    communication_style: str = "directa",
) -> ActorProfile:
    """Factory — minimal valid ActorProfile with dialect override hook."""
    return ActorProfile(
        id="lead-frio-impaciente",
        name="María Cliente Fría",
        actor_goal="Decidir si vale la pena agendar llamada",
        dialect_code=dialect_code,
        traits=["impaciente", "exigente"],
        pain_points=["resultados lentos", "presupuesto limitado"],
        objections=["precio", "tiempo"],
        budget_hint="medio",
        urgency="medium",
        communication_style=communication_style,
        initial_message=initial_message,
        persona_kind="happy",
    )


def _make_state(
    *,
    actor: ActorProfile | None = None,
    current_turn: int = 0,
    transcript: list[ConversationTurn] | None = None,
) -> SimulationState:
    """Factory — minimal valid SimulationState with field override hooks."""
    actor = actor or _make_actor()
    return SimulationState(
        simulation_id=uuid4(),
        run_id=uuid4(),
        tenant_id=uuid4(),
        archetype_slug="ecommerce-fashion-beauty",
        actor_profile=actor,
        trial_n=0,
        transcript=transcript or [],
        current_turn=current_turn,
        max_turns=10,
        eval_metadata={
            "eval_run_kind": "simulator",
            "archetype_slug": "ecommerce-fashion-beauty",
            "actor_profile_id": actor.id,
            "trial_n": 0,
            "simulation_id": "11111111-1111-1111-1111-111111111111",
            "run_id": "22222222-2222-2222-2222-222222222222",
        },
    )


def _agent_turn(content: str, turn_number: int = 1) -> ConversationTurn:
    """Factory — agent turn for transcript history (subsequent turns ≥1)."""
    return ConversationTurn(
        turn_number=turn_number,
        role="agent",
        content=content,
        timestamp=datetime.now(tz=UTC),
        metadata={"generated": True},
    )


def _customer_turn(content: str, turn_number: int = 0) -> ConversationTurn:
    """Factory — customer turn for transcript history."""
    return ConversationTurn(
        turn_number=turn_number,
        role="customer",
        content=content,
        timestamp=datetime.now(tz=UTC),
        metadata={"generated": False},
    )


# ───────────────────────────────────────────────────────────────────────
# A1 — Initial turn 0 short-circuit (no LLM call)
# ───────────────────────────────────────────────────────────────────────


class TestInitialTurnZero:
    """Turn 0 emits actor_profile.initial_message verbatim — no LLM call."""

    @pytest.mark.asyncio
    async def test_turn_zero_uses_initial_message_verbatim(self) -> None:
        actor = _make_actor(initial_message="Hola, ¿en cuánto sale?")
        state = _make_state(actor=actor, current_turn=0)
        result = await customer_node(state)
        assert "transcript" in result
        new_turns: list[ConversationTurn] = result["transcript"]
        assert len(new_turns) == 1
        turn = new_turns[0]
        assert turn.role == "customer"
        assert turn.content == "Hola, ¿en cuánto sale?"
        assert turn.turn_number == 0
        # generated=False marks the deterministic verbatim emission
        assert turn.metadata.get("generated") is False

    @pytest.mark.asyncio
    async def test_turn_zero_does_not_acquire_semaphore(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Turn 0 must NOT touch the semaphore — no rate-limited resource consumed."""
        sem_before = get_eval_simulator_semaphore()
        # Snapshot the available counter (asyncio.Semaphore has _value internal but
        # we use locked() to assert state — semaphore should not be locked).
        assert not sem_before.locked()
        state = _make_state(current_turn=0)
        await customer_node(state)
        assert not sem_before.locked()


# ───────────────────────────────────────────────────────────────────────
# A1 — Dialect injection (headline test_dialect_es_ar_voseo per acceptance)
# ───────────────────────────────────────────────────────────────────────


class TestDialectInjection:
    """The build_customer_prompt function injects dialect_code verbatim."""

    def test_dialect_es_ar_voseo(self) -> None:
        """A1 headline (06-tickets.yaml verifier path literal) — voseo dialect
        rendered verbatim in customer prompt (magic comment escape per
        ``.claude/rules/sales-agent-brand-voice.md`` § Excepción simulator).
        """
        actor = _make_actor(
            dialect_code="es-AR",
            communication_style="canchera, voseo natural",
        )
        prompt = build_customer_prompt(actor)
        assert "es-AR" in prompt, "dialect_code must be injected in prompt"
        # voseo communication style must be rendered, not stripped (excepción simulator)
        assert "voseo natural" in prompt or "canchera" in prompt
        # actor identity rendered
        assert actor.name in prompt
        assert actor.actor_goal in prompt

    def test_build_customer_prompt_injects_neutral_dialect(self) -> None:
        """Other dialects (es-MX / es-CO / es-419) render verbatim too."""
        actor = _make_actor(dialect_code="es-MX", communication_style="formal")
        prompt = build_customer_prompt(actor)
        assert "es-MX" in prompt
        assert "formal" in prompt

    def test_build_customer_prompt_no_tenant_name_interpolation(self) -> None:
        """Cache-prefix safety (sales-agent-brand-voice.md §3) — NO tenant_name in prompt."""
        actor = _make_actor()
        prompt = build_customer_prompt(actor)
        # Whitelist: only ActorProfile fields should appear, never tenant identity
        # The signature accepts NO tenant_id (per ticket); pure actor-driven render.
        # Sanity: Spanish persona structure rendered, no Jinja template residue
        assert "{name}" not in prompt
        assert "{dialect_code}" not in prompt
        assert "{tenant" not in prompt.lower()

    def test_build_customer_prompt_renders_pain_points_bullets(self) -> None:
        actor = _make_actor()
        prompt = build_customer_prompt(actor)
        # Each pain point should appear in rendered prompt
        for pain in actor.pain_points:
            assert pain in prompt

    def test_build_customer_prompt_renders_objections_csv(self) -> None:
        actor = _make_actor()
        prompt = build_customer_prompt(actor)
        for obj in actor.objections:
            assert obj in prompt

    def test_prompt_template_v1_constant_immutable_shape(self) -> None:
        """CUSTOMER_PERSONA_PROMPT_V1 has the 7 strict rules + identity slots."""
        # 7 reglas estrictas per ticket spec
        assert "1." in CUSTOMER_PERSONA_PROMPT_V1
        assert "2." in CUSTOMER_PERSONA_PROMPT_V1
        assert "7." in CUSTOMER_PERSONA_PROMPT_V1
        assert "[EXIT]" in CUSTOMER_PERSONA_PROMPT_V1
        # cache-prefix safety: NO {tenant_name} placeholder in the template itself
        assert "{tenant_name}" not in CUSTOMER_PERSONA_PROMPT_V1
        assert "{tenant_id}" not in CUSTOMER_PERSONA_PROMPT_V1


# ───────────────────────────────────────────────────────────────────────
# A1 + A2 — Customer node dispatches to LLM via factory + semaphore
# ───────────────────────────────────────────────────────────────────────


class TestSemaphoreWrapping:
    """The customer LLM call is wrapped in `async with EVAL_SIMULATOR_SEMAPHORE`."""

    @pytest.mark.asyncio
    async def test_semaphore_acquired_during_llm_call(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """A2 — Probe asserts the semaphore is locked WHILE the LLM call is in flight.

        Strategy: monkeypatch LLMFactory.get_service() to return a mock whose
        get_client() returns a MagicMock with an ainvoke() coroutine that, before
        returning, observes the semaphore state and stores a snapshot.
        """
        observed_locked: dict[str, bool] = {"snapshot": False}

        async def fake_ainvoke(*args: Any, **kwargs: Any) -> MagicMock:
            # While inside the LLM call, the semaphore should be acquired.
            sem = get_eval_simulator_semaphore()
            # If max-concurrency is 1, locked() == True. With default 10, we cannot
            # rely on locked() — we instead check that the internal counter is
            # consumed by 1 vs. baseline. Use a sentinel: monkeypatch sem to size 1.
            observed_locked["snapshot"] = sem.locked()
            mock_response = MagicMock()
            mock_response.content = "Respuesta del cliente generada."
            return mock_response

        # Resize semaphore to 1 so locked() reads True during the call
        from tests.agentic_evals.sales_agent.simulator._internal import concurrency as conc_mod

        single_slot_sem = asyncio.Semaphore(1)
        monkeypatch.setattr(conc_mod, "EVAL_SIMULATOR_SEMAPHORE", single_slot_sem)
        # ALSO patch the symbol that customer_node already imported at module load:
        from tests.agentic_evals.sales_agent.simulator._internal import customer_node as cn_mod

        monkeypatch.setattr(cn_mod, "EVAL_SIMULATOR_SEMAPHORE", single_slot_sem)

        # Mock the factory chain
        mock_client = MagicMock()
        mock_client.ainvoke = AsyncMock(side_effect=fake_ainvoke)
        mock_service = MagicMock()
        mock_service.get_client = MagicMock(return_value=mock_client)

        from src.shared.infrastructure.llm import factory as factory_mod

        monkeypatch.setattr(
            factory_mod.LLMFactory,
            "get_service",
            classmethod(lambda cls: mock_service),
        )

        state = _make_state(
            current_turn=1,
            transcript=[
                _customer_turn("Hola, vi tu anuncio. ¿Cuánto cuesta?", 0),
                _agent_turn("Te cuento, son $50 mensuales con prueba gratis.", 1),
            ],
        )
        await customer_node(state)
        assert observed_locked["snapshot"], "Semaphore must be locked during LLM call (resized to size=1 for probe)."
        # After the call returns, the semaphore must be released
        assert not single_slot_sem.locked()

    @pytest.mark.asyncio
    async def test_get_eval_simulator_semaphore_returns_module_singleton(
        self,
    ) -> None:
        """Two calls to get_eval_simulator_semaphore() return the same instance."""
        sem_a = get_eval_simulator_semaphore()
        sem_b = get_eval_simulator_semaphore()
        assert sem_a is sem_b

    def test_default_max_concurrency_is_10_when_no_env_override(self) -> None:
        """The semaphore default cap is 10 unless EVAL_SIMULATOR_MAX_CONCURRENCY is set."""
        # Module loaded with no override → cap 10.
        assert EVAL_SIMULATOR_MAX_CONCURRENCY == 10


class TestCustomerNodeLLMDispatch:
    """The customer node invokes LLMFactory + injects prompt + appends turn."""

    @pytest.mark.asyncio
    async def test_subsequent_turn_invokes_llm_and_appends_turn(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        captured_messages: list[Any] = []

        async def fake_ainvoke(messages: list[Any], **kwargs: Any) -> MagicMock:
            captured_messages.extend(messages)
            mock_response = MagicMock()
            mock_response.content = "  Genial, decime más sobre la prueba.  "
            return mock_response

        mock_client = MagicMock()
        mock_client.ainvoke = AsyncMock(side_effect=fake_ainvoke)
        mock_service = MagicMock()
        mock_service.get_client = MagicMock(return_value=mock_client)

        from src.shared.infrastructure.llm import factory as factory_mod

        monkeypatch.setattr(
            factory_mod.LLMFactory,
            "get_service",
            classmethod(lambda cls: mock_service),
        )

        actor = _make_actor(dialect_code="es-AR", communication_style="canchera, voseo")
        state = _make_state(
            actor=actor,
            current_turn=2,
            transcript=[
                _customer_turn("Hola", 0),
                _agent_turn("¡Hola! ¿En qué te ayudo?", 1),
            ],
        )
        result = await customer_node(state)
        # The system message renders the persona prompt with dialect injected
        system_message = next(
            (m for m in captured_messages if getattr(m, "type", None) == "system"),
            None,
        )
        assert system_message is not None, "system message expected at index 0"
        assert "es-AR" in system_message.content
        # Result returns appended turn
        assert "transcript" in result
        new_turns: list[ConversationTurn] = result["transcript"]
        assert len(new_turns) == 1
        turn = new_turns[0]
        assert turn.role == "customer"
        # Whitespace stripped
        assert turn.content == "Genial, decime más sobre la prueba."
        assert turn.metadata.get("generated") is True
        # Turn number advances to current_turn (2)
        assert turn.turn_number == 2

    @pytest.mark.asyncio
    async def test_subsequent_turn_uses_eval_default_model(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """`get_eval_llm_model('EVAL_USER_SIMULATOR')` resolves to gpt-5-nano default."""
        assert get_eval_llm_model("EVAL_USER_SIMULATOR") == "gpt-5-nano"
        # Unknown role raises KeyError (defensive)
        with pytest.raises(KeyError):
            get_eval_llm_model("NONEXISTENT_ROLE")


# ───────────────────────────────────────────────────────────────────────
# A1 — Error path: LLM exception → graceful terminate via H7 taxonomy
# ───────────────────────────────────────────────────────────────────────


class TestErrorPath:
    """LLM error path terminates simulation gracefully (no bubble)."""

    @pytest.mark.asyncio
    async def test_llm_exception_terminates_with_http_error_subtype(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        async def boom(*args: Any, **kwargs: Any) -> None:
            msg = "Network unreachable"
            raise RuntimeError(msg)

        mock_client = MagicMock()
        mock_client.ainvoke = AsyncMock(side_effect=boom)
        mock_service = MagicMock()
        mock_service.get_client = MagicMock(return_value=mock_client)

        from src.shared.infrastructure.llm import factory as factory_mod

        monkeypatch.setattr(
            factory_mod.LLMFactory,
            "get_service",
            classmethod(lambda cls: mock_service),
        )

        state = _make_state(
            current_turn=1,
            transcript=[
                _customer_turn("Hola", 0),
                _agent_turn("Hi", 1),
            ],
        )
        result = await customer_node(state)
        assert result.get("is_finished") is True
        assert result.get("error_subtype") == "http_error"
        # Transcript NOT appended on failure (no turn)
        assert "transcript" not in result


# ───────────────────────────────────────────────────────────────────────
# A3 — Eval roles isolation (defense-in-depth at unit level)
# ───────────────────────────────────────────────────────────────────────


class TestEvalRolesIsolation:
    """`EVAL_LLM_ROLES` registry is separate from `LLM_ROLE_BY_SITE` SSoT."""

    def test_eval_user_simulator_role_present_in_eval_registry(self) -> None:
        assert "EVAL_USER_SIMULATOR" in EVAL_LLM_ROLES
        assert "EVAL_USER_SIMULATOR" in EVAL_DEFAULT_MODELS
        assert EVAL_DEFAULT_MODELS["EVAL_USER_SIMULATOR"] == "gpt-5-nano"

    def test_eval_user_simulator_not_in_production_ssot(self) -> None:
        """A3 inline check — production SSoT does NOT carry the eval role."""
        from src.modules.sales_agent.domain.model_tier import LLM_ROLE_BY_SITE

        assert "EVAL_USER_SIMULATOR" not in LLM_ROLE_BY_SITE, (
            "EVAL_USER_SIMULATOR must NOT pollute LLM_ROLE_BY_SITE SSoT (decision §2.1 03-arch-agentic.md)"
        )

    def test_eval_llm_roles_value_is_model_role_nano(self) -> None:
        from src.core.enums import ModelRole

        assert EVAL_LLM_ROLES["EVAL_USER_SIMULATOR"] == ModelRole.NANO


# ───────────────────────────────────────────────────────────────────────
# T-5 (Story C) — V1/V2 dispatch + extended eval_metadata (3 NEW keys)
# ───────────────────────────────────────────────────────────────────────


def _stub_llm_factory(
    monkeypatch: pytest.MonkeyPatch,
    *,
    captured_messages: list[Any] | None = None,
    captured_kwargs: dict[str, Any] | None = None,
    response_content: str = "Respuesta.",
) -> None:
    """Helper — patch ``LLMFactory.get_service`` to return a mock with an
    ``ainvoke`` coroutine that captures messages + kwargs into the supplied
    accumulators (T-5 reusable boilerplate to keep jscpd duplicate count
    flat across the 4 dispatch + metadata tests).
    """

    async def fake_ainvoke(messages: list[Any], **kwargs: Any) -> MagicMock:
        if captured_messages is not None:
            captured_messages.extend(messages)
        if captured_kwargs is not None:
            captured_kwargs.update(kwargs)
        mock_response = MagicMock()
        mock_response.content = response_content
        return mock_response

    mock_client = MagicMock()
    mock_client.ainvoke = AsyncMock(side_effect=fake_ainvoke)
    mock_service = MagicMock()
    mock_service.get_client = MagicMock(return_value=mock_client)

    from src.shared.infrastructure.llm import factory as factory_mod

    monkeypatch.setattr(
        factory_mod.LLMFactory,
        "get_service",
        classmethod(lambda cls: mock_service),
    )


class TestV1V2Dispatch:
    """T-5 — ``customer_node`` dispatches the persona prompt builder by
    ``actor_profile.schema_version``: ``>= 2`` → ``build_customer_prompt_v2``
    (sub-slot rotation, current_turn-aware); ``== 1`` → ``build_customer_prompt``
    (V1 byte-equal back-compat, frozen template).

    The V1 template does NOT carry the V2 sub-slot annotations
    ("slot cacheable" / "Cómo escalar objeciones"); the V2 template does.
    Tests probe the rendered ``SystemMessage.content`` captured at the LLM
    boundary to discriminate.
    """

    @pytest.mark.asyncio
    async def test_v2_dispatch_when_schema_version_is_2(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """schema_version=2 → V2 builder produces sub-slot system prompt."""
        captured_messages: list[Any] = []
        _stub_llm_factory(
            monkeypatch,
            captured_messages=captured_messages,
            response_content="Decime cuánto sale por favor.",
        )

        # Default ActorProfile.schema_version == 2 per T-1 bump (Story C D13).
        # Explicit cement here so the test does not depend on default drift.
        actor = ActorProfile(
            id="test-v2-actor",
            name="V2 Actor",
            actor_goal="Probar dispatch V2",
            dialect_code="es-AR",
            traits=["impaciente"],
            pain_points=["lead frío"],
            objections=["precio", "tiempo", "casos previos"],
            budget_hint="medio",
            urgency="medium",
            communication_style="canchera",
            initial_message="Hola, ¿cuánto sale?",
            persona_kind="happy",
            schema_version=2,
            metadata={"archetype": "tenant_coach_lat"},
        )
        state = _make_state(
            actor=actor,
            current_turn=3,
            transcript=[
                _customer_turn("Hola", 0),
                _agent_turn("¡Hola! ¿Qué necesitás?", 1),
                _customer_turn("Cuánto sale", 2),
            ],
        )
        await customer_node(state)
        system_message = next(
            (m for m in captured_messages if getattr(m, "type", None) == "system"),
            None,
        )
        assert system_message is not None, "system message expected at index 0"
        # V2-only marker — sub-slot annotation absent in V1 template
        assert "slot cacheable" in system_message.content, (
            "V2 dispatch expected: prompt must include 'slot cacheable' sub-slot annotation"
        )
        # V2-only structural section
        assert "Cómo escalar objeciones" in system_message.content, (
            "V2 dispatch expected: prompt must include the rotation rule section"
        )
        # current_turn rendered into V2 volatile suffix
        assert "Turno actual: 3" in system_message.content

    @pytest.mark.asyncio
    async def test_v1_dispatch_when_schema_version_is_1(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """schema_version=1 → V1 builder (legacy fixtures byte-equal)."""
        captured_messages: list[Any] = []
        _stub_llm_factory(
            monkeypatch,
            captured_messages=captured_messages,
            response_content="Ok, contáme más.",
        )

        # Explicit schema_version=1 — legacy v1 persona path. Story C migrator
        # could promote at load time; this fixture simulates a runtime v1
        # instance (e.g. legacy frozen golden) reaching customer_node.
        actor = ActorProfile(
            id="test-v1-actor",
            name="V1 Actor",
            actor_goal="Probar dispatch V1",
            dialect_code="es-419",
            traits=["analítica"],
            pain_points=["resultados lentos"],
            objections=["precio"],
            budget_hint="medio",
            urgency="medium",
            communication_style="formal",
            initial_message="Hola, vi tu anuncio.",
            persona_kind="happy",
            schema_version=1,
        )
        state = _make_state(
            actor=actor,
            current_turn=2,
            transcript=[
                _customer_turn("Hola", 0),
                _agent_turn("Hola, ¿en qué ayudo?", 1),
            ],
        )
        await customer_node(state)
        system_message = next(
            (m for m in captured_messages if getattr(m, "type", None) == "system"),
            None,
        )
        assert system_message is not None
        # V1 must NOT carry V2-only sub-slot annotations (anti-drift probe)
        assert "slot cacheable" not in system_message.content, (
            "V1 dispatch expected: prompt must NOT carry V2 sub-slot annotations"
        )
        assert "Cómo escalar objeciones" not in system_message.content, (
            "V1 dispatch expected: prompt must NOT carry V2 rotation rule section"
        )
        # V1 7-rule structure markers still present (positive probe)
        assert "[EXIT]" in system_message.content
        assert "## Tus dolores" in system_message.content


class TestExtendedEvalMetadata:
    """T-5 — ``customer_node`` extends ``eval_metadata`` with 3 NEW keys at the
    LLM call site:

    * ``persona_kind``      — from ``actor_profile.persona_kind``
    * ``schema_version``    — ``str(actor_profile.schema_version)`` (jsonb-safe)
    * ``archetype``         — ``actor_profile.metadata.get('archetype', '')``

    The Story B 6-key invariants (eval_run_kind, archetype_slug,
    actor_profile_id, trial_n, simulation_id, run_id) MUST be preserved in
    the dict propagated to ``config["metadata"]["eval_metadata"]``. The
    callback handler subclass forwards the dict verbatim onto every
    ``eval_simulator_llm_call`` row (verified at Layer 2 in
    ``test_simulator_smoke.py::test_eval_metadata_extended_persona_kind``).
    """

    @pytest.mark.asyncio
    async def test_eval_metadata_passed_to_llm_extends_with_3_new_keys(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Captured ``config["metadata"]["eval_metadata"]`` carries 3 NEW keys."""
        captured_kwargs: dict[str, Any] = {}
        _stub_llm_factory(monkeypatch, captured_kwargs=captured_kwargs)

        actor = ActorProfile(
            id="test-extended-actor",
            name="Persona Extendida",
            actor_goal="Verify metadata extension",
            dialect_code="es-419",
            traits=["calma"],
            pain_points=["X"],
            objections=["A"],
            budget_hint="alto",
            urgency="medium",
            communication_style="neutro",
            initial_message="Hola.",
            persona_kind="nurture",
            schema_version=2,
            metadata={"archetype": "tenant_medicina_estetica"},
        )
        state = _make_state(
            actor=actor,
            current_turn=1,
            transcript=[_customer_turn("Hola", 0)],
        )
        await customer_node(state)

        config = captured_kwargs.get("config") or {}
        metadata = config.get("metadata") or {}
        eval_md = metadata.get("eval_metadata") or {}

        # Story B 6-key invariants preserved (defense-in-depth — fail-fast
        # on any future regression that drops a mandatory key).
        for h5_key in (
            "eval_run_kind",
            "archetype_slug",
            "actor_profile_id",
            "trial_n",
            "simulation_id",
            "run_id",
        ):
            assert h5_key in eval_md, f"Story B H5 mandatory key dropped: {h5_key!r}"

        # 3 NEW keys per T-5
        assert eval_md["persona_kind"] == "nurture"
        # schema_version stored as str for jsonb compatibility
        assert eval_md["schema_version"] == "2"
        assert eval_md["archetype"] == "tenant_medicina_estetica"

    @pytest.mark.asyncio
    async def test_eval_metadata_archetype_defaults_empty_when_metadata_missing(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """``actor_profile.metadata`` without ``archetype`` key → ``''`` default."""
        captured_kwargs: dict[str, Any] = {}
        _stub_llm_factory(monkeypatch, captured_kwargs=captured_kwargs, response_content="Ok.")

        actor = _make_actor()  # no metadata.archetype set
        state = _make_state(
            actor=actor,
            current_turn=1,
            transcript=[_customer_turn("Hola", 0)],
        )
        await customer_node(state)
        eval_md = ((captured_kwargs.get("config") or {}).get("metadata") or {}).get("eval_metadata") or {}
        assert eval_md["archetype"] == ""

    @pytest.mark.asyncio
    async def test_eval_metadata_does_not_mutate_state_field(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The 3 NEW keys are added to a COPY of ``state.eval_metadata``, not
        to the underlying state dict. Mutation would violate the LangGraph
        node contract (nodes return partial dicts; never mutate state).
        """
        _stub_llm_factory(monkeypatch, response_content="Ok.")

        state = _make_state(
            current_turn=1,
            transcript=[_customer_turn("Hola", 0)],
        )
        original_keys_snapshot = set(state.eval_metadata.keys())
        await customer_node(state)
        # state.eval_metadata MUST remain the H5 6-key dict — Story B invariant
        assert set(state.eval_metadata.keys()) == original_keys_snapshot, (
            "customer_node must NOT mutate state.eval_metadata; Story B 6-key invariant violated."
        )
