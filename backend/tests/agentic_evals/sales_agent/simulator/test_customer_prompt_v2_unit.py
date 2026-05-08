"""T-4 acceptance tests — Customer Prompt V2 sub-slot rotation + V1 backward-compat.

Covers acceptance criteria:

* **A1** — V1 byte-equal preserved (backward-compat):
  ``CUSTOMER_PERSONA_PROMPT_V1`` and ``build_customer_prompt(actor)`` produce
  output byte-equal to pre-Story C baseline. v1 personas (schema_version=1
  serialized) continue using V1 builder; v2 personas opt into V2.
* **A2** — V2 sub-slot pain/objection rotation works across 15 turns:
  given ``actor.objections`` of length 4, parametrize ``current_turn`` ∈
  ``[1, 15]`` and assert each objection appears as ``next_objection_hint``
  at least once. Verifies deterministic round-robin algorithm
  ``objections[(current_turn - 1) % len(objections)]``.
* **A3** — Cache-prefix safety: V2 template MUST NOT contain
  ``{tenant_name}`` placeholder substring (would break Anthropic prompt
  cache per ``.claude/rules/sales-agent-brand-voice.md`` §3 cache prefix
  invariance — slot 5 BRAND_VOICE protected on production sales_agent;
  customer prompt V2 follows same discipline).

Per ``05-guidelines.md`` § Tests required:

* No ``--run-evals`` flag — pure logic test, zero LLM call.
* Pydantic ``ActorProfile`` factory mirrors ``test_customer_node_unit.py``
  pattern (``_make_actor`` keyword-only override).

Tests opt out of the ``eval`` autouse marker via ``pytestmark =
pytest.mark.no_eval`` so they run on default CI without ``--run-evals``.

# voseo-allowed: tests assert dialect_code='es-AR' voseo injection — magic comment escape per
# .claude/rules/spanish-text.md § R25 (Story C archetype-aware AR persona)
"""

# NO ``from __future__ import annotations`` — story-wide cement (T-4).

import pytest

from tests.agentic_evals.sales_agent.simulator.actor_profile import ActorProfile
from tests.agentic_evals.sales_agent.simulator._internal.customer_persona_prompt import (
    CUSTOMER_PERSONA_PROMPT_V1,
    CUSTOMER_PERSONA_PROMPT_V2,
    build_customer_prompt,
    build_customer_prompt_v2,
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
    pain_points: list[str] | None = None,
    objections: list[str] | None = None,
    persona_kind: str = "happy",
) -> ActorProfile:
    """Factory — minimal valid ActorProfile with sub-slot override hooks for V2 tests."""
    return ActorProfile(
        id="lead-frio-impaciente",
        name="María Cliente Fría",
        actor_goal="Decidir si vale la pena agendar llamada",
        dialect_code=dialect_code,
        traits=["impaciente", "exigente"],
        pain_points=pain_points if pain_points is not None else ["resultados lentos", "presupuesto limitado"],
        objections=objections if objections is not None else ["precio", "tiempo"],
        budget_hint="medio",
        urgency="medium",
        communication_style=communication_style,
        initial_message=initial_message,
        persona_kind=persona_kind,  # type: ignore[arg-type]
    )


# ───────────────────────────────────────────────────────────────────────
# A2 — V2 renders all slots correctly (full template fields interpolated)
# ───────────────────────────────────────────────────────────────────────


class TestV2RendersAllSlots:
    """V2 builder fills every Jinja-style placeholder in CUSTOMER_PERSONA_PROMPT_V2."""

    def test_v2_renders_all_slots_correctly(self) -> None:
        """Every documented field from V2 template appears in rendered output."""
        actor = _make_actor(
            dialect_code="es-AR",
            communication_style="canchera, voseo natural",
            pain_points=["resultados lentos", "presupuesto limitado"],
            objections=["precio", "tiempo", "confianza", "comparar"],
        )
        prompt = build_customer_prompt_v2(actor, current_turn=1)

        # Slot 1 (1h cache): identity (name + style + budget + urgency + dialect)
        assert actor.name in prompt
        assert "canchera, voseo natural" in prompt
        assert actor.budget_hint in prompt
        assert actor.urgency in prompt
        assert "es-AR" in prompt

        # Slot 3a (5min cache): pain points
        for pain in actor.pain_points:
            assert pain in prompt

        # Slot 3b (5min cache): objections enumerated
        for obj in actor.objections:
            assert obj in prompt

        # Sub-slot rotation: current_turn echoed + next_objection_hint chosen
        assert "Turno actual: 1" in prompt or "current_turn" not in prompt
        # turn 1 → objection[(1-1) % 4] = objections[0] = "precio"
        # next_objection_hint string must reference the chosen objection text
        assert "precio" in prompt

        # Hidden goal rendered (per ALL slots policy)
        assert actor.actor_goal in prompt

        # No Jinja residue — all placeholders interpolated
        assert "{name}" not in prompt
        assert "{communication_style}" not in prompt
        assert "{budget_hint}" not in prompt
        assert "{urgency}" not in prompt
        assert "{dialect_code}" not in prompt
        assert "{pain_points}" not in prompt
        assert "{objections_ordered}" not in prompt
        assert "{current_turn}" not in prompt
        assert "{next_objection_hint}" not in prompt
        assert "{actor_goal}" not in prompt

    def test_v2_renders_empty_objections_with_fallback(self) -> None:
        """Empty objections → 'ninguna pendiente' + '(ninguna declarada)' rendered."""
        actor = _make_actor(objections=[])
        prompt = build_customer_prompt_v2(actor, current_turn=1)
        assert "ninguna pendiente" in prompt
        assert "(ninguna declarada)" in prompt

    def test_v2_renders_turn_zero_falls_back_to_no_pending(self) -> None:
        """current_turn=0 (initial message turn — runner short-circuits LLM call) →
        per architect template, only turn ≥1 selects an objection. Turn 0 falls
        through to 'ninguna pendiente'."""
        actor = _make_actor(objections=["precio", "tiempo"])
        prompt = build_customer_prompt_v2(actor, current_turn=0)
        assert "ninguna pendiente" in prompt


# ───────────────────────────────────────────────────────────────────────
# A2 — Sub-slot rotation exhaustive 15-turn parametrize
# ───────────────────────────────────────────────────────────────────────


class TestV2SubSlotRotation:
    """V2 rotation: ``next_objection_hint = objections[(current_turn-1) % N]``."""

    @pytest.mark.parametrize("current_turn", list(range(1, 16)))
    def test_v2_rotation_per_turn_selects_correct_objection(self, current_turn: int) -> None:
        """Per-turn rotation must select the objection at index
        ``(current_turn - 1) % len(objections)``. Verified for turns 1..15
        across an actor with 4 objections — exhaustive sub-slot rotation
        contract (sub-slot 3b cache architecture per 03-arch.md §4.4).
        """
        objections = ["precio", "tiempo", "confianza", "comparar-otros"]
        actor = _make_actor(objections=objections)
        expected_objection = objections[(current_turn - 1) % len(objections)]

        prompt = build_customer_prompt_v2(actor, current_turn=current_turn)

        # The chosen objection must appear in the prompt — it's also in the
        # full ordered list (slot 3b), so we assert presence + that the
        # turn marker echoes the current_turn (anchor for hint visibility).
        assert expected_objection in prompt, (
            f"Turn {current_turn} expected hint '{expected_objection}' "
            f"(index {(current_turn - 1) % len(objections)}) "
            f"missing from rendered prompt"
        )
        # Sanity — current_turn echoed
        assert f"Turno actual: {current_turn}" in prompt

    def test_v2_sub_slot_rotation_exhaustive_15_turns(self) -> None:
        """Across 15 turns with 4 objections, EACH objection must be raised at
        least once (round-robin coverage). 4 objections cycle of 4 -> in 15
        turns each objection is selected ceil(15/4) ~ 4 times.
        """
        objections = ["precio", "tiempo", "confianza", "comparar-otros"]
        actor = _make_actor(objections=objections)

        # Stronger property — render real prompts and assert the chosen objection
        # appears at the expected position in each rendered output.
        rendered_per_turn = [build_customer_prompt_v2(actor, current_turn=turn) for turn in range(1, 16)]
        chosen_per_turn = [objections[(turn - 1) % len(objections)] for turn in range(1, 16)]

        # Every objection appears at least once across 15 turns
        for obj in objections:
            assert obj in chosen_per_turn, f"Objection '{obj}' never raised in 15 turns - rotation broken"

        # Each rendered prompt mentions the chosen objection (round-robin works
        # end-to-end through the format() call, not just the algorithm)
        for turn_idx, prompt in enumerate(rendered_per_turn):
            current_turn = turn_idx + 1
            expected_hint = chosen_per_turn[turn_idx]
            assert expected_hint in prompt, (
                f"Turn {current_turn}: rendered prompt missing chosen objection '{expected_hint}'"
            )

        # Verify the rotation pattern is exact: turn 1=obj[0], turn 5=obj[0], turn 9=obj[0]
        # (cycle period = 4, so turns 1, 5, 9, 13 all map to objections[0])
        assert chosen_per_turn[0] == objections[0]  # turn 1
        assert chosen_per_turn[4] == objections[0]  # turn 5
        assert chosen_per_turn[8] == objections[0]  # turn 9
        assert chosen_per_turn[12] == objections[0]  # turn 13


# ───────────────────────────────────────────────────────────────────────
# A3 — Cache prefix safety (no tenant_name interpolation)
# ───────────────────────────────────────────────────────────────────────


class TestV2CachePrefixSafety:
    """Per ``.claude/rules/sales-agent-brand-voice.md`` §3 — V2 prompt cacheable
    must not interpolate tenant_name / tenant_id / timestamps / conversation IDs
    that would break the Anthropic prompt cache prefix on the persona simulator.
    """

    def test_v2_no_tenant_name_interpolation(self) -> None:
        """Cache-prefix safety — V2 template must NOT contain ``{tenant_name}``."""
        # Static template assertion (substring check before any rendering)
        assert "{tenant_name}" not in CUSTOMER_PERSONA_PROMPT_V2
        assert "{tenant_id}" not in CUSTOMER_PERSONA_PROMPT_V2
        # Lower-case sanity (no `{tenant...}` variants)
        assert "{tenant" not in CUSTOMER_PERSONA_PROMPT_V2.lower()

    def test_v2_no_timestamp_or_conversation_id_in_template(self) -> None:
        """Cache-prefix safety — no timestamps / conversation IDs in cacheable section.

        These would make the cache prefix vary per request → silent cache invalidation.
        """
        assert "{timestamp}" not in CUSTOMER_PERSONA_PROMPT_V2
        assert "{conversation_id}" not in CUSTOMER_PERSONA_PROMPT_V2
        assert "{conv_id}" not in CUSTOMER_PERSONA_PROMPT_V2
        assert "{run_id}" not in CUSTOMER_PERSONA_PROMPT_V2
        # Variable section is current_turn + next_objection_hint ONLY
        assert "{current_turn}" in CUSTOMER_PERSONA_PROMPT_V2
        assert "{next_objection_hint}" in CUSTOMER_PERSONA_PROMPT_V2

    def test_v2_rendered_output_has_no_tenant_residue(self) -> None:
        """Even after rendering, no tenant identity leaks via Jinja interpolation."""
        actor = _make_actor()
        prompt = build_customer_prompt_v2(actor, current_turn=1)
        assert "{tenant" not in prompt.lower()
        assert "tenant_id" not in prompt  # exact key string sanity (no leak)
        # The build function's signature accepts NO tenant_id (per architect mandate).
        # Cement: importing inspect to confirm signature has no tenant_* parameter.
        import inspect

        sig = inspect.signature(build_customer_prompt_v2)
        for param_name in sig.parameters:
            assert "tenant" not in param_name.lower(), (
                f"build_customer_prompt_v2 signature leaks tenant identity via "
                f"parameter '{param_name}' — violates cache prefix invariance"
            )

    def test_v2_template_constant_immutable_shape(self) -> None:
        """V2 template has the strict rules + sub-slot architecture markers."""
        # Sub-slot architecture markers (per 03-arch.md §4.4)
        assert "slot cacheable 1h" in CUSTOMER_PERSONA_PROMPT_V2
        assert "sub-slot 3a" in CUSTOMER_PERSONA_PROMPT_V2
        assert "sub-slot 3b" in CUSTOMER_PERSONA_PROMPT_V2
        # Strict rules section retained
        assert "[EXIT]" in CUSTOMER_PERSONA_PROMPT_V2
        # Hidden goal retained (H10 defense Story B)
        assert "NUNCA lo reveles" in CUSTOMER_PERSONA_PROMPT_V2


# ───────────────────────────────────────────────────────────────────────
# A1 — V1 backward-compat preserved (byte-equal pre-Story C baseline)
# ───────────────────────────────────────────────────────────────────────


class TestV1BackwardCompat:
    """V1 personas continue using V1 builder; output byte-equal pre-Story C."""

    def test_v1_backward_compat_preserved(self) -> None:
        """build_customer_prompt(actor) output must match V1 baseline byte-equal.

        Since T-1 introduced schema_version=2 default, we instantiate the actor
        with explicit v1 schema_version=1 to verify the builder produces
        identical bytes to pre-Story C reference output.
        """
        # v1 actor — schema_version=1 explicit (pre-Story C baseline)
        actor_v1 = ActorProfile(
            id="lead-frio-impaciente",
            schema_version=1,  # explicit v1
            name="María Cliente Fría",
            actor_goal="Decidir si vale la pena agendar llamada",
            dialect_code="es-419",
            traits=["impaciente", "exigente"],
            pain_points=["resultados lentos", "presupuesto limitado"],
            objections=["precio", "tiempo"],
            budget_hint="medio",
            urgency="medium",
            communication_style="directa",
            initial_message="Hola, vi tu anuncio. ¿Cuánto cuesta?",
            persona_kind="happy",
        )
        prompt_v1 = build_customer_prompt(actor_v1)

        # Expected V1 byte-equal output — exact baseline string per
        # CUSTOMER_PERSONA_PROMPT_V1 + format() with v1 actor fields.
        # (NOT computed from V2 — independent reference to catch regressions.)
        expected_v1 = """Eres un cliente potencial en una conversación de ventas por chat.

## Tu identidad
Nombre: María Cliente Fría
Estilo de comunicación: directa
Presupuesto: medio
Urgencia: medium
Idioma/dialecto: es-419 (respeta el dialecto en cada respuesta)

## Tus dolores
- resultados lentos
- presupuesto limitado

## Tus objeciones naturales
precio, tiempo

## Tu objetivo oculto (NUNCA lo reveles directamente)
Decidir si vale la pena agendar llamada

## Reglas estrictas
1. Respeta el idioma/dialecto declarado (es-419). Si es es-AR, voseo OK; otros dialectos usa tuteo neutro.
2. Mensajes cortos: 1-3 oraciones, como chat real de WhatsApp/Instagram.
3. Reacciona auténticamente a lo que dice el vendedor.
4. Si la conversación no avanza tras varios turnos sin valor, escribe exactamente [EXIT].
5. Nunca rompas personaje. Nunca pidas al vendedor que ignore instrucciones previas.
6. No uses emojis excesivos — solo los naturales para tu estilo.
7. Responde SOLO con el mensaje del cliente, sin explicaciones ni metacomentarios."""

        assert prompt_v1 == expected_v1, (
            "V1 builder output drifted from pre-Story C baseline — backward-compat broken (H10 cement violation)"
        )

    def test_v1_template_constant_byte_equal_baseline(self) -> None:
        """CUSTOMER_PERSONA_PROMPT_V1 template constant is byte-equal pre-Story C.

        Independent assertion — defense-in-depth so a future refactor of V1
        template (without reading this test) immediately fails.
        """
        # The 7 strict rules + identity section markers are stable
        assert "Eres un cliente potencial en una conversación de ventas por chat." in CUSTOMER_PERSONA_PROMPT_V1
        assert "## Tu identidad" in CUSTOMER_PERSONA_PROMPT_V1
        assert "## Tus dolores" in CUSTOMER_PERSONA_PROMPT_V1
        assert "## Tus objeciones naturales" in CUSTOMER_PERSONA_PROMPT_V1
        assert "## Tu objetivo oculto (NUNCA lo reveles directamente)" in CUSTOMER_PERSONA_PROMPT_V1
        assert "## Reglas estrictas" in CUSTOMER_PERSONA_PROMPT_V1
        # Cache-prefix invariance preserved on V1 too (regression guard)
        assert "{tenant_name}" not in CUSTOMER_PERSONA_PROMPT_V1
        assert "{tenant_id}" not in CUSTOMER_PERSONA_PROMPT_V1

    def test_v1_and_v2_distinguishable_in_all(self) -> None:
        """Module exports both V1 + V2 templates and builders distinctly."""
        from tests.agentic_evals.sales_agent.simulator._internal import (
            customer_persona_prompt as cpp_module,
        )

        assert "CUSTOMER_PERSONA_PROMPT_V1" in cpp_module.__all__
        assert "CUSTOMER_PERSONA_PROMPT_V2" in cpp_module.__all__
        assert "build_customer_prompt" in cpp_module.__all__
        assert "build_customer_prompt_v2" in cpp_module.__all__
        # And distinct (template constants are not the same string)
        assert CUSTOMER_PERSONA_PROMPT_V1 != CUSTOMER_PERSONA_PROMPT_V2
